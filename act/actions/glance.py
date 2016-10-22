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

import random
import time

from oslo_log import log as logging

from act.engine import actions
from act.engine import item


LOG = logging.getLogger(__name__)


class InitGlanceTypes(actions.BatchCreateAction):
    depends_on = {'root'}
    limit = 1

    def act(self, items):
        LOG.info('Initialize Glance meta-classes')
        return (
            item.Item('meta_image'),
        )


class DiscoverImages(actions.BatchCreateAction):
    depends_on = {'meta_image'}
    limit = 1

    def act(self, items):
        LOG.info('Discover images')
        image = dict(name='Cirros', id='9999')
        return [item.Item('image', image, read_only=True)]
