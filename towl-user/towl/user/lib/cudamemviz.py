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

import towl.user.cudamemviz as cv
from ..data.scenario_view import ScenarioView
import numpy as np
from typing import Optional


def dump_cudamemviz(view: ScenarioView, snapshot_path: str, html_path: Optional[str]):
    """
    Converts memory usage information (see `ScenarioView.query_memory_usage`) into
    PyTorch CUDA Memory Visualizer snapshot format and builds HTML page containing
    visualization.

    The `snapshot_path` is path to temporary file where converted data can be stored
    and `html_path` is name of output HTML file.
    """
    snapshot = build_cudamemviz(view)
    cv.model.dump_snapshot_to_file(snapshot_path, snapshot)
    if html_path is not None:
        cv.extract.to_html(snapshot_path, html_path)


def build_cudamemviz(view: ScenarioView):
    xs = []
    df = view._query_devmem_bufs_full()
    b = cv.Builder()

    for i in range(len(df)):
        import json

        entry = df.iloc[i]
        meta = json.loads(entry.meta)
        if meta["unknown"]:
            ident = entry["ident"]
            bufname = f"UNK_{ident}"
        else:
            ident = entry["ident"]
            bufname = f"BUF_{ident}"

        def to_int(x):

            if x is None or np.isnan(x):
                return -1
            return int(x)

        events = (
            to_int(entry["event_malloc"]),
            to_int(entry["event_first_launch"]),
            to_int(entry["event_last_launch"]),
            to_int(entry["event_free"]),
        )

        frames = meta["alloc_frames"]

        if len(frames) > 0:
            xs.append(bufname)

        b.record(
            entry["is_allocation"],
            entry["addr"],
            entry["size"],
            bufname=bufname,
            events=events,
            frames=frames,
        )

    snapshot = b.finish()

    return snapshot
