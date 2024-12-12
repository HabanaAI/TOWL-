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

from typing import NamedTuple, List, Optional
import enum
from towl.db.utils.pydantic import ConfiguredBaseModel
from datetime import datetime


class EventKind(enum.IntEnum):
    DEVMEM_BUF = 0
    DEVMEM_SUMMARY = 1
    RECIPE_LAUNCH = 2
    RECIPE_FINISHED = 3
    PYTHON_LOG = 4


class Event(NamedTuple):
    ident: int
    kind: EventKind
    reference: int
    timestamp: datetime
    tid: int


class DeviceMemoryShortSummaryEvent(NamedTuple):
    ident: int
    used: int
    workspace: int
    persistent: int
    tag: str


class DevMemBufEvent(NamedTuple):
    ident: int
    buffer_ident: int
    is_allocation: bool


class DevMemBufFreeEvent(NamedTuple):
    pass


class FrameInfo(ConfiguredBaseModel):
    filename: str
    funcname: str
    line: int

    @staticmethod
    def make(frame):
        filename = frame.f_code.co_filename
        line = frame.f_lineno
        funcname = frame.f_code.co_name
        return FrameInfo(filename=filename, line=line, funcname=funcname)


class DataBufferMeta(ConfiguredBaseModel):
    unknown: bool

    alloc_frames: List[List[FrameInfo]] = []


class DataBuffer(ConfiguredBaseModel):
    ident: int
    addr: int
    size: int
    stream: int
    meta: DataBufferMeta
    event_malloc: Optional[int]
    event_free: Optional[int]
    event_first_launch: Optional[int]
    event_last_launch: Optional[int]

    @property
    def name(self) -> str:
        if self.meta.unknown:
            return f"UNK_{self.ident}"
        else:
            return f"BUF_{self.ident}"


class DataRecipeLaunchBuffer(ConfiguredBaseModel):
    buffer: int
    offset: int
    index: int
    synapse_name: str


class DataRecipeLaunchMeta(NamedTuple):
    pass


class DataRecipeLaunch(ConfiguredBaseModel):
    ident: int
    handle: int
    workspace: int
    buffers: List[DataRecipeLaunchBuffer]
    meta: DataRecipeLaunchMeta
    recipe_name: str
    event_launch: Optional[int]
    event_finished: Optional[int]

    @property
    def name(self) -> str:
        return f"LAUNCH_{self.ident}"


class PythonLogEvent(ConfiguredBaseModel):
    ident: int
    command: str
    message: Optional[str]
    funcname: Optional[str]
    filename: Optional[str]
    lineno: Optional[int]
    content: Optional[str]
    mark_id: Optional[int]
