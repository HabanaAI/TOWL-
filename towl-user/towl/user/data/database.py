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

from towl.user.utils.typechecked import typechecked
from towl.db.store import Database as Database
from .timerange import EventTimeRange
import pandas as pd
from typing import Optional
import os
from ..utils.strings import memory_str
from towl.db.store import model


@typechecked
class DatabaseFacade:
    def __init__(self, path: str):
        self._db = Database(os.path.join(path, "towl.db"))

    def fetch_global_timerange(self):
        end = self._db.query_number_of_events()
        return EventTimeRange(0, end)

    def query_events(
        self,
        timerange: EventTimeRange,
    ) -> pd.DataFrame:
        columns = [
            "event_ident",
            "tid",
            "timestamp",
            "event_kind",
        ]
        cursor = self._db.query_events(timerange.begin, timerange.end)
        df = pd.DataFrame(cursor, columns=columns)
        df.set_index("event_ident", inplace=True, drop=True)
        from datetime import datetime

        df["timestamp"] = df["timestamp"].map(
            lambda x: datetime.fromisoformat(x).time()
        )
        return df

    def query_recipe_launch_by_launch_ident(self, launch_ident: int):
        x = self._db.query_launch_by_launch_id(launch_ident)
        return self._query_launch(*x)

    def query_recipe_launch_by_event_ident(self, event_ident: int):
        x = self._db.query_launch_by_event_ident(event_ident)
        return self._query_launch(*x)

    def _query_launch(self, event_ident: int, m: model.DataRecipeLaunch):
        from .recipe_launch import RecipeLaunch

        return RecipeLaunch(
            event_ident=event_ident,
            launch_ident=m.ident,
            workspace=m.workspace,
            handle=m.handle,
            event_launch=m.event_launch,
            event_finished=m.event_finished,
            buffer_ids=m.buffers,
            db=self,
        )

    def query_devmem_summary(
        self,
        timerange: EventTimeRange,
        tag: Optional[str],
    ) -> pd.DataFrame:
        cursor = self._db.query_devmem_summary(
            timerange.begin, timerange.end, tag)
        columns = ["event_ident", "used", "workspace", "persistent", "tag"]
        df = pd.DataFrame(cursor, columns=columns)
        df.set_index("event_ident", drop=True, inplace=True)

        return df

    def query_devmem_bufs_full(self, timerange: EventTimeRange) -> pd.DataFrame:

        cursor = self._db.query_devmem_bufs_full(
            timerange.begin, timerange.end)
        columns = [
            "event_ident",
            "is_allocation",
            "ident",
            "addr",
            "size",
            "event_malloc",
            "event_free",
            "event_first_launch",
            "event_last_launch",
            "meta",
            "unknown",
        ]

        df = pd.DataFrame(cursor, columns=columns)
        df["addr"] = 2 * df["addr"]
        df.set_index("event_ident", inplace=True, drop=True)
        return df

    def query_launches(self, timerange: EventTimeRange):
        cursor = self._db.query_launches(timerange.begin, timerange.end)
        columns = [
            "event_ident",
            "launch_ident",
            "workspace",
            "handle",
            "name",
            "event_launch",
            "event_finished",
        ]
        df = pd.DataFrame(cursor, columns=columns)
        df["workspace_gb"] = df["workspace"] / (1024**3)
        df["handle_hex"] = df["handle"].map(lambda x: f"0x{x:x}")
        df.set_index("event_ident", drop=True, inplace=True)
        return df

    def query_buffers_allocs(self, timerange: EventTimeRange) -> pd.DataFrame:
        cursor = self._db.query_devmem_bufs(timerange.begin, timerange.end)
        columns = [
            "event_ident",
            "is_allocation",
            "buffer_ident",
            "addr",
            "size",
            "event_malloc",
            "event_free",
            "event_first_launch",
            "event_last_launch",
            "unknown",
        ]

        df = pd.DataFrame(cursor, columns=columns)
        df["bufname"] = df["buffer_ident"].map(lambda x: f"BUF_{x}")
        df["addr"] = 2 * df["addr"]
        df["addr_str"] = df["addr"].map(lambda x: f"0x{x:x}")
        df["size_str"] = df["size"].map(memory_str)

        def f(i: int):
            row = df.iloc[i]
            size = row["size"]
            is_alloc = row["is_allocation"]
            if is_alloc:
                return size
            else:
                return -size

        import numpy as np

        df["change"] = np.array(map(f, range(len(df))))
        df["change_str"] = df["change"].map(memory_str)

        df.set_index("event_ident", inplace=True, drop=True)
        return df

    def query_launches(self, timerange: EventTimeRange):
        cursor = self._db.query_launches(timerange.begin, timerange.end)
        columns = [
            "event_ident",
            "launch_ident",
            "workspace",
            "handle",
            "event_launch",
            "event_finished",
            "recipe_name",
        ]
        df = pd.DataFrame(cursor, columns=columns)
        df["workspace_str"] = df["workspace"].map(memory_str)
        df["handle_str"] = df["handle"].map(lambda x: f"0x{x:x}")
        df.set_index("event_ident", drop=True, inplace=True)
        return df

    def query_python_log_full(self, timerange: EventTimeRange, *, map_basename: bool):
        cursor = self._db.query_python_log(
            timerange.begin,
            timerange.end,
        )
        columns = [
            "event_ident",
            "command",
            "message",
            "funcname",
            "filename",
            "lineno",
            "content",
            "mark_id",
        ]
        df = pd.DataFrame(cursor, columns=columns)
        df.set_index("event_ident", inplace=True, drop=True)

        if map_basename:
            df["filename"] = df["filename"].map(os.path.basename)
        return df

    def query_python_log_full_by_mark_id(self, mark_id: int, *, map_basename: bool):
        cursor = self._db.query_python_log_by_mark_id(
            mark_id,
        )
        columns = [
            "event_ident",
            "command",
            "message",
            "funcname",
            "filename",
            "lineno",
            "content",
            "mark_id",
        ]
        df = pd.DataFrame(cursor, columns=columns)
        df.set_index("event_ident", inplace=True, drop=True)

        if map_basename:
            df["filename"] = df["filename"].map(os.path.basename)
        return df
