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

import testtools

from act.engine import item
from act.engine import world


class TestWorld(testtools.TestCase):

    def test_put(self):
        globe = world.World()
        angle = item.Item('angle', {})
        globe.put(angle)

        rect = item.Item('rect', {})

        globe.put(rect, [angle])

        self.assertEqual(angle.id, rect.dependencies[0])
