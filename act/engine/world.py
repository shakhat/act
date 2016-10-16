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


class World(object):
    def __init__(self):
        self.storage = {}

    def put(self, item, dependencies=None):
        self.storage[item.id] = item

        if dependencies:
            item.set_dependencies([d.id for d in dependencies])

        LOG.debug('Put item to the world: %s', item)

    def pop(self, item):
        LOG.debug('Remove item from the world: %s', item)

        for dependency_id in item.dependencies:
            self.storage[dependency_id].free()

        del self.storage[item.id]

    def filter_items(self, item_types):
        for item in self.storage.values():
            if not item_types or item.item_type in item_types:
                yield item

    def __repr__(self):
        return str(self.storage)
