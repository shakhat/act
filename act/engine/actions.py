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
    depends_on = None
    limit = None

    def __init__(self):
        super(Action, self).__init__()

    def get_weight(self):
        return self.weight

    def get_depends_on(self):
        return self.depends_on

    def get_limit(self):
        return self.limit

    def filter_items(self, items):
        pass

    def reserve_items(self, items):
        pass

    def release_items(self, items):
        pass

    def do_action(self, items, task_id):
        return operations.Operation(task_id)

    def act(self, items):
        raise NotImplementedError()

    def __repr__(self):
        return type(self).__name__


class ReadLockAction(Action):

    def filter_items(self, items):
        for item in items:
            if item.can_be_taken():
                yield item

    def reserve_items(self, items):
        for item in items:
            item.take()

    def release_items(self, items):
        for item in items:
            item.free()


class CreateAction(ReadLockAction):
    weight = 0.9

    def do_action(self, items, task_id):
        action_result = self.act(items)
        return operations.CreateOperation(
            item=action_result, dependencies=items, task_id=task_id)


class BatchCreateAction(ReadLockAction):
    weight = 0.9

    def do_action(self, items, task_id):
        new_items = self.act(items)
        return operations.BatchCreateOperation(
            new_items=new_items, dependencies=items, task_id=task_id)


class WriteLockAction(Action):

    def filter_items(self, items):
        for item in items:
            if item.can_be_locked():
                yield item

    def reserve_items(self, items):
        for item in items:
            item.lock()

    def release_items(self, items):
        for item in items:
            item.unlock()


class DeleteAction(WriteLockAction):
    weight = 0.1

    def do_action(self, items, task_id):
        assert len(items) == 1
        self.act(items)
        return operations.DeleteOperation(item=items[0], task_id=task_id)


class IdempotantAction(ReadLockAction):
    pass


class IdempotantBlockingAction(WriteLockAction):
    pass
