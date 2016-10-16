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

from act.engine import utils


LOG = logging.getLogger(__name__)


class Item(object):
    def __init__(self, item_type, payload, use_limit=1000):
        self.item_type = item_type
        self.payload = payload
        self.id = utils.make_id()  # unique id
        self.use_limit = use_limit  # max number of users of this item
        self.dependencies = []

        # locks
        self.locked = False  # True if the item is locked exclusively
        self.use_count = 0  # number of users of this item

    def __repr__(self):
        return str(dict(id=self.id, item_type=self.item_type,
                        payload=self.payload, dependencies=self.dependencies,
                        use_count=self.use_count, locked=self.locked))

    def set_dependencies(self, dependencies):
        self.dependencies = dependencies

    def lock(self):
        self.locked = True

    def unlock(self):
        self.locked = False

    def can_be_locked(self):
        # True if the item can be locked exclusively
        return not self.locked and (self.use_count == 0)

    def take(self):
        # take this item as dependency for the new one
        self.use_count += 1

    def free(self):
        # free this item from referencing
        self.use_count -= 1

    def can_be_taken(self):
        # True if the item can be used as dependency
        return not self.locked and (self.use_count < self.use_limit)
