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

import weakref
import inspect
import functools
import threading
from typing import List
from ..core.command import emit_towl_command
from ..utils.frame import FrameInfo
from dataclasses import dataclass
from typing import TypedDict


class AttachAllocationPointPayload(TypedDict):
    addr: int
    frames: List[FrameInfo]


def get_stack_trace(maxdepth=30):
    frames = inspect.stack()[3: maxdepth + 3]
    return [FrameInfo.make(frame.frame) for frame in frames]


class TensorRegistryImpl:
    def __init__(self):
        self._tensors = []
        self._mutex = threading.Lock()
        self._thread = None

        self._keepalive = False
        self._keepalive_cache = {}

    def get_keepalive(self):
        return self._keepalive

    def set_keepalive(self, v):
        self._keepalive = v
        if not v:
            self._keepalive_cache = {}

    def watch_tensor(self, tensor):
        stack = get_stack_trace()
        with self._mutex:
            self._watch_tensor(tensor, stack)

    def _watch_tensor(self, tensor, stack):
        if not self._check_storage(tensor, stack):
            self._tensors.append((weakref.ref(tensor), stack))

    def _check_storage(self, tensor, stack):
        from habana_frameworks.torch.utils.debug import get_tensor_info

        info = get_tensor_info(tensor)
        if info is None:
            return False
        addr, _ = info
        if addr == 0:
            return False
        attach_allocation_point_command(addr, stack)

        return True

    def check_storages(self):
        with self._mutex:
            tensors, self._tensors = self._tensors, []

            for tensor_ref, stack in tensors:
                tensor = tensor_ref()
                if tensor is None:
                    continue
                self._watch_tensor(tensor, stack)


TensorRegistry = TensorRegistryImpl()


def decorate(f):
    @functools.wraps(f)
    def wrap(*args, **kwargs):
        import torch

        y = f(*args, **kwargs)
        if type(y) is not torch.Tensor:
            return y
        if "hpu" not in str(y.device):
            return y

        TensorRegistry.watch_tensor(y)
        TensorRegistry.check_storages()
        return y

    return wrap


def _thread_main(interval):
    try:
        import time

        while True:
            time.sleep(interval)
            TensorRegistry.check_storages()
    except Exception as e:
        print("INTERNAL ERROR", type(e), e)
        raise


class MemoryInterceptorImpl:
    def __init__(self):
        self._enabled = False
        self._visited_modules = set()

    def _install_wrappers_on(self, m, k, v, *, recursive):
        if inspect.isbuiltin(v):
            setattr(m, k, decorate(v))
            return
        if inspect.isfunction(v):
            setattr(m, k, decorate(v))
            return
        if inspect.isroutine(v):
            setattr(m, k, decorate(v))
            return
        if inspect.ismodule(v):
            if "config" in str(v):
                return
            if "habana" in str(v):
                if "hpex" not in str(v):
                    return
                print("INSTALL", v)
            if "torch" not in str(v):
                return
            if recursive:
                self.install_wrappers_on(v, recursive=recursive)

        # old
        tp = str(type(v))
        if "'builtin_function_or_method'" not in tp and "'function'" not in tp:
            return
        setattr(m, k, decorate(v))

    def install_wrappers_on(self, m, *, recursive):
        import inspect

        if m in self._visited_modules:
            return
        self._visited_modules.add(m)
        print("INSTALL", m)
        for k, v in m.__dict__.items():
            self._install_wrappers_on(m, k, v, recursive=recursive)

    def enable(self, interval=0.5):
        if self._enabled:
            raise Exception("Memory interceptor already enabled!")
        self._enabled = True
        self._install_wrappers()
        self._start_thread(interval)

    def _install_wrappers(self):
        import torch

        # import torch.ops.hpu as opthpu
        import habana_frameworks.torch.hpex as hpex
        import habana_frameworks.torch.hpex.kernels as hpex_k
        import habana_frameworks.torch.hpex.normalization as hpex_n
        import habana_frameworks.torch.hpex.experimental.transformer_engine as hpex_t

        self.install_wrappers_on(torch, recursive=True)
        self.install_wrappers_on(hpex, recursive=True)
        self.install_wrappers_on(hpex_k, recursive=True)
        self.install_wrappers_on(hpex_n, recursive=True)
        self.install_wrappers_on(hpex_t, recursive=True)

        from towl.instrument.lib.code import _grad_hook

        self._install_wrappers_on(
            torch, "_grad_hook", _grad_hook, recursive=False)

    def sync(*, mark_step=False):
        if mark_step:
            import habana_frameworks.torch as ht

            ht.core.mark_step()
        TensorRegistry.check_storages()

    def _start_thread(self, interval):
        if TensorRegistry._thread is not None:
            return
        TensorRegistry._thread = threading.Thread(
            target=_thread_main, args=(interval,))
        TensorRegistry._thread.daemon = True
        TensorRegistry._thread.start()


MemoryInterceptor = MemoryInterceptorImpl()


def attach_allocation_point_command(addr, frames):
    payload = AttachAllocationPointPayload(addr=addr, frames=frames)
    emit_towl_command("attach-allocation-point", payload)
