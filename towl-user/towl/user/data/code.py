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

import functools
import rich
from .timerange import EventTimeRange
from .scenario import Scenario


class PythonCodeStack:
    def __init__(self, data):
        self._data = data

    @property
    def data(self):
        return self._data

    def push(self, pc: "PythonCode") -> "PythonCodeStack":
        data = [pc] + self._data
        return PythonCodeStack(data)

    def back(self):
        if len(self.data) > 1:
            return self.data[1]
        return None

    def show(self, *, path_limit: int = 40, limit: int = 9999):
        xs = []
        xs += [
            f"[red][bold]WARNING:[/bold] We can see only routines/blocks marked with `towl.instrument`[/]"
        ]
        data = self.data[0:limit]
        for i, pc in enumerate(data):
            p = self._path(pc.filename, path_limit)
            xs += [f"==> {i:3}. stack [bold green]{pc.funcname}[/]"]
            xs += [f"       [bold]location[/]: [bold blue]{p}:{pc.line}[/]"]
            xs += [f"    [bold]event range[/]: [bold]{pc.event_timerange}[/]"]
            xs += [f"       [bold]mark_id[/]: {pc.mark_id}"]

        msg = "\n".join(xs)
        rich.print(msg)

    def _path(self, path, limit):
        p = path[-limit:]
        if len(p) != len(path):
            p = "..." + p
        return p

    def __len__(self):
        return len(self.data)


class PythonCodeCalls:
    def __init__(self, scenario, data):
        self._data = [entry[0] for entry in data]
        self._ranges = [EventTimeRange(entry[1], entry[2] + 1)
                        for entry in data]
        self._scenario = scenario

    @property
    def data(self):
        return self._data

    def _path(self, path, limit):
        p = path[-limit:]
        if len(p) != len(path):
            p = "..." + p
        return p

    def _pc(self, index: int):
        pc = PythonCode(
            self._scenario, self.data[index], PythonCodeStack(
                []), self._ranges[index]
        )
        return pc

    def __len__(self):
        return len(self.data)

    def show(self, *, path_limit=40, limit: int = 9999):
        xs = []
        xs += [
            f"[red][bold]WARNING:[/bold] We can see only routines/blocks marked with `towl.instrument`[/]"
        ]
        data = self.data[0:limit]
        for i, mark_id in enumerate(data):
            pc = PythonCode(self._scenario, mark_id, PythonCodeStack([]), None)
            p = self._path(pc.filename, path_limit)
            xs += [f"==> {i:3}. call [bold green]{pc.funcname}[/]"]
            xs += [f"       [bold]location[/]: [bold blue]{p}:{pc.line}[/]"]
            xs += [f"    [bold]event range[/]: [bold]{pc.event_timerange}[/]"]
            xs += [f"       [bold]mark_id[/]: {mark_id}"]

        msg = "\n".join(xs)
        rich.print(msg)


class PythonCode:
    @staticmethod
    def make(scenario: Scenario, event_time_range: EventTimeRange):
        return PythonCode(scenario, -1, PythonCodeStack([]), event_time_range)

    def __init__(
        self,
        scenario: Scenario,
        mark_id: int,
        stack: "PythonCodeStack",
        given_event_time_range=None,
    ):
        self._scenario = scenario
        self._stack = stack.push(self)
        self._mark_id = int(mark_id)
        self._given_event_time_range = given_event_time_range

    @property
    def mark_id(self):
        return self._mark_id

    @property
    @functools.cache
    def filename(self):
        if self._mark_id == -1:
            return "GIVEN_TIMERANGE"
        df = self._scenario._common_view.query_python_log_by_mark_id(
            self._mark_id)
        return df.iloc[0]["filename"]

    @property
    @functools.cache
    def funcname(self):
        if self._mark_id == -1:
            return "GIVEN_TIMERANGE"
        df = self._scenario._common_view.query_python_log_by_mark_id(
            self._mark_id)
        return df.iloc[0]["funcname"]

    @property
    @functools.cache
    def line(self):
        if self._mark_id == -1:
            return 0
        df = self._scenario._common_view.query_python_log_by_mark_id(
            self._mark_id)
        return df.iloc[0]["lineno"]

    @property
    @functools.cache
    def event_timerange(self) -> EventTimeRange:
        if self._mark_id == -1:
            return self._given_event_time_range
        if self._given_event_time_range is not None:
            return self._given_event_time_range
        df = self._scenario._common_view.query_python_log_by_mark_id(
            self._mark_id)
        begin, end = df.index[0], df.index[1] + 1
        return EventTimeRange(begin, end)

    def make_view(self):
        return self._scenario.make_view(self.event_timerange)

    @property
    @functools.cache
    def calls(self):
        df = self._scenario.make_view(self.event_timerange).query_python_log()
        body_order = []
        substack = []
        if self._mark_id == -1:
            shift = 0
        else:
            shift = 1
        import tqdm

        df = df[df["command"].isin(["mark-code-enter", "mark-code-exit"])]

        for i in tqdm.trange(shift, len(df) - shift):
            row = df.iloc[i]
            mark_id = row["mark_id"]
            if row["command"] == "mark-code-enter":
                substack.append((int(mark_id), df.index[i]))
            elif row["command"] == "mark-code-exit":
                if len(substack) == 0:
                    continue
                prev_mark_id, event_enter = substack.pop()
                if len(substack) == 0:
                    assert int(mark_id) == prev_mark_id
                    body_call = (int(mark_id), event_enter, df.index[i])
                    body_order.append(body_call)
        print(f"Found {len(body_order)} subcalls")
        return PythonCodeCalls(self._scenario, body_order)

    def enter(self, index: int):
        mark_id = self.calls.data[index]
        return PythonCode(self._scenario, mark_id, self.stack)

    def enter_event(self, event_index: int):
        if not self.event_timerange.has(event_index):
            return None
        calls = self.calls
        import tqdm

        for i in tqdm.trange(len(calls)):
            pc = calls._pc(i)
            if pc.event_timerange.has(event_index):
                return self.enter(i).enter_event(event_index)
        return self

    def back(self):
        return self.stack.back()

    @property
    def stack(self):
        return self._stack

    def __repr__(self):
        return f"PythonCode(mark_id={self._mark_id}, event_timerange={self.event_timerange}) func: {self.funcname} loc:  {self.filename}:{self.line}"
