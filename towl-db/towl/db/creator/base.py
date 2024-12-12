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

from towl.db.events import read_events_file, Event, EventKind
from towl.db.store import Database
import os
import shutil
from .devmem_reactor import DevMemReactor
from .recipe_reactor import RecipeReactor
from .event_writer import EventWriter
from .devmem_manager import DevMemManager
from .recipe_manager import RecipeManager
from .python_reactor import PythonReactor


class Creator:
    def __init__(self, output_path: str, copy: bool):
        self._output_path = output_path
        if os.path.exists(output_path):
            raise RuntimeError(f"Already exist: {output_path}")
        os.makedirs(output_path)
        self._db = Database.create(os.path.join(output_path, "towl.db"))
        self._copy_logs = copy

        self._event_writer = EventWriter(self._db)
        self._devmem_manager = DevMemManager(
            self._db,
            self._event_writer,
        )
        self._recipe_manager = RecipeManager(
            self._db,
            self._event_writer,
            self._devmem_manager,
        )
        self._devmem_reactor = DevMemReactor(
            self._devmem_manager,
        )
        self._recipe_reactor = RecipeReactor(
            self._devmem_manager,
            self._recipe_manager,
        )
        self._python_reactor = PythonReactor(
            self._db,
            self._devmem_manager,
            self._event_writer,
        )

        self._dispatch = {
            EventKind.DEVMEM_MALLOC: self._devmem_reactor.react_malloc,
            EventKind.DEVMEM_FREE: self._devmem_reactor.react_free,
            EventKind.DEVMEM_SUMMARY: self._devmem_reactor.react_summary,
            EventKind.RECIPE_LAUNCH: self._recipe_reactor.react_launch,
            EventKind.RECIPE_LAUNCH_BUF: self._recipe_reactor.react_launch_buf,
            EventKind.RECIPE_FINISHED: self._recipe_reactor.react_finished,
            EventKind.PYTHON_GENERIC: self._python_reactor.react_python_generic,
            EventKind.PYTHON_TOWLCMD: self._python_reactor.react_python_towlcmd,
        }

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        print("Finishing")
        self._devmem_manager.finish()
        self._db.close()

    def read_file(self, path):
        COMMIT_EVERY_N_STEPS = 100  # 0000
        for i, event in enumerate(read_events_file(path)):
            self._react(event)
            if i % COMMIT_EVERY_N_STEPS == 0:
                # print("commit")
                self._db.commit()
        self._db.commit()

    def _react(self, event: Event):
        handler = self._dispatch.get(event.kind, None)
        if handler is None:
            raise RuntimeError(f"Unsupported event: {event}")
        handler(event)

    @staticmethod
    def make(path, *, overwrite: bool, copy: bool) -> "Creator":
        if overwrite:
            if os.path.exists(path):
                shutil.rmtree(path)

        return Creator(path, copy=copy)


def create_from_log_file(
    path: str,
    output: str,
    *,
    overwrite: bool = False,
    do_nothing_if_exists: bool = False,
):
    """
    Create database
    """
    if os.path.exists(output) and do_nothing_if_exists:
        return
    with Creator.make(output, overwrite=overwrite, copy=True) as cr:
        cr.read_file(path)
