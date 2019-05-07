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

from cmframework.apis.cmactivator import CMGlobalActivator


class ovsconfigactivator(CMGlobalActivator):
    """ OVS config activator plugin class. """


    CLOUD_HOSTS = 'cloud.networking'
    PLAYBOOK = '/opt/openstack-ansible/playbooks/ovs_config.yaml'

    def __init__(self):
        super(ovsconfigactivator, self).__init__()

    def get_subscription_info(self):
        return self.CLOUD_HOSTS

    def activate_set(self, props):
        self._activate()

    def activate_delete(self, props):
        self._activate()

    def activate_full(self, target):
        self._activate(target=target)

    def _activate(self, target=None):
        self.run_playbook(self.PLAYBOOK, target)
