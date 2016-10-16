# -*- coding: utf-8 -*-
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

import functools
import time

import click
from oslo_config import cfg
from oslo_log import log as logging
import rq
from tabulate import tabulate

from act.engine import config
from act.engine import metrics
from act.engine import utils

LOG = logging.getLogger(__name__)


green = functools.partial(click.style, fg='green')
red = functools.partial(click.style, fg='red')


def get_scale(x):
    """Finds the lowest scale where x <= scale."""
    scales = [20, 50, 100, 200, 400, 600, 800, 1000]
    for scale in scales:
        if x <= scale:
            return scale
    return x


def show():
    click.clear()

    term_width, _ = click.get_terminal_size()
    chart_width = min(20, term_width - 20)

    m = metrics.get_all_metrics()
    max_count = max(m.value for m in m.values())

    scale = get_scale(max_count)
    ratio = chart_width * 1.0 / scale

    t = []
    headers = ['param', 'value', 'chart']
    keys = sorted(m.keys())
    for key in keys:
        metric = m[key]
        count = metric.value
        color = green if metric.mood == metrics.MOOD_HAPPY else red
        chart = color('|' + u'█' * int(ratio * count))

        t.append([key, count, chart])

    s = tabulate(t, headers=headers, tablefmt='simple')
    for line in s.split('\n'):
        click.echo(line)

    time.sleep(cfg.CONF.interval)


def run():
    utils.init_config_and_logging(config.MONITOR_OPTS)

    redis_connection = utils.make_redis_connection(host=cfg.CONF.redis_host,
                                                   port=cfg.CONF.redis_port)
    with rq.Connection(redis_connection):
        try:
            while True:
                show()
        except KeyboardInterrupt:
            LOG.info('Shutdown')


if __name__ == '__main__':
    run()
