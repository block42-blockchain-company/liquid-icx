# -*- coding: utf-8 -*-

# Copyright 2020 ICONation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from iconservice import *

# ================================================
#  Consts
# ================================================
MAX_ITERATION_LOOP = 100

TAG = 'LiquidICX'
VERSION = '0.1.0'
SYSTEM_SCORE = Address.from_string('cx0000000000000000000000000000000000000000')
ZERO_WALLET_ADDRESS = Address.from_string('hx0000000000000000000000000000000000000000')

TERM_LENGTH = 43120
UNSTAKING_MARGIN = 300

# Temporary System Contract for easier developing
FAKE_SYSTEM_CONTRACT_LOCAL = Address.from_string('cx7c0f2d7d4253a230177bf95b897e0321ac5e43d1')
FAKE_SYSTEM_CONTRACT_YEOUIDO = Address.from_string('cx2b01010a92bf78ee464be0b5eff94676e95cd757')

# ------------ LOCAL NET -------------
PREP_ADDRESS = Address.from_string("hxca1e081e686ec4975d14e0fb8f966c3f068298be")
