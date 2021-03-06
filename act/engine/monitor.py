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

LOGO = """
 _____  ____ _____
(____ |/ ___|_   _)
/ ___ ( (___  | |
\_____|\____) |_|
"""
LOGO2 = """
 ____   ____  _____
 ____| |        |
|____| |____    |
"""

green = functools.partial(click.style, fg='green')
red = functools.partial(click.style, fg='red')


def get_scale(x):
    """Finds the lowest scale where x <= scale."""
    scales = [20, 50, 100, 200, 400, 600, 800, 1000]
    for scale in scales:
        if x <= scale:
            return scale
    return x


def make_canvas(width, height):
    return [[' ' for x in range(width)] for y in range(height)]


def place(canvas, block, x, y):
    lines = block.split('\n')
    for i, line in enumerate(lines):
        if y + i >= len(canvas):
            break
        for j, ch in enumerate(line):
            if j + x >= len(canvas[y + i]):
                break
            canvas[y + i][j + x] = ch


def render(canvas):
    for line in canvas:
        click.echo(''.join(line))


def show():
    click.clear()

    term_width, term_height = click.get_terminal_size()
    canvas = make_canvas(term_width, term_height - 1)

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

    place(canvas, LOGO2, 0, 0)

    s = tabulate(t, headers=headers, tablefmt='simple')
    place(canvas, s, 25, 0)

    render(canvas)

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
