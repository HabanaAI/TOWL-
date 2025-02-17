################################################################################
# Copyright 2024 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################

import os
import numpy as np
import typing

_is_typeguard_enabled = os.environ.get(
    "TOWL_TYPEGUARD", "1").lower() in ["1", "true"]


def _dummy_typechecked(f):
    return f


if _is_typeguard_enabled:
    from typeguard import typechecked
else:
    typechecked = _dummy_typechecked


int_or_int64 = typing.Union[int, np.int64]

__all__ = ["typechecked", "int_or_int64"]
