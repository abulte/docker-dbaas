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
from docker_lib import ok, ko
from flask.ext.script import Manager

from webapp import app

manager = Manager(app)

c = Client(base_url=app.config.get('BASE_URL'), version='1.3')


# def _extract_info(c_id):
#     data = c.inspect_container(c_id)
#     if not data['State']['Running']:
#         print '%s Container is not running' % ko()
#         return False
#     ip = data['NetworkSettings']['IPAddress']
#     mysql_port = data['NetworkSettings']['PortMapping']['Tcp'].get('3306', None)
#     return ip, mysql_port

@manager.command
def test_container(c_id, ttype, quiet=False):
    docker.test_container(c_id, ttype, quiet)

@manager.command
def create(ttype):
    """dbaas create DB_TYPE"""
    container = docker.create_container('mysql', quiet=False)
    print "%s Started container %s" % (ok(), container['Id'])
    print 'Waiting for MySQL to boot...'
    time.sleep(5)
    return test_container(container['Id'], 'mysql', quiet=False)

@manager.command
def test():
    print 'this is a test'

@manager.command
def list(type='all'):
    print docker.get_containers()

@manager.command
def inspect(container_id):
    print docker.inspect_container(container_id)

if __name__ == "__main__":
    manager.run()
