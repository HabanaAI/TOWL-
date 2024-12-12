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

import towl.db.store.model as model
from towl.db.store import Database
import logging
from typing import Dict
from .primary_key_generator import PrimaryKeyGenerator
from towl.db.utils.typechecked import typechecked
from .event_writer import EventWriter
from datetime import datetime
import bisect
from typing import List, Tuple
from intervaltree import IntervalTree


class MemoryMap:
    def __init__(self):
        self._itree = IntervalTree()

    def map_buffer(self, buffer: model.DataBuffer):
        begin = buffer.addr
        end = buffer.addr + buffer.size
        self._itree.chop(begin, end)
        self._itree.addi(begin, end, buffer)

    def unmap_buffer(self, buffer: model.DataBuffer):
        begin = buffer.addr
        end = buffer.addr + buffer.size
        self._itree.chop(begin, end)

    def lookup(self, addr: int):
        xs = self._itree.at(addr)
        if len(xs) == 1:
            return list(xs)[0].data
        if len(xs) == 0:
            return None
        raise Exception(
            f"internal error: inconsistent data: len(xs)={len(xs)}")


@typechecked
class DevMemManager:
    def __init__(self, db: Database, event_writer: EventWriter):
        self._live_buffers: Dict[int, model.DataBuffer] = {}
        self._get_buffer_by_addr_primary_key = PrimaryKeyGenerator()
        self._get_operation_primary_key = PrimaryKeyGenerator()
        self._get_summary_primary_key = PrimaryKeyGenerator()
        self._event_writer = event_writer
        self._db = db
        self._memory_map = MemoryMap()
        self._all_buffers = {}

        self._needs_meta_update = set()

    def malloc(
        self,
        timestamp: datetime,
        tid: int,
        addr: int,
        size: int,
        stream: int,
        *,
        unknown=False,
    ):
        meta = model.DataBufferMeta(unknown=unknown, alloc_frames=[])
        buffer = model.DataBuffer(
            ident=self._get_buffer_by_addr_primary_key(),
            addr=addr,
            size=size,
            meta=meta,
            stream=stream,
            event_malloc=None,
            event_free=None,
            event_first_launch=None,
            event_last_launch=None,
        )
        self._all_buffers[buffer.ident] = buffer
        self._memory_map.map_buffer(buffer)
        self._live_buffers[buffer.addr] = buffer
        self._db.insert_data_buffer(buffer)

        op = model.DevMemBufEvent(
            ident=self._get_operation_primary_key(),
            buffer_ident=buffer.ident,
            is_allocation=True,
        )

        self._db.insert_event_devmem_buf(op)

        event_entity = self._event_writer.add(
            timestamp,
            tid,
            model.EventKind.DEVMEM_BUF,
            op.ident,
        )

        buffer.event_malloc = event_entity.ident
        self.update_buffer_events(buffer)

        return buffer

    def get_buffer_by_addr(self, addr: int) -> model.DataBuffer:
        buffer = self._memory_map.lookup(addr)
        if buffer is None:
            buffer = self.malloc(datetime.now(), 0, addr, 1, 0, unknown=True)
        return buffer

    def get_buffer_by_id(self, ident: int) -> model.DataBuffer:
        return self._all_buffers[ident]

    def free(self, timestamp: datetime, tid: int, addr: int):
        if addr not in self._live_buffers:
            logging.warn(f"Freeing unknown buffer: 0x{addr:x}")
            return

        buffer = self.get_buffer_by_addr(addr)
        self._memory_map.unmap_buffer(buffer)

        op = model.DevMemBufEvent(
            ident=self._get_operation_primary_key(),
            buffer_ident=buffer.ident,
            is_allocation=False,
        )
        self._db.insert_event_devmem_buf(op)

        event_entity = self._event_writer.add(
            timestamp,
            tid,
            model.EventKind.DEVMEM_BUF,
            op.ident,
        )

        buffer.event_free = event_entity.ident
        self.update_buffer_events(buffer)
        del self._live_buffers[buffer.addr]

        return buffer

    def update_buffer_events(self, buffer: model.DataBuffer):
        self._needs_meta_update.add(buffer.ident)

    def update_buffer_meta(self, buffer: model.DataBuffer):
        self._needs_meta_update.add(buffer.ident)

    def finish(self):
        for buffer_ident in self._needs_meta_update:
            buffer = self.get_buffer_by_id(buffer_ident)
            self._db.update_data_buffer_meta(buffer)
            self._db.update_data_buffer_events(buffer)

    def record_status(
        self,
        timestamp: datetime,
        tid: int,
        used: int,
        workspace: int,
        persistent: int,
        tag: str,
    ):

        entity = model.DeviceMemoryShortSummaryEvent(
            ident=self._get_summary_primary_key(),
            used=used,
            workspace=workspace,
            persistent=persistent,
            tag=tag,
        )

        self._db.insert_event_devmem_summary(entity)

        event_entity = self._event_writer.add(
            timestamp,
            tid,
            model.EventKind.DEVMEM_SUMMARY,
            entity.ident,
        )
