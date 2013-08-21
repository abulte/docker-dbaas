#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013 Alexandre Bulté <alexandre[at]bulte[dot]net>
# 
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import time
from docker import Client
import docker_lib as docker
from flask.ext.script import Manager, prompt_bool
from termcolor import colored

from webapp import app

manager = Manager(app)

c = Client(base_url=app.config.get('BASE_URL'), version='1.3')

def ok():
    return colored('[OK]', 'green')

def ko():
    return colored('[KO]', 'red')

@manager.command
def start(container_id):
    try:
        docker.start_container(container_id)
        print '%s %s' % (ok(), 'Container %s started' % container_id)
        print 'Waiting for database to boot...'
        time.sleep(5)
        return test(container_id)
    except Exception, e:
        print '%s %s' % (ko(), e)

@manager.command
def stop(container_id):
    try:
        docker.stop_container(container_id)
        print '%s %s' % (ok(), 'Container %s stopped' % container_id)
    except Exception, e:
        print '%s %s' % (ko(), e)

@manager.command
def remove(container_id):
    try:
         if prompt_bool("Are you sure?"):
            docker.remove_container(container_id)
            print '%s %s' % (ok(), 'Container %s removed' % container_id)
    except Exception, e:
        print '%s %s' % (ko(), e)

@manager.command
def test(c_id):
    try:
        status = docker.test_container(c_id)
        if status:
            print '%s %s' % (ok(), 'Connection successful')
        else:
            print '%s %s' % (ko(), 'Connection failed')
    except Exception, e:
        print '%s %s' % (ko(), e)

@manager.command
def create(dbtype, name, nopm=False, memorylimit=256):
    """dbaas create DB_TYPE NAME"""
    try:
        pm = not nopm
        container = docker.create_container(dbtype, name, memorylimit, pm)
        print "%s Started container %s" % (ok(), container['Id'])
        print 'Waiting for database to boot...'
        time.sleep(5)
        return test(container['Id'])
    except Exception, e:
       print '%s %s' % (ko(), e)
 
@manager.command
def list(type='all'):
    cs = docker.get_containers(details=True)
    print '%s\t\t%s\t%s\t\t%s\t\t%s\t%s' % ('Id', 'Type', 'Name', 'IP', 'DB port', 'Running')
    for c in cs:
        if c['running']:
            color = 'green'
        else:
            color = 'red'
        cid = colored(c['id'], color)
        print '%s\t%s\t%s\t%s\t%s\t%s' % (cid, c['type'], c['name'], c.get('ip', ''), c.get('db_port', ''), c['running'])

@manager.command
def inspect(container_id):
    data = docker.inspect_container(container_id)
    for k, v in data.items():
        print '%s\t\t\t\t\t%s' % (k,v)

if __name__ == "__main__":
    manager.run()
