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
    def get_items(self, *item_types):
        return [x for x in self.storage.values() if x.item_type in item_types]


class TestEngine(testtools.TestCase):

    @mock.patch('redis.StrictRedis.from_url', StrictRedisMock.from_url)
    @mock.patch('time.sleep', mock.MagicMock)
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

        core.process(scenario, 0)

        nets = self.world.get_items('net')
        self.assertEqual(2, len(nets))

        meta_net = self.world.get_items('meta_net')[0]
        self.assertEqual(2, len(meta_net.refs))
