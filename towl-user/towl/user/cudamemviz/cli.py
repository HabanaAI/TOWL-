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

from towl.user.cli import main_cli
from . import model
from . import extract
import rich_click as click
from towl.user.utils.file import smart_open
import os
import sys


@main_cli.group(name="cudamemviz")
def memviz_cli():
    pass


@memviz_cli.command()
@click.argument("path")
@click.option("--output", "-o", required=True, help="output file")
@click.option("--device", "-d", help="device index", default=0, type=int)
def to_csv(path: str, output: str, device: int):
    df = extract.extract_memory_usage(path, device)
    df.to_csv(output)


@memviz_cli.command()
@click.argument("path")
@click.option("--output", "-o", required=True, help="output file")
def to_html(path: str, output: str):
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


@memviz_cli.command()
@click.argument("path")
@click.argument("begin", type=int)
@click.argument("end", type=int)
@click.option("--output", "-o", required=True, help="output file")
@click.option("--device", "-d", help="device index", default=0, type=int)
def cut(path: str, output: str, begin: int, end: int, device: int):
    extract.cut_and_dump(path, output, begin, end, device)
