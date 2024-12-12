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

from pydantic import BaseModel
from typing import NamedTuple, Optional, Any
from datetime import datetime
from enum import Enum
from towl.db.store import model


class LogEntry(NamedTuple):
    lineno: int
    timestamp: datetime
    tid: Optional[int]
    content: str


class EventKind(Enum):
    RECIPE_LAUNCH = "recipe.launch"
    RECIPE_LAUNCH_BUF = "recipe.launch.buf"
    RECIPE_FINISHED = "recipe.finished"
    DEVMEM_MALLOC = "devmem.malloc"
    DEVMEM_FREE = "devmem.free"
    DEVMEM_SUMMARY = "devmem.summary"
    PYTHON_GENERIC = "python"
    PYTHON_TOWLCMD = "python_towlcmd"


class Event:
    def __init__(self, kind: EventKind, tid: int, timestamp: datetime):
        self.kind = kind
        self.tid = tid
        self.timestamp = timestamp

    def __repr__(self):
        aux = self._repr_helper()
        return f"Event(kind={self.kind}; {aux})"

    def _repr_helper(self):
        return f"tid={self.tid}; timestamp={self.timestamp}"


class Event_DevMemMalloc(Event):
    def __init__(
        self, tid: int, timestamp: datetime, addr: int, size: int, stream: int
    ):
        super().__init__(EventKind.DEVMEM_MALLOC, tid, timestamp)
        self.addr = addr
        self.size = size
        self.stream = stream

    def __repr__(self):
        aux = self._repr_helper()
        return f"Event_DevMemMalloc({aux}; addr=0x{self.addr:x}; size={self.size}; stream={self.stream})"


class Event_DevMemFree(Event):
    def __init__(self, tid: int, timestamp: datetime, addr: int):
        super().__init__(EventKind.DEVMEM_FREE, tid, timestamp)
        self.addr = addr

    def __repr__(self):
        aux = self._repr_helper()
        return f"Event_DevMemFree({aux}; addr=0x{self.addr:x})"


class Event_DevMemSummary(Event):
    def __init__(
        self,
        tid: int,
        timestamp: datetime,
        used: int,
        workspace: int,
        persistent: int,
        tag: str,
    ):
        super().__init__(EventKind.DEVMEM_SUMMARY, tid, timestamp)
        self.used = used
        self.workspace = workspace
        self.persistent = persistent
        self.tag = tag

    def __repr__(self):
        aux = self._repr_helper()
        return f"Event_DevMemSummary({aux}; used={self.used}; workspace={self.workspace}; persistent={self.persistent}; tag={repr(self.tag)})"


class Event_RecipeLaunch(Event):
    def __init__(
        self,
        tid: int,
        timestamp: datetime,
        workspace_size: int,
        nbuffers: int,
        handle: int,
        name: str,
    ):
        super().__init__(EventKind.RECIPE_LAUNCH, tid, timestamp)
        self.workspace_size = workspace_size
        self.nbuffers = nbuffers
        self.handle = handle
        self.name = name

    def __repr__(self):
        aux = self._repr_helper()
        return f"Event_RecipeLaunch({aux}; handle=0x{self.handle:x}; workspace_size={self.workspace_size}; nbufs={self.nbuffers}; name={repr(self.name)}))"


class Event_RecipeLaunchBuf(Event):
    def __init__(
        self,
        tid: int,
        timestamp: datetime,
        index: int,
        tensor_id: int,
        tensor_type: str,
        device_addr: int,
        handle_addr: int,
        synapse_name: str,
    ):
        super().__init__(EventKind.RECIPE_LAUNCH_BUF, tid, timestamp)
        self.index = index
        self.tensor_id = tensor_id
        self.tensor_type = tensor_type
        self.device_addr = device_addr
        self.handle_addr = handle_addr
        self.synapse_name = synapse_name

    def __repr__(self):
        aux = self._repr_helper()
        c = ""
        c += f"; index={self.index}"
        c += f"; tensor_id={self.tensor_id}"
        c += f"; tensor_type={self.tensor_type}"
        c += f"; device_addr=0x{self.device_addr:x}"
        c += f"; handle_addr=0x{self.handle_addr:x}"
        c += f"; synapse_name={repr(self.synapse_name)}"
        return f"Event_RecipeLaunchBuf({aux}{c})"


class Event_PythonGeneric(Event):
    def __init__(self, tid: int, timestamp: datetime, content):
        super().__init__(EventKind.PYTHON_GENERIC, tid, timestamp)
        self.content = content

    def __repr__(self):
        aux = self._repr_helper()
        return f"Event_PythonGeneric({aux}; {self.c})"


class Event_PythonTowlCmd(Event):
    def __init__(self, tid: int, timestamp: datetime, command: str, payload):
        super().__init__(EventKind.PYTHON_TOWLCMD, tid, timestamp)
        self.command = command
        self.payload = payload

    def __repr__(self):
        aux = self._repr_helper()
        return f"Event_PythonTowlCmd({aux}; {self.command} {self.content})"


class Event_RecipeFinished(Event):
    def __init__(self, tid: int, timestamp: datetime, handle: int):
        super().__init__(EventKind.RECIPE_FINISHED, tid, timestamp)
        self.handle = handle

    def __repr__(self):
        aux = self._repr_helper()
        return f"Event_RecipeFinished({aux}; handle=0x{self.handle:x})"


class TowlCommand(BaseModel):
    command: str
    payload: Any
