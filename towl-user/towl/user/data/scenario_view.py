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
import pandas as pd
from typing import Optional
import towl.user.utils.strings as ustrings
from ..utils.strings import memory_str
from .common_view import CommonView


@typechecked
class ScenarioView:
    """
    Scenario view. Object gives access to data related to given `EventTimeRange`.

    * See `Scenario.make_view`
    """

    def __init__(self, db: DatabaseFacade, event_timerange: EventTimeRange):
        self._db = db
        self._event_timerange = event_timerange
        self._common_view = CommonView(db)

    def make_view(self, event_timerange: EventTimeRange):
        "Make a view for given timerange. See `Scenario.make_view`."
        return ScenarioView(self._db, event_timerange)

    @property
    def event_timerange(self) -> EventTimeRange:
        "Event time range associated with this view"
        return self._event_timerange

    def query_events(self) -> pd.DataFrame:
        "Returns pandas DataFrame with events"
        df = self._db.query_events(self.event_timerange)
        return df

    def query_memory_usage(self, tag: Optional[str] = None) -> pd.DataFrame:
        """
        Returns pandas DataFrame with memory usage.
        """
        df = self._db.query_devmem_summary(self.event_timerange, tag)

        df["workspace_str"] = df["workspace"].map(ustrings.memory_str)
        df["persistent_str"] = df["persistent"].map(ustrings.memory_str)
        df["used_str"] = df["used"].map(ustrings.memory_str)

        # df["addr_hex"] = df["addr"].map(ustrings.to_hex)
        # df["size_str"] = df["size"].map(ustrings.memory_str)

        return df

    def _query_devmem_bufs_full(self) -> pd.DataFrame:
        df = self._db.query_devmem_bufs_full(self._event_timerange)
        df["addr_hex"] = df["addr"].map(lambda x: f"0x{x:x}")
        df["size_str"] = df["size"].map(memory_str)
        return df

    def _x_query_recipe_launches(self) -> pd.DataFrame:
        return self._db.query_recipe_launches(self._event_timerange)

    def query_buffers_allocs(self) -> pd.DataFrame:
        """
        Returns pandas DataFrame with memory allocations and deallocations.
        """
        df = self._db.query_buffers_allocs(self._event_timerange)
        return df

    def query_recipe_launches(self) -> pd.DataFrame:
        """
        Returns pandas DataFrame with recipe launches.
        """
        df = self._db.query_launches(self._event_timerange)
        return df

    def query_recipe_launch_by_launch_ident(self, launch_ident: int):
        "Returns `RecipeLaunch` representation for given `launch_ident`"
        return self._common_view.query_recipe_launch_by_launch_ident(launch_ident)

    def query_recipe_launch_by_event_ident(self, event_ident: int):
        "Returns `RecipeLaunch` representation for given `event_ident`"
        return self._common_view.query_recipe_launch_by_event_ident(event_ident)

    def query_python_log(self, *, map_basename=False) -> pd.DataFrame:
        "Returns pandas DataFrame with python log events"
        df = self._query_python_log_full(map_basename=map_basename)
        del df["content"]
        return df

    def _query_python_log_full(self, *, map_basename=False) -> pd.DataFrame:
        df = self._db.query_python_log_full(
            self._event_timerange,
            map_basename=map_basename,
        )
        return df
