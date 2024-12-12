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

from towl.user.data import ScenarioView
from typing import NamedTuple
import pandas as pd
from towl.user.utils import memory_str
import towl.user.plots as P
import matplotlib.pyplot as plt
import numpy as np


class ZombieAnalysisResult(NamedTuple):
    df: pd.DataFrame
    min_size: int
    min_zombie: int

    def size_of_buffers(self):
        return self.df["size"].sum()

    def size_of_buffers_human_str(self):
        return memory_str(self.size_of_buffers())

    def plot_zombie_buffers(self):
        with P.MatplotLib():
            plt.scatter(
                self.df["size"] / 1024**2, self.df["zombie"], s=3
            )  # , marker='.', s=3)
            plt.xlabel("Buffer size (MiB)")
            plt.ylabel("Time (Events)")
            plt.yscale("log")
            plt.xticks(np.arange(50, 150, 5))
            plt.title("Zombie buffers")

    def plot_zombie_buffers_perc(self):
        with P.MatplotLib():
            plt.scatter(
                self.df["size"] / 1024**2, self.df["zombie%"], s=3
            )  # , marker='.', s=3)
            plt.xlabel("Buffer size (MiB)")
            plt.ylabel(
                "Time (Events) of not used before free (% of whole lifetime)")
            plt.xticks(np.arange(50, 150, 5))
            plt.title("Zombie buffers relative")


def analyze_zombie(
    view: ScenarioView,
    *,
    min_size: int,
    min_zombie: int,
) -> ZombieAnalysisResult:
    df = view.query_buffers_allocs()
    df = df[df["is_allocation"] == 1]
    df = df[df["size"] >= min_size]
    df["zombie"] = df["event_free"] - df["event_last_launch"]
    df = df[df["zombie"] >= min_zombie]
    df["zombie%"] = df["zombie"] / (df["event_free"] - df["event_malloc"])

    result = ZombieAnalysisResult(
        df=df,
        min_size=min_size,
        min_zombie=min_zombie,
    )
    return result
