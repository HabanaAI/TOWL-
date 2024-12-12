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

from .file_reader import read_lines
from typing import NamedTuple, Optional
from datetime import datetime
from .data import LogEntry


class Prefix(NamedTuple):
    timestamp: datetime
    tid: Optional[int]


class LogReader:
    def __init__(self, path):
        self._path = path

    def _parse_date(self, s):
        return datetime.strptime(s, "%H:%M:%S.%f")

    def _parse_prefix(self, text: str):
        columns = text.split("]")
        timestamp = self._parse_date(columns[0][1:])
        tid = None
        s_tid = "tid:"
        for column in columns:
            column = column[1:]
            if column.startswith(s_tid):
                content = column[len(s_tid):]
                tid = int(content, 16)
        return Prefix(timestamp=timestamp, tid=tid)

    def _handle_line(self, p):
        lineno, line = p
        s_prefix, s_content = line.split(" ", maxsplit=1)
        prefix = self._parse_prefix(s_prefix)
        return LogEntry(
            lineno=lineno,
            timestamp=prefix.timestamp,
            tid=prefix.tid,
            content=s_content,
        )

    def read_log_entries(self):
        yield from map(self._handle_line, enumerate(read_lines(self._path)))


def read_log_file(path: str):
    yield from LogReader(path).read_log_entries()
