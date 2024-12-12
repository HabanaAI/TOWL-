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

"""Collection of useful routines and helpers.
"""

from . import footprint
from . import zigzag
from . import cudamemviz
from . import zombie
from . import framelog

from .footprint import MemoryFootprint
from .zigzag import find_hills, find_zigzags
from .cudamemviz import dump_cudamemviz
from .zombie import ZombieAnalysisResult, analyze_zombie
from .framelog import decode_framelog

__pdoc__ = {
    "footprint": False,
    "zigzag": False,
    "cudamemviz": False,
    "MemoryFootprint": False,
    "find_zigzags": False,
}

__all__ = [
    "MemoryFootprint",
    "find_hills",
    "find_zigzags",
    "dump_cudamemviz",
]
