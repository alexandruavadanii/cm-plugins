#! /usr/bin/python
# Copyright 2019 Nokia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from cmframework.apis import cmuserconfig
from cmframework.apis import cmerror
from cmdatahandlers.api import configerror

"""
This plugin is used to handle REC specific host configs. Currently
its sole purpuse is to set default middleware reserved memory.
"""


class rechosthandler(cmuserconfig.CMUserConfigPlugin):
    default_middleware_reserved_memory = '4Gi'

    def __init__(self):
        super(rechosthandler, self).__init__()

    def handle(self, confman):
        self._set_default_memory(confman)

    def _set_default_memory(self, confman):
        hostconf = confman.get_hosts_config_handler()
        hostconf.set_default_reserved_memory_to_all_hosts(default_middleware_reserved_memory)

