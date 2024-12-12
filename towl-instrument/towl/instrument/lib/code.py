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
from towl.instrument.utils.frame import (
    FrameInfo,
    get_your_caller_frame,
    get_frame_for_function,
)


class MarkCodePayload(TypedDict):
    message: str
    mark_id: int
    frame: Optional[FrameInfo]


class CodeMarker:
    _MARK_ID = 1

    @classmethod
    def _get_mark_id(self) -> int:
        mark_id = self._MARK_ID
        self._MARK_ID += 1
        return mark_id

    def __init__(
        self,
        kind: str,
        title: str,
        sync_after: bool,
        sync_before: bool,
        frame: Optional[FrameInfo],
    ):
        self._kind = kind
        self._title = title
        self._sync_before = sync_before
        self._sync_after = sync_after
        self._frame = frame
        self._mark_id = self._get_mark_id()

    def __enter__(self):
        frame = self._frame
        if frame is None:
            frame = get_your_caller_frame(1)
        payload = MarkCodePayload(
            message=self._title, frame=frame, mark_id=self._mark_id
        )
        emit_towl_command("mark-code-enter", payload)

    def __exit__(self, *args):
        frame = self._frame
        if frame is None:
            frame = get_your_caller_frame(1)
        payload = MarkCodePayload(
            message=self._title, frame=frame, mark_id=self._mark_id
        )
        emit_towl_command("mark-code-exit", payload)


def mark_block(title: str, *, sync_before=False, sync_after=False):
    """
    Mark block of code
    """
    return CodeMarker("block", title, sync_before, sync_after, None)


class CallableWrapper:
    def __init__(self, callable, codemarker: CodeMarker):
        self._codemarker = codemarker
        self._callable = callable

    def _call(self, *args, **kwargs):
        with self._codemarker:
            return self._callable(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        return self._call(*args, **kwargs)


def dtype_to_bytes(dt):
    import torch

    if dt == torch.float32:
        return 4
    if dt == torch.float64:
        return 8
    if dt == torch.int32:
        return 4
    if dt == torch.bfloat16:
        return 2
    return 0


def _grad_hook(orig, grad):
    from towl.instrument import script_log

    bsize = dtype_to_bytes(grad.dtype) * grad.numel()
    script_log("grad", grad.dtype, grad.numel(), bsize)


def mark_func(*, title: str, sync_before=False, sync_after=False):
    """
    Mark blody of function
    """

    def decorator(f):
        qname = f"{f.__module__}.{f.__qualname__}"
        if hasattr(f, "__towl_wrapper__"):
            qname = getattr(f, "__towl_wrapper__")
            print(f"Function already has installed wrapper:", qname)
            return f

        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            with CodeMarker(
                "func",
                title,
                sync_before=sync_before,
                sync_after=sync_after,
                frame=get_frame_for_function(f),
            ):
                y = f(*args, **kwargs)

                if False:
                    import torch
                    if isinstance(y, torch.Tensor):
                        if y.requires_grad:
                            y.register_hook(lambda grad: _grad_hook(y, grad))
                return y

        setattr(wrapper, "__towl_wrapper__", qname)
        return wrapper

    return decorator


def wrap_model(model):
    def decorate(f):
        g = f.forward
        if g.__module__.startswith("peft."):
            print("ignored", g.__module__, g.__name__)
            return
        print("towl wrapping forward: ", g.__module__, g.__name__)
        f.forward = mark_func(title="wrap_model")(f.forward)

    model.apply(decorate)
