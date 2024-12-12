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
from typing import List
from towl.user.utils.strings import memory_str
from .timerange import EventTimeRange
from typeguard import typechecked
from towl.db.store import model
import pandas as pd


@typechecked
class RecipeLaunch:
    """
    The recipe launch representation.
    """

    def __init__(
        self,
        *,
        event_ident: int,
        launch_ident: int,
        workspace: int,
        handle: int,
        event_launch: int,
        event_finished: int,
        buffer_ids: List[model.DataRecipeLaunchBuffer],
        db: DatabaseFacade,
    ):
        self.event_ident = event_ident
        self.launch_ident = launch_ident
        self.workspace = workspace
        self.handle = handle
        self.event_launch = event_launch
        self.event_finished = event_finished
        self.buffer_ids = buffer_ids
        self._db = db

    def __repr__(self):
        ws = memory_str(self.workspace)
        return f"RecipeLaunch(event_ident={self.event_ident} launch_ident={self.launch_ident} handle=0x{self.handle:x} workspace={ws} event={{launch={self.event_launch} finished={self.event_finished}}})"

    @property
    def event_lifetime(self) -> EventTimeRange:
        """
        Returns event time range representing recipe life time -- from launch event
        to finished event.

        In simple words: `(event_launch, event_finished + 1)`.
        """
        return EventTimeRange(self.event_launch, self.event_finished + 1)

    def query_recipe_launch_buffers(self) -> pd.DataFrame:
        """
        Returns pandas DataFrame representing buffers passed to recipe
        for this launch.
        """
        d = {x: [] for x in model.DataRecipeLaunchBuffer.model_fields}
        for entry in self.buffer_ids:
            for k, v in entry:
                d[k].append(v)

        df = pd.DataFrame.from_dict(d)
        df.set_index("index", drop=True, inplace=True)
        df["bufname"] = df["buffer"].map(lambda x: f"BUF_{x}")
        return df
