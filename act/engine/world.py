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
        LOG.debug('Put item to the world: %s', item)
        self.storage[item.id] = item

        if dependencies:
            for dep in dependencies:
                # dependencies are copies of storage objects!
                real_dep = self.storage[dep.id]
                real_dep.add_ref(item.id)
                real_dep.unlock()

    def pop(self, item):
        LOG.debug('Remove item from the world: %s', item)
        for ref_id in self.storage[item.id].refs:
            self.storage[ref_id].del_ref(item.id)

        del self.storage[item.id]

    def filter_items(self, item_types):
        for item in self.storage.values():
            if not item_types or item.item_type in item_types:
                yield item

    def __repr__(self):
        return str(self.storage)
