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
from typing import Union
import pandas as pd


def extract_memory_usage(
    inp: Union[str, model.Snapshot], device: int = 0
) -> pd.DataFrame:
    if type(inp) is str:
        snapshot = model.load_snapshot_from_file(inp)
    else:
        snapshot = inp
    traces = model.get_device_traces(snapshot, device)

    allocated_memory = 0

    rows = []

    for trace in traces:
        if trace["action"] == "alloc":
            allocated_memory += trace["size"]
            dump = True
        elif trace["action"] == "free_completed":
            allocated_memory -= trace["size"]
            dump = True
        else:
            dump = False
        if dump:
            rows.append(allocated_memory)

    df = pd.DataFrame(dict(used=rows))
    df["used_gb"] = df["used"] / 1024**3
    return df


def cut(inp: Union[str, model.Snapshot], begin, end, device=0) -> model.Snapshot:
    if type(inp) is str:
        snapshot = model.load_snapshot_from_file(inp)
    else:
        snapshot = inp
    traces = model.get_device_traces(snapshot, device)

    filtered_trace = []
    index = 0
    for trace in traces:
        if trace["action"] == "alloc":
            dump = True
        elif trace["action"] == "free_requested":
            dump = True
        elif trace["action"] == "free_completed":
            index -= 1
            dump = True
        else:
            dump = False
        if dump:
            if begin <= index and index < end:
                filtered_trace.append(trace)
            index += 1

    snapshot = model.Snapshot(segments=[], device_traces=[filtered_trace])
    return snapshot


def cut_and_dump(
    inp: Union[str, model.Snapshot], out: str, begin, end, device=0
) -> model.Snapshot:
    snapshot = cut(inp, begin, end, device)
    model.dump_snapshot_to_file(out, snapshot)
    return snapshot


def to_html(path: str, output: str):
    import sys
    import os

    cmd = [
        sys.executable,
        "-m",
        "torch.cuda._memory_viz",
        "trace_plot",
        "-o",
        f"'{output}'",
        f"'{path}'",
    ]
    cmd = " ".join(cmd)
    print(">", cmd)
    os.system(cmd)
