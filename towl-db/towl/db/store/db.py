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

import sqlite3
import os
from . import sql
from towl.db.store import model
import json
from typeguard import typechecked
from typing import Optional
import msgspec


class Database:
    def __init__(self, path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Not found database: {path}")

        self._db = sqlite3.connect(path)

        self._db.executescript(sql.Opening.configure)
        self._db.commit()

    @staticmethod
    def create(path: str):
        if os.path.exists(path):
            raise RuntimeError(f"Database already exists: {path}")

        db = sqlite3.connect(path)
        try:
            db.executescript(sql.Initialization.create_tables)
            db.executescript(sql.Initialization.create_views)
            db.executescript(sql.Initialization.insert_version)
            db.executescript(sql.Initialization.insert_enums)
            db.commit()
        except:
            db.close()
            os.remove(path)
            raise
        db = Database(path)
        db._db.executescript(sql.Opening.xconfigure)
        return db

    def commit(self):
        self._db.commit()

    def close(self):
        if self._db is not None:
            self.commit()
            self._db.close()
            self._db = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def insert_event_devmem_summary(self, d: model.DeviceMemoryShortSummaryEvent):
        self._db.execute(sql.EventsInserting.insert_devmem_summary, d._asdict())

    def insert_event_devmem_buf(self, d: model.DevMemBufEvent):
        self._db.execute(sql.EventsInserting.insert_devmem_buf, d._asdict())

    def insert_event(self, d: model.Event):
        row = d._asdict()
        # row["kind"] = int(d.kind.value)
        row["timestamp"] = d.timestamp
        self._db.execute(sql.EventsInserting.insert_event, row)

    def insert_event_python(self, d: model.PythonLogEvent):
        row = msgspec.to_builtins(d)
        self._db.execute(sql.Python.insert_python, row)

    def query_python_log(self, begin: int, end: int):
        params = {
            "begin": begin,
            "end": end,
        }
        cursor = self._db.execute(sql.Python.query_python_log, params)
        cursor.row_factory = sqlite3.Row

        return cursor

    def query_python_log_by_mark_id(self, mark_id: int):
        params = {
            "mark_id": mark_id,
        }
        cursor = self._db.execute(sql.Python.query_python_log_by_mark_id, params)
        cursor.row_factory = sqlite3.Row

        return cursor

    def insert_data_buffer(self, d: model.DataBuffer):
        row = msgspec.to_builtins(d)
        row["meta"] = msgspec.json.encode(d.meta).decode()
        row["unknown"] = d.meta.unknown
        row["addr"] = row["addr"] // 2
        self._db.execute(sql.Buffers.insert_buffer, row)

    def update_data_buffer_events(self, d: model.DataBuffer):
        row = {
            "ident": d.ident,
            "event_malloc": d.event_malloc,
            "event_free": d.event_free,
            "event_first_launch": d.event_first_launch,
            "event_last_launch": d.event_last_launch,
        }

        self._db.execute(sql.Buffers.update_buffer_events, row)

    def update_data_buffer_meta(self, d: model.DataBuffer):
        row = {
            "ident": d.ident,
            "meta": msgspec.json.encode(d.meta).decode(),
        }

        self._db.execute(sql.Buffers.update_buffer_meta, row)

    def update_launch_events(self, d: model.DataRecipeLaunch):
        row = {
            "ident": d.ident,
            "event_launch": d.event_launch,
            "event_finished": d.event_finished,
        }
        self._db.execute(sql.Launches.update_launch_events, row)

    def insert_data_launch(self, d: model.DataRecipeLaunch):
        row = msgspec.to_builtins(d)
        del row["buffers"]
        row["meta"] = msgspec.json.encode(d.meta).decode()
        self._db.execute(sql.Launches.insert_launch, row)

        rows = [
            (d.ident, buf.buffer, buf.index, buf.offset, buf.synapse_name)
            for buf in d.buffers
        ]

        self._db.executemany(sql.Launches.insert_launch_buf, rows)

    def query_events(self, begin: int, end: int):
        params = {
            "begin": begin,
            "end": end,
        }
        return self._db.execute(sql.Query.query_events, params)

    def query_number_of_events(self):
        for r in self._db.execute(sql.Opening.count_events):
            return r[0]

    def query_devmem_summary(self, begin: int, end: int, tag: Optional[str]):
        if tag is None:
            return self._db.execute(
                sql.Query.query_devmem_summary, dict(begin=begin, end=end)
            )
        else:
            return self._db.execute(
                sql.Query.query_devmem_summary_tag, dict(begin=begin, end=end, tag=tag)
            )

    def query_devmem_bufs(self, begin: int, end: int):
        return self._db.execute(sql.Query.query_devmem_bufs, dict(begin=begin, end=end))

    def query_devmem_bufs_full(self, begin: int, end: int):
        return self._db.execute(
            sql.Query.query_devmem_bufs_full, dict(begin=begin, end=end)
        )

    def query_buffers(self):
        for row in self._db.execute(sql.Buffers.query_buffers):
            (
                ident,
                addr,
                size,
                meta,
                event_malloc,
                event_free,
                event_first_launch,
                event_last_launch,
            ) = row
            meta = model.DataBufferMeta(**json.loads(meta))
            b = model.DataBuffer(
                ident=ident,
                addr=addr * 2,
                size=size,
                meta=meta,
                event_malloc=event_malloc,
                event_free=event_free,
                event_first_launch=event_first_launch,
                event_last_launch=event_last_launch,
            )
            yield b

    def query_launches(self, begin: int, end: int):
        return self._db.execute(sql.Query.query_launches, dict(begin=begin, end=end))

    def query_launch_by_event_ident(self, event_ident: int):
        cursor = self._db.execute(
            sql.Launches.query_launch_by_event_id, dict(event_ident=event_ident)
        )
        cursor = list(cursor)
        if len(cursor) == 0:
            raise KeyError(f"Cannot find launch with event ident {event_ident}")

        (
            event_ident,
            ident,
            workspace,
            handle,
            name,
            meta,
            event_launch,
            event_finished,
        ) = cursor[0]
        meta = json.loads(meta)

        return self._finish_query_launch(
            event_ident,
            ident,
            handle,
            workspace,
            name,
            meta,
            event_launch,
            event_finished,
        )

    def query_launch_by_launch_id(self, launch_ident: int):
        cursor = self._db.execute(
            sql.Launches.query_launch_by_launch_id, dict(launch_ident=launch_ident)
        )
        cursor = list(cursor)
        if len(cursor) == 0:
            raise KeyError(f"Cannot find launch with ident {launch_ident}")

        (
            event_ident,
            ident,
            workspace,
            handle,
            name,
            meta,
            event_launch,
            event_finished,
        ) = cursor[0]
        meta = json.loads(meta)
        return self._finish_query_launch(
            event_ident,
            ident,
            handle,
            workspace,
            name,
            meta,
            event_launch,
            event_finished,
        )

    def query_launch_bufs(
        self,
        launch_ident,
    ):
        cursor = self._db.execute(
            sql.Launches.query_launch_bufs_by_launch_id, dict(launch_ident=launch_ident)
        )
        cursor.row_factory = sqlite3.Row

        for row in cursor:
            meta = model.DataBufferMeta(**json.loads(row["meta"]))
            yield model.DataBuffer(
                ident=row["ident"],
                addr=row["addr"] * 2,
                size=row["size"],
                meta=meta,
                event_malloc=row["event_malloc"],
                event_free=row["event_malloc"],
                event_first_launch=row["event_first_launch"],
                event_last_launch=row["event_last_launch"],
            )

    def _finish_query_launch(
        self,
        event_ident: int,
        ident,
        handle,
        workspace,
        name,
        meta,
        event_launch,
        event_finished,
    ):
        launch_buffers = []
        cursor = self._db.execute(
            sql.Launches.query_launch_bufs_by_launch_id, dict(launch_ident=ident)
        )
        cursor.row_factory = sqlite3.Row
        for row in cursor:
            x = model.DataRecipeLaunchBuffer(
                buffer=row["ident"],
                offset=row["offset"],
                index=row["index"],
                synapse_name=row["synapse_name"],
            )
            launch_buffers.append(x)

        launch = model.DataRecipeLaunch(
            ident=ident,
            handle=handle,
            workspace=workspace,
            buffers=launch_buffers,
            meta=meta,
            recipe_name=name,
            event_finished=event_finished,
            event_launch=event_launch,
        )

        return event_ident, launch

    def cleanup(self):
        self._db.commit()
        self._db.execute(sql.Initialization.cleanup)
        self._db.commit()
