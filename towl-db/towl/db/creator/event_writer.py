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

from .primary_key_generator import PrimaryKeyGenerator
from towl.db.utils.typechecked import typechecked
from datetime import datetime
import towl.db.store.model as model
from towl.db.store import Database


@typechecked
class EventWriter:
    def __init__(self, db: Database):
        self._primary_key_generator = PrimaryKeyGenerator()
        self._db = db

    def add(self, timestamp: datetime, tid: int, kind: model.EventKind, reference: int):
        entity = model.Event(
            ident=self._primary_key_generator(),
            kind=kind,
            reference=reference,
            timestamp=timestamp,
            tid=tid,
        )

        self._db.insert_event(entity)

        return entity
