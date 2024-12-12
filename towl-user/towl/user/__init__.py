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

__doc__ = """
Torch Owl - user interface.

 * See `towl-notebooks` directory inside the saturn repository.

"""

from . import cli
from . import cudamemviz
from . import data
from . import lib
from . import plots

from .data import Scenario, ScenarioView, EventTimeRange, RecipeLaunch
from .data import WallclockTimeRange

__pdoc__ = {
    "data": False,
    "cli": False,
    "cudamemviz": False,
    "utils": False,
    "WallclockTimeRange": False,
}

__all__ = [
    "Scenario",
    "ScenarioView",
    "EventTimeRange",
    "RecipeLaunch",
    "WallclockTimeRange",
    "lib",
    "plots",
    "cudamemviz",
]
