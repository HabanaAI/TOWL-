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

from tqdm.auto import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm
import lzma
import gzip
import io
import os


class FileReader:
    def __init__(self, path):
        self._path = path
        self._size = os.stat(path).st_size

    def _open(self, raw_fd):
        if self._path.endswith(".xz"):
            fd = lzma.open(raw_fd, "rb")
        elif self._path.endswith(".gz"):
            fd = gzip.open(raw_fd, "rb")
        else:
            fd = raw_fd
        return io.TextIOWrapper(fd, encoding="utf-8", errors="replace")

    def read_lines(self):
        with logging_redirect_tqdm():
            with io.open(self._path, "rb") as raw_fd:
                with self._open(raw_fd) as in_fd:
                    yield from self._read_lines_from(raw_fd, in_fd)

    def _read_lines_from(self, raw_fd, in_fd):
        position = 0
        pbar = tqdm(
            desc="reading",
            total=self._size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
        )
        line_no = 0
        try:
            with pbar:
                for line in in_fd:
                    line_no += 1
                    new_position = raw_fd.tell()
                    pbar.update(new_position - position)
                    position = new_position
                    yield line.rstrip()
        except Exception:
            print(f"!!!!!!!!! Problem after line {line_no}")
            raise


def read_lines(path: str):
    fr = FileReader(path)
    yield from fr.read_lines()
