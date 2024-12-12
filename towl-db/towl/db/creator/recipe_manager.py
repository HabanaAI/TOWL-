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

import towl.db.store.model as model
from towl.db.store import Database
import logging
from typing import Dict, List
from .primary_key_generator import PrimaryKeyGenerator
from towl.db.utils.typechecked import typechecked
from .event_writer import EventWriter
from datetime import datetime
from .devmem_manager import DevMemManager


@typechecked
class RecipeManager:
    def __init__(
        self, db: Database, event_writer: EventWriter, devmem_manager: DevMemManager
    ):
        self._live_buffers: Dict[int, model.DataBuffer] = {}
        self._event_writer = event_writer
        self._db = db
        self._get_launch_primary_key = PrimaryKeyGenerator()
        self._launched_recipes: List[model.DataRecipeLaunch] = []
        self._devmem_manager = devmem_manager

    def publish_launch(
        self,
        timestamp: datetime,
        tid: int,
        *,
        handle: int,
        workspace: int,
        recipe_name: str,
        launch_buffers: List[model.DataRecipeLaunchBuffer],
        buffers: List[model.DataBuffer],
    ):
        entity = model.DataRecipeLaunch(
            ident=self._get_launch_primary_key(),
            handle=handle,
            workspace=workspace,
            buffers=launch_buffers,
            meta=model.DataRecipeLaunchMeta(),
            event_launch=None,
            event_finished=None,
            recipe_name=recipe_name,
        )

        self._db.insert_data_launch(entity)

        event_entity = self._event_writer.add(
            timestamp,
            tid,
            model.EventKind.RECIPE_LAUNCH,
            entity.ident,
        )

        entity.event_launch = event_entity.ident
        self._db.update_launch_events(entity)
        self._launched_recipes.append(entity)

        for buffer in buffers:
            buffer.event_last_launch = event_entity.ident
            if buffer.event_first_launch is None:
                buffer.event_first_launch = event_entity.ident
            self._devmem_manager.update_buffer_events(buffer)

    def finish_launch(
        self,
        timestamp: datetime,
        tid: int,
        handle: int,
    ):
        if len(self._launched_recipes) == 0:
            logging.error(
                "Finished unknown recipe 0x{handle:x}: no recorder launch")
            return

        if self._launched_recipes[0].handle != handle:
            logging.error(
                "Finished unknown recipe 0x{handle:x}: invalid order?")
            return

        launch_entity = self._launched_recipes.pop(0)

        event_entity = self._event_writer.add(
            timestamp,
            tid,
            model.EventKind.RECIPE_FINISHED,
            launch_entity.ident,
        )

        launch_entity.event_finished = event_entity.ident
        self._db.update_launch_events(launch_entity)
