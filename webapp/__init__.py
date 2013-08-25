#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013 Alexandre Bulté <alexandre[at]bulte[dot]net>
# 
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
# import docker_lib as docker
from flask_docker.flask_docker import Docker, SQLite3
from flask import Flask, render_template, request, redirect, \
    url_for, flash, jsonify, g

app = Flask(__name__)

app.debug = True

app.config.update(
    SECRET_KEY = 'sLdNV5V33lFAaDKzswFVt6NG2ciz1OrJ5IfAwgyr',
    MEM_LIMIT = 256*1024*1024,
    DOCKER_BASE_URL = 'http://172.17.42.1:4243',
    SQLITE3_DATABASE = 'dbaas.db'
)

docker_ext = Docker(app)
docker_ext.test_extension()

db = SQLite3(app)

## VIEWS

@app.route('/')
def index():
    try :
        import psutil
        mem_total = psutil.virtual_memory().total / 1024 / 1024
        mem_available = psutil.virtual_memory().available / 1024 / 1024
        mem_percent = psutil.virtual_memory().percent
        load = ', '.join([str(l) for l in os.getloadavg()])
    except ImportError:
        mem_total = mem_available = mem_percent = load = 'NA'
    plugins = docker.getPluginNames()
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
    try:
        status = docker.test_container(c_id)
    except Exception, e:
        status = False
        app.logger.error('Error in pulse for %s: %s' % (c_id, e))
    return jsonify({'up': status})