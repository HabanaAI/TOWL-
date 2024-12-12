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

from towl.db.events import (
    Event_RecipeLaunch,
    Event_RecipeLaunchBuf,
    Event_RecipeFinished,
)
from typing import Optional, List
from .devmem_manager import DevMemManager
from .recipe_manager import RecipeManager
from towl.db.store import model
import logging


class RecipeCollector:
    def __init__(self, event: Event_RecipeLaunch):
        self._launch_event = event
        self._launch_buf_events: List[Event_RecipeLaunchBuf] = []
        self._missing_buffers = event.nbuffers

    def push_buffer(self, event: Event_RecipeLaunchBuf):
        self._missing_buffers -= 1
        self._launch_buf_events.append(event)
        return self._missing_buffers == 0

    def finish(self):
        return self._launch_event, self._launch_buf_events


class RecipeReactor:
    def __init__(self, devmem_manager: DevMemManager, recipe_manager: RecipeManager):
        self._devmem_manager = devmem_manager
        self._recipe_manager = recipe_manager
        self._collector: Optional[RecipeCollector] = None

    def react_launch(self, event: Event_RecipeLaunch):
        self._start_collector(event)

    def react_launch_buf(self, event: Event_RecipeLaunchBuf):
        if self._collector is None:
            logging.warn("Unstarted recipe processing")
            return

        is_finished = self._collector.push_buffer(event)
        if is_finished:
            events = self._collector.finish()
            self._collector = None
            self._publish_launch(*events)

    def react_finished(self, event: Event_RecipeFinished):
        self._recipe_manager.finish_launch(
            event.timestamp,
            event.tid,
            event.handle,
        )

    def _start_collector(self, event: Event_RecipeLaunch):
        if self._collector is not None:
            logging.warn("Unfinished recipe processing")

        self._collector = RecipeCollector(event)

    def _publish_launch(
        self,
        launch_event: Event_RecipeLaunch,
        launch_bufs_events: List[Event_RecipeLaunchBuf],
    ):

        launch_buffers = []
        buffers = []
        for event in launch_bufs_events:
            buffer = self._devmem_manager.get_buffer_by_addr(event.handle_addr)
            buffers.append(buffer)
            offset = event.handle_addr - buffer.addr
            launch_buffer = model.DataRecipeLaunchBuffer(
                buffer=buffer.ident,
                index=event.index,
                synapse_name=event.synapse_name,
                offset=offset,
            )
            launch_buffers.append(launch_buffer)

        self._recipe_manager.publish_launch(
            timestamp=launch_event.timestamp,
            tid=launch_event.tid,
            handle=launch_event.handle,
            recipe_name=launch_event.name,
            launch_buffers=launch_buffers,
            workspace=launch_event.workspace_size,
            buffers=buffers,
        )
