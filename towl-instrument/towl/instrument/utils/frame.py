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

from dataclasses import dataclass
import inspect
from typing import TypedDict, Dict, Any, List


class FrameInfo(TypedDict):
    filename: str
    funcname: str
    line: int

    @staticmethod
    def make(frame):
        if frame is None:
            return None
        filename = frame.f_code.co_filename
        line = frame.f_lineno
        funcname = frame.f_code.co_name
        return FrameInfo(filename=filename, line=line, funcname=funcname)


class FrameVariables(TypedDict):
    frame: FrameInfo
    memory: Dict[str, Any]


def _skips(f, n: int):
    for _ in range(n):
        f = f.f_back
        if f is None:
            return None
    return f


def get_your_caller_frame(nskip: int = 1):
    frame = inspect.currentframe()
    frame = _skips(frame, nskip + 1)
    return FrameInfo.make(frame)


def get_frame_for_function(f):
    qname = f"{f.__module__}.{f.__qualname__}"
    return FrameInfo(
        filename=f.__code__.co_filename,
        funcname=qname,
        line=f.__code__.co_firstlineno,
    )


def scan_frames(stack_depth: int, object_depth: int):
    results = []
    frames = inspect.stack()[2: stack_depth + 2]
    for frame in frames:
        fvars = _scan_frame(frame.frame, object_depth)
        results.append(fvars)

    return results


def _scan_frame(frame, object_depth: int):
    memory = {}
    for k, v in frame.f_locals.items():
        r = ObjectScanner.scan(k, v, object_depth)
        if r is not None:
            memory.update(r)

    return FrameVariables(
        frame=FrameInfo.make(frame),
        memory=memory,
    )


class ObjectScanner:
    def __init__(self):
        self._visited = set()
        self._result = {}

    def _scan(self, prefix, value, max_depth):
        import torch

        if max_depth <= 0:
            return
        if id(value) in self._visited:
            return
        self._visited.add(id(value))
        if value is None:
            return
        if type(value) in [tuple, list, set]:
            for i, x in enumerate(value):
                self._scan(f"{prefix}[{i}]", x, max_depth - 1)
            return
        if type(value) in [dict]:
            for i, (k, v) in enumerate(value.items()):
                nk = str(k)
                if len(nk) > 20:
                    nk = nk[0:20] + "..."

                self._scan(f"{prefix}[dict-key {nk}]", v, max_depth - 1)
            return
        if inspect.ismodule(value):
            return
        if isinstance(value, torch.Tensor):
            if "hpu" not in str(value.device):
                return

            if value.data_ptr() != 0:
                self._result[prefix] = value.untyped_storage().data_ptr()
            return

        if hasattr(value, "__dict__"):
            for k, v in value.__dict__.items():
                try:
                    self._scan(f"{prefix}.{k}", v, max_depth - 1)
                except:
                    pass
            return

    def _start(self, prefix, value, max_depth):
        self._scan(prefix, value, max_depth)
        if len(self._result) == 0:
            return None
        return self._result

    @staticmethod
    def scan(prefix: str, v, max_depth):
        return ObjectScanner()._start(prefix, v, max_depth)
