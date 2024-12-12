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

from .database import DatabaseFacade
from towl.user.utils.typechecked import typechecked
from .timerange import EventTimeRange
from .scenario_view import ScenarioView
from .common_view import CommonView
from .recipe_launch import RecipeLaunch


@typechecked
class Scenario:
    """
    Representation of scenario stored in the database stored in the `path` directory.
    """

    def __init__(self, path: str):
        self._db = DatabaseFacade(path)
        self._common_view = CommonView(self._db)

    @property
    def global_event_timerange(self) -> EventTimeRange:
        """Returns timerange representing whole scenario"""
        return self._db.fetch_global_timerange()

    def make_view(self, event_timerange: EventTimeRange) -> ScenarioView:
        """
        Makes a view for given timerange.
        """
        return ScenarioView(self._db, event_timerange)

    def make_global_view(self) -> ScenarioView:
        """
        Shortcut for `make_view(global_timerange)`
        """
        return self.make_view(self.global_event_timerange)

    def query_recipe_launch_by_launch_ident(self, launch_ident: int) -> RecipeLaunch:
        "Returns `RecipeLaunch` representation for given `launch_ident`"
        return self._common_view.query_recipe_launch_by_launch_ident(launch_ident)

    def query_recipe_launch_by_event_ident(self, event_ident: int) -> RecipeLaunch:
        "Returns `RecipeLaunch` representation for given `event_ident`"
        return self._common_view.query_recipe_launch_by_event_ident(event_ident)

    def python_code(self, view=None):
        from .code import PythonCode

        if view is None:
            view = self.make_global_view()

        return PythonCode.make(self, view.event_timerange)
