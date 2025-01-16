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

from .devmem_manager import DevMemManager
from .recipe_manager import RecipeManager
from towl.db.events import Event_PythonGeneric, Event_PythonTowlCmd
from towl.db.store import model
from towl.db.store import Database
from typing import List, Any, Optional, Dict
from .primary_key_generator import PrimaryKeyGenerator
from .event_writer import EventWriter
from datetime import datetime
import msgspec


class AttachAllocationPointPayload(msgspec.Struct):
    addr: int
    frames: List[model.FrameInfo]


class FrameInfo(msgspec.Struct):
    filename: str
    line: int
    funcname: str


class ScriptLogPayload(msgspec.Struct):
    message: str
    frame: FrameInfo


class FrameVariables(msgspec.Struct):
    frame: FrameInfo
    memory: Dict[str, Any]


class FrameLogContent(msgspec.Struct):
    stack: List[FrameVariables]


class FrameLogPayload(msgspec.Struct):
    message: str
    frame: FrameInfo
    stack: List[FrameVariables]


class MarkCodePayload(msgspec.Struct):
    message: str
    frame: Optional[FrameInfo]
    mark_id: int


class PythonReactor:
    def __init__(
        self,
        db: Database,
        devmem_manager: DevMemManager,
        event_writer: EventWriter,
    ):
        self._devmem_manager = devmem_manager
        self._get_primary_key = PrimaryKeyGenerator()
        self._db = db
        self._event_writer = event_writer

    def react_python_generic(self, event: Event_PythonGeneric):
        pass

    def react_python_towlcmd(self, event: Event_PythonTowlCmd):
        if event.command == "attach-allocation-point":
            payload = msgspec.convert(
                event.payload,
                type=AttachAllocationPointPayload,
            )
            self._handle_attach_allocation_point(payload)
        elif event.command == "script-log":
            payload = msgspec.convert(
                event.payload,
                type=ScriptLogPayload,
            )
            self._handle_scriptlog(event.timestamp, event.tid, payload)
        elif event.command == "frame-log":
            payload = msgspec.convert(
                event.payload,
                type=FrameLogPayload,
            )
            self._handle_framelog(event.timestamp, event.tid, payload)
        elif event.command == "mark-code-enter":
            payload = msgspec.convert(
                event.payload,
                type=MarkCodePayload,
            )
            self._handle_mark_code_enter(event.timestamp, event.tid, payload)
        elif event.command == "mark-code-exit":
            payload = msgspec.convert(
                event.payload,
                type=MarkCodePayload,
            )
            self._handle_mark_code_exit(event.timestamp, event.tid, payload)
        else:
            raise RuntimeError(f"Unsupported command: {event.command}")

    def _handle_mark_code_enter(
        self, timestamp: datetime, tid: int, payload: MarkCodePayload
    ):
        entity = model.PythonLogEvent(
            ident=self._get_primary_key(),
            command="mark-code-enter",
            message=payload.message,
            funcname=payload.frame.funcname,
            filename=payload.frame.filename,
            lineno=payload.frame.line,
            content=None,
            mark_id=payload.mark_id,
        )
        self._db.insert_event_python(entity)
        self._event_writer.add(
            timestamp,
            tid,
            model.EventKind.PYTHON_LOG,
            entity.ident,
        )

    def _handle_mark_code_exit(
        self, timestamp: datetime, tid: int, payload: MarkCodePayload
    ):
        entity = model.PythonLogEvent(
            ident=self._get_primary_key(),
            command="mark-code-exit",
            message=payload.message,
            funcname=payload.frame.funcname,
            filename=payload.frame.filename,
            lineno=payload.frame.line,
            content=None,
            mark_id=payload.mark_id,
        )
        self._db.insert_event_python(entity)
        self._event_writer.add(
            timestamp,
            tid,
            model.EventKind.PYTHON_LOG,
            entity.ident,
        )

    def _handle_scriptlog(
        self,
        timestamp: datetime,
        tid: int,
        payload: ScriptLogPayload,
    ):
        entity = model.PythonLogEvent(
            ident=self._get_primary_key(),
            command="script-log",
            message=payload.message,
            funcname=payload.frame.funcname,
            filename=payload.frame.filename,
            lineno=payload.frame.line,
            content=None,
            mark_id=None,
        )
        self._db.insert_event_python(entity)
        self._event_writer.add(
            timestamp,
            tid,
            model.EventKind.PYTHON_LOG,
            entity.ident,
        )

    def _handle_framelog(
        self,
        timestamp: datetime,
        tid: int,
        payload: FrameLogPayload,
    ):
        stack = []
        for fvars in payload.stack:
            memory = {}
            for k, v in fvars.memory.items():
                memory[k] = self._devmem_manager.get_buffer_by_addr(v).ident
            new_fvars = FrameVariables(frame=fvars.frame, memory=memory)
            stack.append(new_fvars)

        content = msgspec.json.encode(FrameLogContent(stack=stack))
        entity = model.PythonLogEvent(
            ident=self._get_primary_key(),
            command="frame-log",
            message=payload.message,
            funcname=payload.frame.funcname,
            filename=payload.frame.filename,
            lineno=payload.frame.line,
            content=content,
            mark_id=None,
        )
        self._db.insert_event_python(entity)
        self._event_writer.add(
            timestamp,
            tid,
            model.EventKind.PYTHON_LOG,
            entity.ident,
        )

    def _handle_attach_allocation_point(self, payload: AttachAllocationPointPayload):
        buffer = self._devmem_manager.get_buffer_by_addr(payload.addr)
        buffer.meta.alloc_frames.append(payload.frames)
        self._devmem_manager.update_buffer_meta(buffer)
