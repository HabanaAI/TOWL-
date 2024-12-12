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

from . import model


class Builder:
    def __init__(self):
        self._traces = []
        self._addr_id = {}

    def _get_addr(self, addr):
        if addr not in self._addr_id:
            ident = len(self._addr_id)
            self._addr_id[addr] = ident
        return self._addr_id[addr]

    def finish(self) -> model.Snapshot:
        self._traces, traces = [], self._traces
        return model.Snapshot(segments=[], device_traces=[traces])

    def _build_frames_bufname(self, bufname):
        if bufname is None:
            return []

        frame = model.Frame(name=bufname, filename="BUFFER_NAME", line=0)
        return [frame]

    def _build_frames_events(self, events):
        if events is None:
            return []
        event_malloc, event_first_launch, event_last_launch, event_free = events

        frames = [
            model.Frame(name="malloc", filename="EVENTS", line=event_malloc),
            model.Frame(
                name="first_launch", filename="EVENTS", line=event_first_launch
            ),
            model.Frame(name="last_launch", filename="EVENTS",
                        line=event_last_launch),
            model.Frame(name="free", filename="EVENTS", line=event_free),
        ]

        return frames

    def _build_frames_stack(self, framess):
        if framess is None or len(framess) == 0:
            return []
        _frames = []

        frame = model.Frame(
            name="", filename="ATTACHED STACKS", line=len(framess))
        _frames.append(frame)

        for i, frames in enumerate(framess):
            frame = model.Frame(name="", filename="======== STACK", line=i)
            _frames.append(frame)
            for frame in frames:
                _frame = model.Frame(
                    filename=frame["filename"],
                    line=frame["line"],
                    name=frame["funcname"],
                )
                _frames.append(_frame)

        return _frames

    def record_malloc(
        self, addr: int, size: int, *, bufname=None, frames=None, events=None
    ):
        _frames = []
        _frames += self._build_frames_bufname(bufname)
        _frames += self._build_frames_events(events)
        _frames += self._build_frames_stack(frames)
        trace = model.TraceEntry(
            action="alloc",
            addr=self._get_addr(addr),
            frames=_frames,
            size=int(size),
            stream=0,
            device_free=0,
        )
        self._traces.append(trace)

    def record_free(self, addr, size, *, bufname=None):
        frames = []
        frames += self._build_frames_bufname(bufname)
        trace_r = model.TraceEntry(
            action="free_requested",
            addr=self._get_addr(addr),
            frames=frames,
            size=int(size),
            stream=0,
            device_free=0,
        )
        trace_c = model.TraceEntry(
            action="free_completed",
            addr=self._get_addr(addr),
            frames=frames,
            size=int(size),
            stream=0,
            device_free=0,
        )
        self._traces.append(trace_r)
        self._traces.append(trace_c)

    def record(
        self, is_allocation, addr, size, *, bufname=None, frames=None, events=None
    ):
        if is_allocation:
            self.record_malloc(
                addr, size, bufname=bufname, frames=frames, events=events
            )
        else:
            self.record_free(addr, size, bufname=bufname)
