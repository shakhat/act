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

from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class Operation(object):
    def __init__(self, item, dependencies):
        self.item = item
        self.dependencies = dependencies

    def do(self, world):
        LOG.info('Do nothing')


class CreateOperation(Operation):
    def do(self, world):
        LOG.info('Created item: %s', self.item)
        world.put(self.item, self.dependencies)


class DeleteOperation(Operation):
    def do(self, world):
        LOG.info('Deleted item: %s', self.dependencies[0])
        world.pop(self.dependencies[0])
