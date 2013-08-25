#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013 Alexandre Bulté <alexandre[at]bulte[dot]net>
# 
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask.ext.script import Manager, Server
from contextlib import closing
import docker_lib as docker

from webapp import app, db

manager = Manager(app)

# Turn on debugger by default and reloader
manager.add_command("runserver", Server(
    use_debugger=True,
    use_reloader=True,
    host='0.0.0.0',
    port=5000)
)

@manager.command
def init_db():
    print 'Starting...'
    with closing(db.connect()) as mydb:
        with app.open_resource('schema.sql', mode='r') as f:
            mydb.cursor().executescript(f.read())
        mydb.commit()
    print 'Done.'

if __name__ == "__main__":
    manager.run()
