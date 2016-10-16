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

import mock
import redis
import rq
import testtools

from act.actions import network as a
from act.engine import core
from act.engine import world as world_pkg


class StrictRedisMock(mock.MagicMock, redis.StrictRedis):
    @classmethod
    def from_url(cls, arg, db=None, **kwargs):
        return cls()


class QueueMock(mock.MagicMock):
    def enqueue(self, f, *args, **kwargs):
        class _Item(object):
            return_value = f(*args, **kwargs)
        return _Item()


class StopWatchMock(mock.MagicMock):
    def __init__(self, *args, **kw):
        super(StopWatchMock, self).__init__(*args, **kw)
        self.counter = 0
        self.duration = kw.get('duration')

    def expired(self):
        self.counter += 1
        return self.counter > self.duration

    @classmethod
    def make_instance(cls, *args, **kwargs):
        return cls(*args, **kwargs)


class WorldMock(world_pkg.World):
    def reset(self):
        self.storage.clear()

    def get_items(self, *item_types):
        return [x for x in self.storage.values() if x.item_type in item_types]

    def get_one_item(self, item_type):
        return self.get_items(item_type)[0]


class RandomChoiceMock(object):
    def __init__(self):
        self.timeline = None
        self.counter = -1

    def setup(self, timeline):
        self.timeline = timeline
        self.counter = 0

    def weighted_random_choice(self, objs):
        assert self.timeline is not None
        obj_types = set(type(o) for o in objs)
        assert obj_types == set(self.timeline[self.counter]['options'])

        choice_type = self.timeline[self.counter]['choice']
        self.counter += 1

        for obj in objs:
            if type(obj) == choice_type:
                return obj


@mock.patch('time.sleep', mock.MagicMock)
class TestEngine(testtools.TestCase):

    @mock.patch('redis.StrictRedis.from_url', StrictRedisMock.from_url)
    def setUp(self):
        queue_patcher = mock.patch('rq.Queue')
        mock_queue = queue_patcher.start()
        mock_queue.return_value = QueueMock()
        self.addCleanup(queue_patcher.stop)

        watch_patcher = mock.patch('oslo_utils.timeutils.StopWatch')
        mock_watch = watch_patcher.start()
        mock_watch.side_effect = StopWatchMock.make_instance
        self.addCleanup(watch_patcher.stop)

        world_patcher = mock.patch('act.engine.world.World')
        self.world = WorldMock()
        mock_world = world_patcher.start()
        mock_world.return_value = self.world
        self.addCleanup(world_patcher.stop)

        rq.push_connection(StrictRedisMock())
        self.addCleanup(rq.pop_connection)

        choice_patcher = mock.patch('act.engine.utils.weighted_random_choice')
        self.choice = RandomChoiceMock()
        mock_choice = choice_patcher.start()
        mock_choice.side_effect = self.choice.weighted_random_choice
        self.addCleanup(choice_patcher.stop)

        return super(TestEngine, self).setUp()

    def test_one_create_action(self):
        # this scenario should create 2 networks
        scenario = {
            'play': [
                {
                    'duration': 2,
                    'concurrency': 1,
                    'filter': 'CreateNetwork',
                }
            ],
            'title': __name__
        }

        timeline = [
            {  # step 0
                'options': [a.CreateNetwork],
                'choice': a.CreateNetwork,
            },
            {  # step 1
                'options': [a.CreateNetwork],
                'choice': a.CreateNetwork,
            },
        ]
        self.choice.setup(timeline)
        self.world.reset()

        core.process(scenario, 0)

        nets = self.world.get_items('net')
        self.assertEqual(2, len(nets))

        meta_net = self.world.get_one_item('meta_net')
        self.assertEqual(2, meta_net.use_count)

    def test_dependent_create_actions(self):
        # this scenario should create 1 network and 1 subnet
        scenario = {
            'play': [
                {
                    'duration': 2,
                    'concurrency': 1,
                    'filter': 'CreateNetwork|CreateSubnet',
                }
            ],
            'title': __name__
        }

        timeline = [
            {  # step 0
                'options': [a.CreateNetwork],
                'choice': a.CreateNetwork,
            },
            {  # step 1
                'options': [a.CreateNetwork, a.CreateSubnet],
                'choice': a.CreateSubnet,
            },
        ]
        self.choice.setup(timeline)
        self.world.reset()

        core.process(scenario, 0)

        self.assertEqual(1, len(self.world.get_items('net')))
        self.assertEqual(1, len(self.world.get_items('subnet')))
        self.assertEqual(1, self.world.get_one_item('meta_net').use_count)
        self.assertEqual(1, self.world.get_one_item('meta_subnet').use_count)

        net = self.world.get_one_item('net')
        self.assertEqual(1, net.use_count)
