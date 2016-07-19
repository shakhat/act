# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import inspect
import os
import sys

from oslo_log import log as logging
from oslo_utils import importutils

import act


LOG = logging.getLogger(__name__)

REGISTRY = []


def import_modules_from_package(package):
    base = os.path.join(os.path.dirname(act.__file__), os.pardir)
    path = os.path.normpath(os.path.join(base, *package.split('.')))

    for root, dirs, files in os.walk(path):
        for filename in files:
            if filename.startswith('__') or not filename.endswith('.py'):
                continue

            relative_path = os.path.relpath(os.path.join(root, filename), base)
            name = os.path.splitext(relative_path)[0]  # remove extension
            module_name = '.'.join(name.split(os.sep))  # convert / to .

            if module_name not in sys.modules:
                module = importutils.import_module(module_name)
                sys.modules[module_name] = module
                yield module


def init():
    global REGISTRY

    modules = import_modules_from_package('act.actions')

    klazz_list = []
    for module in modules:
        class_info_list = inspect.getmembers(module, inspect.isclass)
        klazz_list += [ci[1] for ci in class_info_list]

    REGISTRY += [k() for k in klazz_list]

    LOG.info('Registry: %s', REGISTRY)


def get_actions():
    return REGISTRY
