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

from .log_reader import read_log_file
from .data import Event
from .data import Event, EventKind, Event_DevMemMalloc, LogEntry
from .data import Event_DevMemMalloc, Event_DevMemFree, Event_DevMemSummary
from .data import Event_RecipeLaunch, Event_RecipeFinished, Event_RecipeLaunchBuf
from .data import Event_PythonGeneric, Event_PythonTowlCmd
from typing import Generator, Any
from .data import TowlCommand
import msgspec


class EventReader:
    def __init__(self, path: str):
        self._path = path
        self._dispatch = {
            EventKind.DEVMEM_MALLOC.value: self._parse_devmem_malloc,
            EventKind.DEVMEM_FREE.value: self._parse_devmem_free,
            EventKind.DEVMEM_SUMMARY.value: self._parse_devmem_summary,
            EventKind.RECIPE_LAUNCH.value: self._parse_recipe_launch,
            EventKind.RECIPE_FINISHED.value: self._parse_recipe_finished,
            EventKind.RECIPE_LAUNCH_BUF.value: self._parse_recipe_launch_buf,
            EventKind.PYTHON_GENERIC.value: self._parse_python_generic,
        }

    def _parse_python_generic(self, log_entry: LogEntry, content: str):
        import json

        if content.startswith("TOWL-CMD: "):
            content = content[len("TOWL-CMD: ") :]
            content = msgspec.json.decode(content, type=TowlCommand)
            yield Event_PythonTowlCmd(
                log_entry.tid,
                log_entry.timestamp,
                content.command,
                content.payload,
            )

    def _parse_devmem_malloc(self, log_entry: LogEntry, content: str):
        columns = content.split(" ")
        addr = int(columns[0], 16)
        size = int(columns[2])
        stream = int(columns[4])

        yield Event_DevMemMalloc(
            log_entry.tid,
            log_entry.timestamp,
            addr,
            size,
            stream,
        )

    def _parse_devmem_free(self, log_entry: LogEntry, content: str):
        columns = content.split(" ")
        addr = int(columns[0], 16)
        yield Event_DevMemFree(
            log_entry.tid,
            log_entry.timestamp,
            addr,
        )

    def _parse_devmem_summary(self, log_entry: LogEntry, content: str):
        columns = content.split(" ", maxsplit=7)
        used = int(columns[1])
        workspace = int(columns[3])
        persistent = int(columns[5])
        tag = columns[7]
        yield Event_DevMemSummary(
            log_entry.tid,
            log_entry.timestamp,
            used,
            workspace,
            persistent,
            tag,
        )

    def _parse_recipe_launch(self, log_entry: LogEntry, content: str):
        columns = content.split(" ", maxsplit=7)
        ws = int(columns[1])
        addr = int(columns[3], 16)
        nbufs = int(columns[5])
        name = columns[-1]
        yield Event_RecipeLaunch(
            log_entry.tid,
            log_entry.timestamp,
            ws,
            nbufs,
            addr,
            name,
        )

    def _parse_recipe_launch_buf(self, log_entry: LogEntry, content: str):
        columns = content.split(" ", maxsplit=10)

        index = int(columns[0])
        tensor_id = int(columns[2])
        tensor_type = columns[4]
        device_addr = int(columns[6], 16)
        handle_addr = int(columns[8], 16)
        synapse_name = columns[10]

        yield Event_RecipeLaunchBuf(
            log_entry.tid,
            log_entry.timestamp,
            index,
            tensor_id,
            tensor_type,
            device_addr,
            handle_addr,
            synapse_name,
        )

    def _parse_recipe_finished(self, log_entry: LogEntry, content: str):
        columns = content.split(" ")
        addr = int(columns[0], 16)
        yield Event_RecipeFinished(
            log_entry.tid,
            log_entry.timestamp,
            addr,
        )

    def read_events(self) -> Generator[Event, Any, Any]:
        for log_entry in read_log_file(self._path):
            event_kind, content = log_entry.content.split(" ", maxsplit=1)
            parser = self._dispatch.get(event_kind, None)
            if parser is not None:
                yield from parser(log_entry, content)


def read_events_file(path: str):
    yield from EventReader(path).read_events()
