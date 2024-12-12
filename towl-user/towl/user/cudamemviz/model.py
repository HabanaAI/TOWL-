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

from typing import TypedDict, List, Literal
import pickle
from towl.user.utils.file import smart_open


class Frame(TypedDict):
    filename: str
    line: int
    name: str


class TraceEntry(TypedDict):
    # When `torch.cuda.memory._record_memory_history()` is enabled,
    # the snapshot will contain TraceEntry objects that record each
    # action the allocator took.
    action: Literal[
        "alloc"  # memory allocated
        "free_requested",  # the allocated received a call to free memory
        "free_completed",  # the memory that was requested to be freed is now
        # able to be used in future allocation calls
        "segment_alloc",  # the caching allocator ask cudaMalloc for more memory
        # and added it as a segment in its cache
        "segment_free",  # the caching allocator called cudaFree to return memory
        # to cuda possibly trying free up memory to
        # allocate more segments or because empty_caches was called
        "oom",  # the allocator threw an OOM exception. 'size' is
        # the requested number of bytes that did not succeed
        "snapshot",  # the allocator generated a memory snapshot
        # useful to coorelate a previously taken
        # snapshot with this trace
    ]
    addr: int  # not present for OOM
    frames: List[Frame]
    size: int
    stream: int
    device_free: int  # only present for OOM, the amount of
    # memory cuda still reports to be free


class Block(TypedDict):
    # A piece of memory returned from the allocator, or
    # current cached but inactive.
    size: int
    requested_size: int  # size requested during malloc, may be smaller than
    # size due to rounding
    address: int
    state: Literal[
        "active_allocated",  # used by a tensor
        "active_awaiting_free",  # waiting for another stream to finish using
        # this, then it will become free
        "inactive",
    ]  # free for reuse
    frames: List[Frame]  # stack trace from where the allocation occurred


class Segment(TypedDict):
    # Segments are memory returned from a cudaMalloc call.
    # The size of reserved memory is the sum of all Segments.
    # Segments are cached and reused for future allocations.
    # If the reuse is smaller than the segment, the segment
    # is split into more then one Block.
    # empty_cache() frees Segments that are entirely inactive.
    address: int
    total_size: int  # cudaMalloc'd size of segment
    stream: int
    segment_type: Literal["small", "large"]  # 'large' (>1MB)
    allocated_size: int  # size of memory in use
    active_size: int  # size of memory in use or in active_awaiting_free state
    blocks: List[Block]


class Snapshot(TypedDict):
    segments: List[Segment]
    device_traces: List[List[TraceEntry]]


def load_snapshot_from_file(path) -> Snapshot:
    with smart_open(path, "rb") as fd:
        return pickle.load(fd)


def dump_snapshot_to_file(path, snapshot: Snapshot):
    with smart_open(path, "wb") as fd:
        pickle.dump(snapshot, fd)


def filter_out_non_python_frames(snapshot: Snapshot):
    import copy
    import os

    all_traces = []
    for traces in snapshot["device_traces"]:
        new_traces = []
        for trace in traces:
            trace = copy.deepcopy(trace)
            frames = trace["frames"]
            trace["frames"] = []
            for frame in frames:
                fname = frame["filename"]
                if not fname.endswith(".py"):
                    continue
                trace["frames"].append(frame)
            new_traces.append(trace)
        all_traces.append(new_traces)
    return Snapshot(segments=[], device_traces=all_traces)


def get_allocation_sizes(snapshot: Snapshot, device=0):
    allocs = []
    for trace in snapshot["device_traces"][device]:
        if trace["action"] == "alloc":
            allocs.append(trace["size"])
    return allocs


def get_device_traces(snapshot: Snapshot, device_index: int) -> List[TraceEntry]:
    all_traces = snapshot["device_traces"]
    if len(all_traces) <= device_index:
        raise RuntimeError(f"No device {device_index} in CUDA Snapshot traces")
    return all_traces[device_index]
