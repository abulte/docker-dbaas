#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013 Alexandre Bulté <alexandre[at]bulte[dot]net>
# 
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from plugins.base import BaseDatabasePlugin
from yapsy.IPlugin import IPlugin

class MysqlPlugin(BaseDatabasePlugin, IPlugin):

    DOCKER_IMAGE_NAME = 'dbaas/mysql'
    DEFAULT_MEMORY_LIMIT = 256*1024*1024
    STARTUP_CMD = '/usr/sbin/mysqld'
    USER_LOGIN = 'root'
    USER_PASSWD = 'root4mysql'
    PORT = 3306

    def test_container(self, info):
        ip = info.get('ip', '127.0.0.1')
        import mysql.connector
        cnx = mysql.connector.connect(user=self.USER_LOGIN, 
                                    password=self.USER_PASSWD,
                                    host=ip, # database='users'
                                )
        cnx.close()
        return True
