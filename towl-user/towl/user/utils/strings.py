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

def memory_str(x):
    if x < 0:
        return "-" + memory_str(-x)
    v = float(x)
    suffix = None
    if v > 1024:
        v /= 1024
        suffix = "KiB"
    if v > 1024:
        v /= 1024
        suffix = "MiB"
    if v > 1024:
        v /= 1024
        suffix = "GiB"
    result = str(x) + " B"
    if suffix is not None:
        result = f"{v:.3f} {suffix}"
    return result


def to_hex(x: int):
    return f"0x{x:x}"
