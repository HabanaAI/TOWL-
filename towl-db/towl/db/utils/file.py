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

import lzma
import gzip
import io


def smart_open(path, mode):
    if "t" not in mode and "b" not in mode:
        mode += "t"

    if path.endswith(".xz"):
        fd = lzma.open(path, mode)
    elif path.endswith(".gz"):
        fd = gzip.open(path, mode)
    else:
        fd = io.open(path, mode)

    return fd
