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

from act.engine import operations


LOG = logging.getLogger(__name__)


class Action(object):
    weight = 0.1
    meta_type = None
    depends_on = None

    def __init__(self):
        super(Action, self).__init__()

    def get_weight(self):
        return self.weight

    def get_meta_type(self):
        return self.meta_type

    def get_depends_on(self):
        return self.depends_on

    def filter_items(self, items):
        pass

    def do_action(self, items, task_id):
        return operations.Operation(task_id)

    def act(self, items):
        raise NotImplementedError()

    def __repr__(self):
        return type(self).__name__


class CreateAction(Action):
    weight = 0.9

    def __init__(self):
        super(CreateAction, self).__init__()

    def filter_items(self, items):
        for item in items:
            if item.can_be_used():
                yield item

    def do_action(self, items, task_id):
        action_result = self.act(items)
        return operations.CreateOperation(
            item=action_result, dependencies=items, task_id=task_id)


class DeleteAction(Action):
    weight = 0.1

    def filter_items(self, items):
        for item in items:
            if not item.has_dependants() and not item.is_locked():
                yield item

    def do_action(self, items, task_id):
        action_result = self.act(items)
        return operations.DeleteOperation(item=action_result, task_id=task_id)


class IdempotantAction(Action):
    def filter_items(self, items):
        for item in items:
            yield item


class IdempotantBlockingAction(Action):
    def filter_items(self, items):
        for item in items:
            if not item.is_locked():
                yield item
