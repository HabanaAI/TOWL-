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

import pandas as pd
import itables
from ..data.scenario_view import ScenarioView
from ..data.timerange import EventTimeRange
import matplotlib.pyplot as plt
from typing import TypedDict
from contextlib import nullcontext


class _GLOBALS:
    matplotlib = []

    @classmethod
    def has_matplotlib(self):
        return len(self.matplotlib) > 0

    @classmethod
    def get_matplotlib(self):
        if self.has_matplotlib():
            return self.matplotlib[-1]
        return None


def _call_optional(f, x):
    if x is not None:
        f(x)


class MatplotLib:
    def __init__(
        self,
        *,
        enable=True,
        suptitle=None,
        xlabel=None,
        ylabel=None,
        ylim=None,
        title=None,
    ):
        self._enable = enable
        self._suptitle = suptitle
        self._xlabel = xlabel
        self._ylabel = ylabel
        self._ylim = ylim
        self._title = title

    def __enter__(self):
        if not self._enable:
            return
        plt.clf()
        plt.figure()
        _GLOBALS.matplotlib.append(self)

    def __exit__(self, *args):
        if not self._enable:
            return
        _call_optional(plt.suptitle, self._suptitle)
        _call_optional(plt.xlabel, self._xlabel)
        _call_optional(plt.ylabel, self._ylabel)
        _call_optional(plt.ylim, self._ylim)
        _call_optional(plt.title, self._title)
        plt.tight_layout()
        plt.show()
        _GLOBALS.matplotlib.pop()

    def _offer(
        self,
        suptitle=None,
        xlabel=None,
        ylabel=None,
        ylim=None,
        title=None,
    ):
        if self._suptitle is None:
            self._suptitle = suptitle
        if self._title is None:
            self._title = title
        if self._xlabel is None:
            self._xlabel = xlabel
        if self._ylabel is None:
            self._ylabel = ylabel
        if self._ylim is None:
            self._ylim = ylim


def MatplotLibNested(**kwargs):
    ctx = _GLOBALS.get_matplotlib()
    if ctx is None:
        return MatplotLib(**kwargs)
    ctx._offer(**kwargs)
    return nullcontext()


class MemoryUsageColors(TypedDict):
    workspace: str
    persistent: str
    used: str


_default_memory_usage_colors = {
    "workspace": "red",
    "persistent": "blue",
    "used": "black",
}


def _fill_memory_usage_colors(d):
    r = dict(d)
    for key in _default_memory_usage_colors.keys():
        if key not in r:
            r[key] = _default_memory_usage_colors[key]
    return r


def select_ylim(scenario_view: ScenarioView):
    df = scenario_view.query_memory_usage()
    x = df["used"].max() / 1024**3

    if x < 32:
        return (0, 32)
    if x < 100:
        return (0, 100)
    if x < 130:
        return (0, 130)
    return (0, x + 1)


def plot_memory_usage(
    scenario_view: ScenarioView,
    *,
    persistent=True,
    workspace=True,
    used=True,
    tag=None,
    colors=None,
    legend_prefix=None,
):
    """
    Plots memory usage from given `scenario_view`.

    * `persistent` - controls if persistent memory should be drawn
    * `workspace` - controls if workspace memory should be drawn
    * `used` - controls if used memory should be drawn
    """
    title = f"Memory usage {scenario_view.event_timerange}"
    ylim = select_ylim(scenario_view)
    with MatplotLibNested(
        title=title,
        xlabel="Events",
        ylabel="Memory (GiB)",
        ylim=ylim,
    ):
        if colors is None:
            colors = _default_memory_usage_colors
        if legend_prefix is None:
            legend_prefix = ""
        colors = _fill_memory_usage_colors(colors)

        df = scenario_view.query_memory_usage(tag=tag)
        if persistent:
            plt.plot(
                df.index,
                df["persistent"] / 1024**3,
                label=f"{legend_prefix} persistent",
                color=colors["persistent"],
            )
        if workspace:
            plt.plot(
                df.index,
                df["workspace"] / 1024**3,
                label=f"{legend_prefix} workspace",
                color=colors["workspace"],
            )
        if used:
            plt.plot(
                df.index,
                df["used"] / 1024**3,
                label=f"{legend_prefix} used",
                color=colors["used"],
            )
        plt.legend()


def plot_vlines(timerange: EventTimeRange):
    plt.axvline(timerange.begin)
    plt.axvline(timerange.end)


def plot_shadow(timerange: EventTimeRange, *, alpha=0.8, color="yellow"):
    """
    Plots box for given event time range `timerange` interval.

    Useful for marking hills/functions/blocks on the memory usage plot.
    """
    plt.axvspan(timerange.begin, timerange.end, alpha=alpha, facecolor=color)
