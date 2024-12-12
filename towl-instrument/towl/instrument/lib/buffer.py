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

from towl.instrument.core.command import emit_towl_command
import functools
from typing import TypedDict, Optional
from towl.instrument.utils.frame import FrameInfo, get_your_caller_frame
from habana_frameworks.torch.utils.debug import get_tensor_info


class MarkBufferPayload(TypedDict):
    label: str
    addr: int


def mark_buffer(label: str, t):
    info = get_tensor_info(t)
    if info is None:
        return
    addr, _ = info

    payload = MarkBufferPayload(
        label=label,
        addr=addr,
    )

    emit_towl_command("mark-buffer", payload)
