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
from typing import Optional


@main_cli.group(name="create")
def cli_create():
    """
    Database creation
    """


@click.argument("path")
@click.option("--output", "-o", help="output directory")
@click.option("--overwrite/--no-overwrite", "-f/-F", help="overwrite output directory")
@click.option("--copy/--no-copy", "-c/-C", help="copy input log file")
@click.option("--title", help="extra title", type=str)
@cli_create.command()
def from_log_file(path, output, overwrite, copy, title: Optional[str]):
    """
    Create database from towl_log file.
    """
    from towl.db.creator import Creator

    with Creator.make(output, overwrite=overwrite, copy=copy) as cr:
        cr.read_file(path)


@click.argument("path")
@click.option("--output", "-o", help="output directory")
@click.option("--overwrite/--no-overwrite", "-f/-F", help="overwrite output directory")
@click.option("--copy/--no-copy", "-c/-C", help="copy input log file")
def from_log_dir(path, output, overwrite, copy):
    """
    Create database from towl_log file from given directory
    """
    raise NotImplemented()


@click.option("--output", "-o", help="output directory")
@click.option("--overwrite/--no-overwrite", "-f/-F", help="overwrite output directory")
@click.option("--copy/--no-copy", "-c/-C", help="copy input log file")
def from_habana_logs(output, overwrite, copy):
    """
    Create database from towl_log file from ${HABANA_LOGS} directory
    """
    raise NotImplemented()


@click.option("--output", "-o", help="output directory")
@click.option("--overwrite/--no-overwrite", "-f/-F", help="overwrite output directory")
def from_cudamemviz(output, overwrite, copy):
    """
    Create database from cudamemviz Snapshot pickled file
    """
    raise NotImplemented()
