# Copyright (c) 2016 OpenStack Foundation
#
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
import testtools

from act.engine import utils


class TestUtils(testtools.TestCase):
    def setUp(self):
        super(TestUtils, self).setUp()

    def test_split_address_valid(self):
        self.assertEqual(('10.0.0.1', '6777'),
                         utils.split_address('10.0.0.1:6777'))

    def test_split_address_invalid(self):
        self.assertRaises(ValueError, utils.split_address, 'erroneous')

    def test_flatten_dict(self):
        self.assertEqual({}, dict(utils.flatten_dict({})))
        self.assertEqual(
            {'pa_b': 1},
            dict(utils.flatten_dict({'a': {'b': 1}}, prefix='p', sep='_')))
        self.assertEqual(
            {'a': 1, 'b.c': 2, 'b.d': 3},
            dict(utils.flatten_dict({'a': 1, 'b': {'c': 2, 'd': 3}})))

    @mock.patch('os.walk')
    @mock.patch('act.engine.utils.resolve_relative_path')
    def test_make_help_options(self, resolve_mock, walk_mock):
        base_dir = 'abc/def'
        abs_dir = '/files/' + base_dir
        walk_mock.side_effect = [
            [(abs_dir, [], ['klm.yaml']), (abs_dir, [], ['ijk.yaml'])],
        ]
        resolve_mock.side_effect = [abs_dir]

        expected = 'List: "ijk", "klm"'
        observed = utils.make_help_options('List: %s', base_dir)
        self.assertEqual(expected, observed)

    @mock.patch('os.walk')
    @mock.patch('act.engine.utils.resolve_relative_path')
    def test_make_help_options_subdir(self, resolve_mock, walk_mock):
        base_dir = 'abc/def'
        abs_dir = '/files/' + base_dir
        walk_mock.side_effect = [
            [(abs_dir + '/sub', [], ['klm.yaml']),
             (abs_dir + '/sub', [], ['ijk.yaml'])],
        ]
        resolve_mock.side_effect = [abs_dir]

        expected = 'List: "sub/ijk", "sub/klm"'
        observed = utils.make_help_options('List: %s', base_dir)
        self.assertEqual(expected, observed)

    @mock.patch('os.walk')
    @mock.patch('act.engine.utils.resolve_relative_path')
    def test_make_help_options_with_filter(self, resolve_mock, walk_mock):
        base_dir = 'abc/def'
        abs_dir = '/files/' + base_dir
        walk_mock.side_effect = [
            [(abs_dir + '/sub', [], ['klm.yaml']),
             (abs_dir + '/sub', [], ['ijk.html']),
             (abs_dir + '/sub', [], ['mno.yaml'])],
        ]
        resolve_mock.side_effect = [abs_dir]

        expected = 'List: "sub/klm", "sub/mno"'
        observed = utils.make_help_options(
            'List: %s', base_dir, type_filter=lambda x: x.endswith('.yaml'))
        self.assertEqual(expected, observed)

    def test_algebraic_product_empty(self):
        expected = [{}]

        observed = list(utils.algebraic_product())

        self.assertEqual(expected, observed)

    def test_algebraic_product_string(self):
        expected = [{'a': 1, 'b': 'zebra'}, {'a': 2, 'b': 'zebra'}]

        observed = list(utils.algebraic_product(a=[1, 2], b='zebra'))

        self.assertEqual(expected, observed)

    def test_algebraic_product_number(self):
        expected = [{'a': 'x', 'b': 4}, {'a': 2, 'b': 4}]

        observed = list(utils.algebraic_product(a=['x', 2], b=4))

        self.assertEqual(expected, observed)

    def test_strict(self):
        self.assertEqual('some_01_string_a',
                         utils.strict('Some 01-string (brr!) + %% A'))

    @mock.patch('random.random')
    def test_weighted_random_choice(self, mock_random):
        class _ItemWithWeight(object):
            def __init__(self, value, weight):
                self.value = value
                self.weight = weight

        items = [
            _ItemWithWeight('abc', 0.1),
            _ItemWithWeight('def', 0.3),
            _ItemWithWeight('klm', 0.6),
        ]

        mock_random.return_value = 0.05
        observed = utils.weighted_random_choice(items)
        self.assertEqual('abc', observed.value)

        mock_random.return_value = 0.25
        observed = utils.weighted_random_choice(items)
        self.assertEqual('def', observed.value)

        mock_random.return_value = 0.5
        observed = utils.weighted_random_choice(items)
        self.assertEqual('klm', observed.value)
