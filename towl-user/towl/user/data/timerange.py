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

import datetime
from typeguard import typechecked
import numpy as np
from towl.user.utils.typechecked import int_or_int64


@typechecked
class EventTimeRange:
    """
    The event time range object. Represents time interval
    starting at `begin` and ending **before** `end`.

    So the interval `[begin; end)` is left-closed and right-closed
    like ranges in C++.
    """

    def __init__(self, begin: int_or_int64, end: int_or_int64):
        self._begin = int(begin)
        self._end = int(end)

    @staticmethod
    def make(begin, end):
        return EventTimeRange(int(begin), int(end))

    @property
    def begin(self):
        "Event number starting the interval"
        return self._begin

    @property
    def end(self):
        "Event number closing the interval"
        return self._end

    def __len__(self):
        return self.end - self.begin

    def __repr__(self):
        return f"EventTimeRange(begin={self.begin}; end={self.end}; {len(self)} events)"

    def __add__(self, other: "EventTimeRange"):
        if type(other) not in [EventTimeRange]:
            raise RuntimeError("EventTimeRange can be added to timerange only")

        lhs = min(self.begin, other.begin)
        rhs = max(self.end, other.end)
        return EventTimeRange(lhs, rhs)

    def alter(self, *, begin: int = 0, end: int = 0):
        """
        Returns a new interval where `begin` and `end` are adjusted by given
        parameters.
        """
        return EventTimeRange(self.begin + begin, self.end + end)

    def has(self, index: int_or_int64) -> bool:
        "Check if given event number is contained inside timerange"
        return bool(self.begin <= index and index < self.end)


@typechecked
class WallclockTimeRange:
    def __init__(self, begin: datetime.time, end: datetime.time):
        self._begin = begin
        self._end = end

    def __repr__(self):
        return (
            f"WallclockTimeRange(begin={self._begin}; end={self.end}; {self.length()})"
        )

    def length(self):
        return self._end - self._begin

    @property
    def begin(self):
        return self._begin

    @property
    def end(self):
        return self._end
