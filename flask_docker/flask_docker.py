#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013 Alexandre Bulté <alexandre[at]bulte[dot]net>
# 
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sqlite3
import datetime
import dateutil.parser
from docker import Client
from yapsy.PluginManager import PluginManager
from flask import current_app

# Find the stack on which we want to store the database connection.
# Starting with Flask 0.9, the _app_ctx_stack is the correct one,
# before that we need to use the _request_ctx_stack.
try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack

import logging 
logging.basicConfig(level=logging.DEBUG)

class SQLite3(object):

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.config.setdefault('SQLITE3_DATABASE', ':memory:')
        # Use the newstyle teardown_appcontext if it's available,
        # otherwise fall back to the request context
        if hasattr(app, 'teardown_appcontext'):
            app.teardown_appcontext(self.teardown)
        else:
            app.teardown_request(self.teardown)

    def connect(self):
        return sqlite3.connect(current_app.config['SQLITE3_DATABASE'])

    def teardown(self, exception):
        ctx = stack.top
        if hasattr(ctx, 'sqlite3_db'):
            ctx.sqlite3_db.close()

    def query_db(self, query, args=(), one=False):
        cur = self.connection.execute(query, args)
        rv = cur.fetchall()
        cur.close()
        return (rv[0] if rv else None) if one else rv

    @property
    def connection(self):
        ctx = stack.top
        if ctx is not None:
            if not hasattr(ctx, 'sqlite3_db'):
                ctx.sqlite3_db = self.connect()
                ctx.sqlite3_db.row_factory = sqlite3.Row
            return ctx.sqlite3_db

class Docker(object):

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.config.setdefault('DOCKER_BASE_URL', 'http://127.0.0.1:4243')

        self.client = Client(base_url=app.config.get('DOCKER_BASE_URL'), version='1.3')
        
        self.manager = PluginManager()
        self.manager.setPluginPlaces(["plugins"])
        self.manager.collectPlugins()

        self.db = SQLite3(app)

    def test_extension(self):
        app = getattr(self, 'app', None) or current_app
        db = SQLite3(app)
        # with app.app_context():
        #     app.logger.debug(db.query_db('select * from databases'))

    def getPluginNames(self):
        return [plugin.name for plugin in self.manager.getAllPlugins()]

    def _getAdapter(self, ttype):
        adapter = self.manager.getPluginByName(ttype)
        if adapter is None:
            raise Exception('Unsupported database type: %s' % ttype)
        else:
            return adapter.plugin_object

    ## END PLUGINS

    def dc(self):
        return self.client

    def _format_container(self, raw):
        # app.logger.debug(raw)
        adapter = self._getAdapter(raw['type'])
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

    def _get_container_from_db(self, c_id):
        cdb = self.db.query_db('select * from databases where docker_id = ?', args=[c_id], one=True)
        if cdb is None:
            raise Exception('No container by id %s' % c_id)
        return cdb

    def stop_container(self, c_id):
        self.dc().stop(c_id)
        return True

    def start_container(self, c_id):
        self.dc().start(c_id)
        return True

    def remove_container(self, c_id):
        app = getattr(self, 'app', None) or current_app
        with app.app_context():
            self.db.connection.execute('delete from databases where docker_id = ?', [c_id])
            self.db.connection.commit()
        self.dc().remove_container(c_id)
        return True

    def inspect_container(self, container_id):
        raw = self.dc().inspect_container(container_id)
        cdb = self._get_container_from_db(container_id)
        raw['type'] = cdb['type']
        return self._format_container(raw)

    def get_containers(self, details=False):
        cs = []
        app = getattr(self, 'app', None) or current_app
        with app.app_context():
            for c in self.db.query_db('select * from databases'):
                cs.append({'id': c['docker_id'], 'name': c['name'], 'type': c['type']})
        if not details:
            return cs
        else:
            detail_containers = []
            for c in cs:
                # app.logger.debug(c)
                details = self.inspect_container(c['id'])
                details['name'] = c['name']
                details['type'] = c['type']
                detail_containers.append(details)
        return detail_containers

    def create_container(self, dbtype, name, mem_limit, pm):
        adapter = self._getAdapter(dbtype)
        container = adapter.create_container(mem_limit=int(mem_limit)*1024*1024, pm=pm)
        app = getattr(self, 'app', None) or current_app
        with app.app_context():
            self.db.connection.execute('insert into databases (docker_id, name, memory_limit, port_mapping, type) \
                values (?, ?, ?, ?, ?)', [container['Id'], name, mem_limit, pm, dbtype])
            self.db.connection.commit()
        self.start_container(container['Id'])
        return container

    def test_container(self, c_id):
        app = getattr(self, 'app', None) or current_app
        with app.app_context():
            cdb = self._get_container_from_db(c_id)
        adapter = self._getAdapter(cdb['type'])
        info = self.inspect_container(c_id)
        if not info:
            raise Exception('No container by id')
        elif not info['running']:
            return False
        return adapter.test_container(info)

