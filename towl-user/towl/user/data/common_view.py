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
from .recipe_launch import RecipeLaunch
from towl.db.store import model
import pandas as pd


@typechecked
class CommonView:
    def __init__(self, db: DatabaseFacade):
        self._db = db

    def query_recipe_launch_by_launch_ident(self, launch_ident: int):
        return self._db.query_recipe_launch_by_launch_ident(launch_ident)

    def query_recipe_launch_by_event_ident(self, event_ident: int):
        return self._db.query_recipe_launch_by_event_ident(event_ident)

    def query_python_log_by_mark_id(
        self, mark_id: int, map_basename=False
    ) -> pd.DataFrame:
        "Returns pandas DataFrame with python log events"
        df = self._db.query_python_log_full_by_mark_id(
            mark_id,
            map_basename=map_basename,
        )
        return df
