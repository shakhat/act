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

from oslo_config import cfg
from oslo_log import log as logging
import rq

from act.engine import config
from act.engine import consts
from act.engine import utils


LOG = logging.getLogger(__name__)


def run():
    utils.init_config_and_logging(config.ENGINE_OPTS)

    redis_connection = utils.make_redis_connection(host=cfg.CONF.redis_host,
                                                   port=cfg.CONF.redis_port)
    with rq.Connection(redis_connection):
        LOG.info('Connected to Redis')
        queue = rq.Queue(consts.TASK_QUEUE_NAME)
        rq.Worker(queue).work()


if __name__ == '__main__':
    run()
