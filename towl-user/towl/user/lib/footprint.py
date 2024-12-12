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

from typing import NamedTuple, Optional
import pandas as pd
from towl.user.utils.strings import memory_str
from towl.user.data import ScenarioView


class MemoryFootprint(NamedTuple):
    title: str
    max_memory: int
    avg_memory: int
    bottom_memory: int
    max_workspace: Optional[int]

    def show(self):
        print(">>", self.title)
        print("Max memory:", memory_str(self.max_memory))
        print("Avg memory:", memory_str(self.avg_memory))
        print("Bot memory:", memory_str(self.bottom_memory))
        if self.max_workspace is not None:
            print("Max workspace", memory_str(self.max_workspace))
            if self.max_memory > 0:
                print(">>", self.title, "minus max workspace")
                print(
                    "Max memory:",
                    memory_str(self.max_memory - self.max_workspace),
                )
                print(
                    "Avg memory:",
                    memory_str(self.avg_memory - self.max_workspace),
                )
                print(
                    "Bot memory:",
                    memory_str(self.bottom_memory - self.max_workspace),
                )

    @staticmethod
    def from_pdserie(title: str, serie: pd.Series):
        return MemoryFootprint(
            title=title,
            max_memory=serie.max(),
            avg_memory=serie.mean(),
            bottom_memory=serie[1000:].min(),
            max_workspace=None,
        )

    @staticmethod
    def from_view(title: str, view: ScenarioView):
        usage_df = view.query_memory_usage()
        max_workspace = usage_df["workspace"].max()
        return MemoryFootprint(
            title=title,
            max_memory=usage_df["used"].max(),
            avg_memory=usage_df["used"].mean(),
            bottom_memory=usage_df["used"][1000:].min(),
            max_workspace=max_workspace,
        )


def global_mem_usage(global_view):
    usage_df = global_view.query_memory_usage()
    max_workspace = usage_df["workspace"].max()
    bot_usage = usage_df["used"][1000:].min()
    print("Max memory", memory_str(usage_df["used"].max()))
    print("Max worksp", memory_str(max_workspace))
    print("Avg memory", memory_str(usage_df["used"].mean()))
    print(
        "Bot memory:",
        memory_str(bot_usage),
        "without workspace:",
        memory_str(bot_usage - max_workspace),
    )
