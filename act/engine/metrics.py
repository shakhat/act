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
import json
import time

from oslo_log import log as logging
import rq

LOG = logging.getLogger(__name__)


KEY_METRICS = 'act_metrics'
MOOD_HAPPY = 'happy'
MOOD_SAD = 'sad'

METRIC_TYPE_SUMMARY = 'summary'
METRIC_TYPE_ACTIONS = 'actions'
METRIC_TYPE_OBJECTS = 'objects'

Metric = collections.namedtuple(
    'Metric', ['metric_type', 'value', 'timestamp', 'mood'])


def clear():
    LOG.debug('Clear metrics')
    redis_connection = rq.connections.get_current_connection()
    redis_connection.delete(KEY_METRICS)


def set_metric(metric_type, metric, value, mood=MOOD_HAPPY):
    m = Metric(metric_type=metric_type, value=value, timestamp=time.time(),
               mood=mood)
    LOG.debug('Set metric %s = %s', metric, m)
    redis_connection = rq.connections.get_current_connection()
    redis_connection.hset(KEY_METRICS, metric, json.dumps(m))


def get_all_metrics():
    LOG.debug('Get all metrics')
    redis_connection = rq.connections.get_current_connection()

    all_metrics = redis_connection.hgetall(KEY_METRICS)
    result = {}
    for key, one_metric in all_metrics.items():
        m = json.loads(one_metric)
        result[key] = Metric(metric_type=m[0], value=m[1], timestamp=m[2],
                             mood=m[3])

    return result
