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

from .command import emit_towl_command
from ..utils.strings import log_to_str
from ..utils.frame import get_your_caller_frame, FrameInfo, scan_frames, FrameVariables
from dataclasses import dataclass
from ..utils.sync import maybe_sync
from typing import TypedDict, Optional, List


class ScriptLogPayload(TypedDict):
    message: str
    frame: Optional[FrameInfo]


class FrameLogPayload(TypedDict):
    message: str
    frame: Optional[FrameInfo]
    stack: List[FrameVariables]


def script_log(*args, sync=False):
    maybe_sync(sync)
    message = log_to_str(*args)
    frame = get_your_caller_frame()
    payload = ScriptLogPayload(message=message, frame=frame)
    emit_towl_command("script-log", payload)


def frame_log(*args, sync=False, stack_depth=1, object_depth=10):
    maybe_sync(sync)
    message = log_to_str(*args)
    frame = get_your_caller_frame()
    stack = scan_frames(stack_depth, object_depth)
    payload = FrameLogPayload(message=message, frame=frame, stack=stack)
    emit_towl_command("frame-log", payload)
