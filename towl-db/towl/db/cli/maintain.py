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

from .main_cli import main_cli
import rich_click as click
import sys


@main_cli.group(name="maintain")
def cli_maintain():
    """
    Database maintanence
    """


@click.argument("path", default=".")
@cli_maintain.command()
def recreate(path):
    """
    # Recreate the database

    Useful when towl is getting updated. Works only if you have copy
    of original log inside output directory (see option --copy to create commands).

    a
    """
    pass
