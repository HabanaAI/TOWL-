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

from typing import TypedDict, Any, Union, Literal, List, NamedTuple, Any
from dataclasses import dataclass
import json
import enum


class TowlLogCommand(TypedDict):
    command: str
    payload: Any


def emit_towl_command(command: str, payload: Any):
    import habana_frameworks.torch as ht

    msg = TowlLogCommand(command=command, payload=payload)
    text = json.dumps(msg)

    ht.utils.debug._towl_print(f"TOWL-CMD:  {text}")
