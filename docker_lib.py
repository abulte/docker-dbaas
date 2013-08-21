#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013 Alexandre Bulté <alexandre[at]bulte[dot]net>
# 
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import dateutil.parser
from docker import Client
from yapsy.PluginManager import PluginManager
from webapp import app, query_db, get_db

# import logging 
# logging.basicConfig(level=logging.DEBUG)

## PLUGINS
# Load the plugins from the plugin directory.
manager = PluginManager()
manager.setPluginPlaces(["plugins"])
manager.collectPlugins()

def getPluginNames():
    return [plugin.name for plugin in manager.getAllPlugins()]

def _getAdapter(ttype):
    adapter = manager.getPluginByName(ttype)
    if adapter is None:
        raise Exception('Unsupported database type: %s' % ttype)
    else:
        return adapter.plugin_object

## END PLUGINS

def dc():
    return Client(base_url=app.config.get('BASE_URL'), version='1.3')

def _format_container(raw):
    # app.logger.debug(raw)
    adapter = _getAdapter(raw['type'])
    port = adapter.PORT
    running = raw['State']['Running']
    c_id = raw['ID'][:12]
    if not running:
        return {'id': c_id, 'running': False}
    else:
        start = raw['State']['StartedAt']
        start = dateutil.parser.parse(start)
        up_for = datetime.datetime.now(start.tzinfo) - start
        status = 'Up %s day(s) %s hour(s)' % (up_for.days, up_for.seconds / 3600)
        return {
            'id': c_id,
            'running': True,
            'ip': raw['NetworkSettings']['IPAddress'],
            'db_port': raw['NetworkSettings']['PortMapping']['Tcp'].get('%s' % port, None),
            'created': raw['Created'],
            'status': status
        }

def _get_container_from_db(c_id):
    cdb = query_db('select * from databases where docker_id = ?', args=[c_id], one=True)
    if cdb is None:
        raise Exception('No container by id %s' % c_id)
    return cdb

def stop_container(c_id):
    dc().stop(c_id)
    return True

def start_container(c_id):
    dc().start(c_id)
    return True

def remove_container(c_id):
    with app.app_context():
        get_db().execute('delete from databases where docker_id = ?', [c_id])
        get_db().commit()
    dc().remove_container(c_id)
    return True

def inspect_container(container_id):
    raw = dc().inspect_container(container_id)
    cdb = _get_container_from_db(container_id)
    raw['type'] = cdb['type']
    return _format_container(raw)

def get_containers(details=False):
    cs = []
    with app.app_context():
        for c in query_db('select * from databases'):
            cs.append({'id': c['docker_id'], 'name': c['name'], 'type': c['type']})
    if not details:
        return cs
    else:
        detail_containers = []
        for c in cs:
            # app.logger.debug(c)
            details = inspect_container(c['id'])
            details['name'] = c['name']
            details['type'] = c['type']
            detail_containers.append(details)
    return detail_containers

def create_container(dbtype, name, mem_limit, pm):
    adapter = _getAdapter(dbtype)
    container = adapter.create_container(mem_limit=int(mem_limit)*1024*1024, pm=pm)
    with app.app_context():
        get_db().execute('insert into databases (docker_id, name, memory_limit, port_mapping, type) \
            values (?, ?, ?, ?, ?)', [container['Id'], name, mem_limit, pm, dbtype])
        get_db().commit()
    start_container(container['Id'])
    return container

def test_container(c_id):
    with app.app_context():
        cdb = _get_container_from_db(c_id)
    adapter = _getAdapter(cdb['type'])
    info = inspect_container(c_id)
    if not info:
        raise Exception('No container by id')
    elif not info['running']:
        return False
    return adapter.test_container(info)
