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

from .main import main_cli
from towl.user.data import Scenario, ScenarioView
import rich_click as click


@main_cli.group(name="plot")
def plot_cli():
    pass


@plot_cli.command()
@click.argument('path', default='.')
@click.option('--output', '-o', required=True, help="output html")
def cudamemviz(path: str, output: str):
    scenario = Scenario(path)
    scenario_view = scenario.make_global_view()
    from towl.user.lib import dump_cudamemviz
    dump_cudamemviz(scenario_view, '/tmp/cudamemviz.pickle', output)
