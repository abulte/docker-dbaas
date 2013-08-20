#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013 Alexandre Bulté <alexandre[at]bulte[dot]net>
# 
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sqlite3
import psutil
import docker_lib as docker
from flask import Flask, render_template, request, redirect, \
    url_for, flash, jsonify, g

app = Flask(__name__)

app.debug = True

app.config.update(
    SECRET_KEY = 'sLdNV5V33lFAaDKzswFVt6NG2ciz1OrJ5IfAwgyr',
    MEM_LIMIT = 256*1024*1024,
    BASE_URL = 'http://172.17.42.1:4243',
    DATABASE = 'dbaas.db'
)

## DATABASE
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_db()
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

## VIEWS

@app.route('/')
def index():
    plugins = docker.getPluginNames()
    mem_total = psutil.virtual_memory().total / 1024 / 1024
    mem_available = psutil.virtual_memory().available / 1024 / 1024
    mem_percent = psutil.virtual_memory().percent
    load = ', '.join([str(l) for l in os.getloadavg()])
    containers = docker.get_containers(details=True)
    return render_template('index.html', containers=containers, mem_total=mem_total, 
        mem_available=mem_available, mem_percent=mem_percent, load=load, plugins=plugins)

@app.route('/stop/<c_id>')
def stop(c_id):
    docker.stop_container(c_id)
    flash('Server successfully stopped.', 'success')
    return redirect(url_for('index'))

@app.route('/start/<c_id>')
def start(c_id):
    docker.start_container(c_id)
    flash('Server successfully started.', 'success')
    return redirect(url_for('index'))

@app.route('/remove/<c_id>')
def remove(c_id):
    docker.remove_container(c_id)
    get_db().execute('delete from databases where docker_id = ?', 
        [c_id])
    get_db().commit()
    flash('Server successfully removed.', 'success')
    return redirect(url_for('index'))

@app.route('/add/<dbtype>', methods=['GET', 'POST'])
def add(dbtype):
    if request.method == 'POST':
        name = request.form.get('name')
        ml = request.form.get('memory_limit')
        pm = request.form.get('port_mapping', 'off')
        if pm == 'on':
            pm = True
        else:
            pm = False
        docker.create_container(dbtype, name, ml, pm)
        flash('Server successfully started.', 'success')
        return redirect(url_for('index'))
    return render_template('add.html', dbtype=dbtype)

@app.route('/pulse/<c_id>')
def pulse(c_id):
    cdb = query_db('select * from databases where docker_id = ?', args=[c_id], one=True)
    if cdb is None:
        raise Exception('No container by id %s' % c_id)
    status = docker.test_container(c_id, cdb['type'], quiet=True)
    return jsonify({'up': status})

if __name__ == '__main__':
    app.run(host='0.0.0.0')