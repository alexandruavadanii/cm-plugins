#!/usr/bin/python
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

import json
import re
import base64
import logging
import ipaddr
from cmframework.apis import cmvalidator
from cmdatahandlers.api import validation
from cmdatahandlers.api import configerror


class CaasValidationError(configerror.ConfigError):
    def __init__(self, description):
        configerror.ConfigError.__init__(
            self, 'Validation error in caas_validation: {}'.format(description))


class CaasValidationUtils(object):

    def __init__(self):
        pass

    @staticmethod
    def check_key_in_dict(key, dictionary):
        if key not in dictionary:
            raise CaasValidationError("{} cannot be found in {} ".format(key, dictionary))

    def get_every_key_occurrence(self, var, key):
        if hasattr(var, 'iteritems'):
            for k, v in var.iteritems():
                if k == key:
                    yield v
                if isinstance(v, dict):
                    for result in self.get_every_key_occurrence(v, key):
                        yield result
                elif isinstance(v, list):
                    for d in v:
                        for result in self.get_every_key_occurrence(d, key):
                            yield result

    @staticmethod
    def is_optional_param_present(key, dictionary):
        if key not in dictionary:
            logging.info('{} key is not in the config dictionary, since this is an optional '
                         'parameter, validation is skipped.'.format(key))
            return False
        if not dictionary[key]:
            logging.info('Although {} key is in the config dictionary the correspondig value is '
                         'empty, since this is an optional parametery, '
                         'validation is skipped.'.format(key))
            return False
        return True


class CaasValidation(cmvalidator.CMValidator):

    SUBSCRIPTION = r'^cloud\.caas|cloud\.hosts|cloud\.networking$'
    CAAS_DOMAIN = 'cloud.caas'
    NETW_DOMAIN = 'cloud.networking'
    HOSTS_DOMAIN = 'cloud.hosts'

    SERV_PROF = 'service_profiles'
    CAAS_PROFILE_PATTERN = 'caas_master|caas_worker'
    CIDR = 'cidr'

    DOCKER_SIZE_QOUTA = "docker_size_quota"
    DOCKER_SIZE_QOUTA_PATTERN = r"^\d*[G,M,K]$"

    CHART_NAME = "chart_name"
    CHART_NAME_PATTERN = r"[A-Za-z0-9\.-_]+"

    CHART_VERSION = "chart_version"
    CHART_VERSION_PATTERN = r"^\d+\.\d+\.\d+$"

    HELM_OP_TIMEOUT = "helm_operation_timeout"

    DOCKER0_CIDR = "docker0_cidr"

    INSTANTIATION_TIMEOUT = "instantiation_timeout"

    HELM_PARAMETERS = "helm_parameters"

    ENCRYPTED_CA = "encrypted_ca"
    ENCRYPTED_CA_KEY = "encrypted_ca_key"

    def __init__(self):
        cmvalidator.CMValidator.__init__(self)
        self.validation_utils = validation.ValidationUtils()
        self.conf = None
        self.caas_conf = None
        self.caas_utils = CaasValidationUtils()

    def get_subscription_info(self):
        return self.SUBSCRIPTION

    def validate_set(self, props):
        if not self.is_caas_mandatory(props):
            logging.info("{} not found in {}, caas validation is not needed.".format(
                self.CAAS_PROFILE_PATTERN, self.HOSTS_DOMAIN))
            return
        self.props_pre_check(props)
        self.validate_docker_size_quota()
        self.validate_chart_name()
        self.validate_chart_version()
        self.validate_helm_operation_timeout()
        self.validate_docker0_cidr(props)
        self.validate_instantiation_timeout()
        self.validate_helm_parameters()
        self.validate_encrypted_ca(self.ENCRYPTED_CA)
        self.validate_encrypted_ca(self.ENCRYPTED_CA_KEY)

    def is_caas_mandatory(self, props):
        hosts_conf = json.loads(props[self.HOSTS_DOMAIN])
        service_profiles = self.caas_utils.get_every_key_occurrence(hosts_conf, self.SERV_PROF)
        pattern = re.compile(self.CAAS_PROFILE_PATTERN)
        for profile in service_profiles:
            if filter(pattern.match, profile):
                return True
        return False

    def props_pre_check(self, props):
        if not isinstance(props, dict):
            raise CaasValidationError('The given input: {} is not a dictionary!'.format(props))
        if self.CAAS_DOMAIN not in props:
            raise CaasValidationError(
                '{} configuration is missing from {}!'.format(self.CAAS_DOMAIN, props))
        self.caas_conf = json.loads(props[self.CAAS_DOMAIN])
        self.conf = {self.CAAS_DOMAIN: self.caas_conf}
        if not self.caas_conf:
            raise CaasValidationError('{} is an empty dictionary!'.format(self.conf))

    def validate_docker_size_quota(self):
        if not self.caas_utils.is_optional_param_present(self.DOCKER_SIZE_QOUTA, self.caas_conf):
            return
        if not re.match(self.DOCKER_SIZE_QOUTA_PATTERN, self.caas_conf[self.DOCKER_SIZE_QOUTA]):
            raise CaasValidationError('{} is not a valid {}!'.format(
                self.caas_conf[self.DOCKER_SIZE_QOUTA],
                self.DOCKER_SIZE_QOUTA))

    def validate_chart_name(self):
        if not self.caas_utils.is_optional_param_present(self.CHART_NAME, self.caas_conf):
            return
        if not re.match(self.CHART_NAME_PATTERN, self.caas_conf[self.CHART_NAME]):
            raise CaasValidationError('{} is not a valid {} !'.format(
                self.caas_conf[self.CHART_NAME],
                self.CHART_NAME))

    def validate_chart_version(self):
        if not self.caas_utils.is_optional_param_present(self.CHART_VERSION, self.caas_conf):
            return
        if not self.caas_conf[self.CHART_NAME]:
            logging.warn('{} shall be set only, when {} is set.'.format(
                self.CHART_VERSION, self.CHART_NAME))
        if not re.match(self.CHART_VERSION_PATTERN, self.caas_conf[self.CHART_VERSION]):
            raise CaasValidationError('{} is not a valid {} !'.format(
                self.caas_conf[self.CHART_VERSION],
                self.CHART_VERSION))

    def validate_helm_operation_timeout(self):
        if not self.caas_utils.is_optional_param_present(self.HELM_OP_TIMEOUT, self.caas_conf):
            return
        if not isinstance(self.caas_conf[self.HELM_OP_TIMEOUT], int):
            raise CaasValidationError('{}:{} is not an integer'.format(
                self.HELM_OP_TIMEOUT,
                self.caas_conf[self.HELM_OP_TIMEOUT]))

    def get_docker0_cidr_netw_obj(self, subnet):
        try:
            return ipaddr.IPNetwork(subnet)
        except ValueError as exc:
            raise CaasValidationError('{} is an invalid subnet address: {}'.format(
                self.DOCKER0_CIDR, exc))

    def check_docker0_cidr_overlaps_with_netw_subnets(self, docker0_cidr, props):
        netw_conf = json.loads(props[self.NETW_DOMAIN])
        cidrs = self.caas_utils.get_every_key_occurrence(netw_conf, self.CIDR)
        for cidr in cidrs:
            if docker0_cidr.overlaps(ipaddr.IPNetwork(cidr)):
                raise CaasValidationError(
                    'CIDR configured for {} shall be an unused IP range, '
                    'but it overlaps with {} from {}.'.format(
                        self.DOCKER0_CIDR, cidr, self.NETW_DOMAIN))

    def validate_docker0_cidr(self, props):
        if not self.caas_utils.is_optional_param_present(self.DOCKER0_CIDR, self.caas_conf):
            return
        docker0_cidr_obj = self.get_docker0_cidr_netw_obj(self.caas_conf[self.DOCKER0_CIDR])
        self.check_docker0_cidr_overlaps_with_netw_subnets(docker0_cidr_obj, props)

    def validate_instantiation_timeout(self):
        if not self.caas_utils.is_optional_param_present(self.INSTANTIATION_TIMEOUT,
                                                         self.caas_conf):
            return
        if not isinstance(self.caas_conf[self.INSTANTIATION_TIMEOUT], int):
            raise CaasValidationError('{}:{} is not an integer'.format(
                self.INSTANTIATION_TIMEOUT,
                self.caas_conf[self.INSTANTIATION_TIMEOUT]))

    def validate_helm_parameters(self):
        if not self.caas_utils.is_optional_param_present(self.HELM_PARAMETERS, self.caas_conf):
            return
        if not isinstance(self.caas_conf[self.HELM_PARAMETERS], dict):
            raise CaasValidationError('The given input: {} is not a dictionary!'.format(
                self.caas_conf[self.HELM_PARAMETERS]))

    def validate_encrypted_ca(self, enc_ca):
        self.caas_utils.check_key_in_dict(enc_ca, self.caas_conf)
        enc_ca_str = self.caas_conf[enc_ca][0]
        if not enc_ca_str:
            raise CaasValidationError('{} shall not be empty !'.format(enc_ca))
        try:
            base64.b64decode(enc_ca_str)
        except TypeError as exc:
            raise CaasValidationError('Invalid {}: {}'.format(enc_ca, exc))