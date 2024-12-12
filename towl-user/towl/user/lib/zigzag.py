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

import numpy as np
import pandas as pd
from ..data.timerange import EventTimeRange
from typing import List, Tuple


class ZigZagImpl:
    def __init__(self, series: pd.Series, threshold: int):
        self._series = series
        self._n = len(series)
        self._threshold = threshold
        self._result = []

    def _zigzag_up(self, begin):
        # print('finding next up', begin, self._series.iloc[begin])
        hill = begin
        for i in range(begin + 1, self._n):
            value_i = self._series.iloc[i]
            value_hill = self._series.iloc[hill]
            if value_i >= value_hill:
                hill = i
            else:
                diff = value_hill - value_i
                if diff >= self._threshold:
                    self._emit(1, begin, hill - 1)
                    return self._zigzag_down, hill
        self._emit(1, begin, self._n - 1)
        return None, self._n

    def _zigzag_down(self, begin):
        # print('finding next down', begin, self._series.iloc[begin])
        hill = begin
        for i in range(begin + 1, self._n):
            value_i = self._series.iloc[i]
            value_hill = self._series.iloc[hill]
            if value_i <= value_hill:
                hill = i
            else:
                diff = value_i - value_hill
                if diff >= self._threshold:
                    self._emit(-1, begin, hill - 1)
                    return self._zigzag_up, hill
        self._emit(-1, begin, self._n - 1)
        return None, self._n

    def _check_direction(self):
        value = self._series.iloc[0]
        for i in range(1, self._n):
            diff = self._series.iloc[i] - value
            if np.abs(diff) >= self._threshold:
                if diff > 0:
                    return self._zigzag_up
                else:
                    return self._zigzag_down
        return None

    def _emit(self, d, begin, end):
        tr = EventTimeRange(
            self._series.index[begin],
            self._series.index[end] + 1,
        )
        self._result.append((d, tr))

    def __call__(self):
        state = self._check_direction()
        if state is None:
            self._emit(0, self._n)
            return self._result

        begin = 0
        while begin < self._n:
            state, begin = state(begin)

        return self._result


def find_zigzags(psr: pd.Series, threshold: int) -> List[Tuple[int, EventTimeRange]]:
    return ZigZagImpl(psr, threshold)()


def find_hills(psr: pd.Series, threshold: int = 10 * 1024**3) -> List[EventTimeRange]:
    """
    Returns list of event time ranges denoting discovered hills on given time serie `psr`.

    The `threshold` parameter controls sensitivity of algorithm. Default value denotes
    10GiB.

    Example:
    ```
        find_hills(df_memory_usage['used'])
    ```
    """
    zz = find_zigzags(psr, threshold)
    if len(zz) < 2:
        return []

    result = []
    while len(zz) > 0:
        direction, zig = zz.pop(0)
        if direction != 1:
            continue
        if len(zz) == 0:
            break
        direction, zag = zz.pop(0)
        if direction != -1:
            continue

        result.append(zig + zag)

    return result
