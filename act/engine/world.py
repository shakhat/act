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

import collections

from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class World(object):
    def __init__(self):
        # item id -> item
        self.storage = {}
        # item type -> {item_id}
        self.type_to_ids = collections.defaultdict(set)

    def put(self, item, dependencies=None):
        self.storage[item.id] = item
        self.type_to_ids[item.item_type].add(item.id)

        if dependencies:
            item.set_dependencies([d.id for d in dependencies])

        LOG.debug('Put item to the world: %s', item)

    def pop(self, item):
        LOG.debug('Remove item from the world: %s', item)

        for dependency_id in item.dependencies:
            self.storage[dependency_id].free()

        self.type_to_ids[item.item_type].remove(item.id)
        del self.storage[item.id]

    def filter_items(self, item_types):
        if item_types:
            for one_type in item_types:
                for one_id in self.type_to_ids[one_type]:
                    yield self.storage[one_id]
        else:
            for item in self.storage.values():
                yield item

    def get_counters(self):
        return dict((t, len(v)) for t, v in self.type_to_ids.items())

    def __repr__(self):
        return str(self.storage)
