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

from towl.user.data import Scenario
import json


def decode_framelog(scenario: Scenario, event_index: int):
    df = scenario.make_global_view()._query_python_log_full()
    row = df.loc[event_index]
    content = row["content"]
    data = json.loads(content)

    for frame in data["stack"]:
        print("=====>", frame["frame"]["funcname"])
        for k, v in frame["memory"].items():
            print(k, f"BUF_{v}")
