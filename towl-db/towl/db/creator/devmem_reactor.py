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

from towl.db.events import Event_DevMemMalloc, Event_DevMemFree, Event_DevMemSummary
from .devmem_manager import DevMemManager
from towl.db.utils.typechecked import typechecked


@typechecked
class DevMemReactor:
    def __init__(self, devmem_manager: DevMemManager):
        self._devmem_manager = devmem_manager

    def react_malloc(self, event: Event_DevMemMalloc):
        self._devmem_manager.malloc(
            event.timestamp,
            event.tid,
            event.addr,
            event.size,
            event.stream,
        )

    def react_free(self, event: Event_DevMemFree):
        self._devmem_manager.free(event.timestamp, event.tid, event.addr)

    def react_summary(self, event: Event_DevMemSummary):
        self._devmem_manager.record_status(
            event.timestamp,
            event.tid,
            event.used,
            event.workspace,
            event.persistent,
            event.tag,
        )
