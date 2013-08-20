#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013 Alexandre Bulté <alexandre[at]bulte[dot]net>
# 
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import docker_lib as docker

class BaseDatabasePlugin:

    DOCKER_IMAGE_NAME = None
    DEFAULT_MEMORY_LIMIT = None
    STARTUP_CMD = None

    def test_container(self, info):
        raise NotImplementedError

    def create_container(self, mem_limit=None):
        if mem_limit is None: mem_limit = self.DEFAULT_MEMORY_LIMIT
        if len(docker.dc().images(self.DOCKER_IMAGE_NAME)) == 0:
            docker.dc().pull(self.DOCKER_IMAGE_NAME)
        return docker.dc().create_container(self.DOCKER_IMAGE_NAME, self.STARTUP_CMD, detach=True, 
            mem_limit=mem_limit)
