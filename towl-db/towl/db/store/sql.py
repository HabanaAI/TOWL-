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

class Initialization:
    create_tables = """
        CREATE TABLE meta
            ( version INTEGER
            )
        ;

        CREATE TABLE event_kind
            ( ident INTEGER PRIMARY KEY
            , name TEXT NOT NULL
            )
        ;
        

        CREATE TABLE events 
            ( ident INTEGER PRIMARY KEY
            , timestamp TIME NOT NULL
            , tid INTEGER
            , kind INTEGER NOT NULL
            , reference INTEGER NOT NULL
            , FOREIGN KEY(kind) REFERENCES event_kind(ident)
            )
        ;

        CREATE TABLE data_buffers
            ( ident INTEGER PRIMARY KEY
            , addr INTEGER NOT NULL
            , size INTEGER NOT NULL
            , meta TEXT NOT NULL
            , unknown BOOLEAN NOT NULL
            , event_malloc INTEGER
            , event_free INTEGER
            , event_first_launch INTEGER
            , event_last_launch INTEGER
            )
        ;

        CREATE TABLE events_devmem_buf
            ( ident INTEGER PRIMARY KEY
            , buffer_ident INTEGER NOT NULL
            , is_allocation BOOLEAN NOT NULL
            , FOREIGN KEY(buffer_ident) REFERENCES data_buffers(ident)
            )
        ;

        CREATE TABLE events_devmem_summary
            ( ident INTEGER PRIMARY KEY
            , used INTEGER NOT NULL
            , workspace INTEGER NOT NULL
            , persistent INTEGER NOT NULL
            , tag TEXT NOT NULL
            )
        ;

        CREATE TABLE data_launches
            ( ident INTEGER PRIMARY KEY
            , workspace INTEGER NOT NULL
            , handle INTEGER NOT NULL
            , recipe_name TEXT NOT NULL
            , meta TEXT NOT NULL
            , event_launch INTEGER
            , event_finished INTEGER
            )
        ;

        CREATE TABLE data_launches_bufs
            ( launch_ident INTEGER NOT NULL
            , buffer_ident INTEGER NOT NULL
            , [index] INTEGER NOT NULL
            , offset INTEGER NOT NULL
            , synapse_name TEXT
            , FOREIGN KEY (launch_ident) REFERENCES data_launches(ident)
            , FOREIGN KEY (buffer_ident) REFERENCES data_buffers(ident)
            )
        ;

        CREATE TABLE events_recipe_launch
            ( ident INTEGER PRIMARY KEY
            , launch_ident INTEGER NOT NULL
            , FOREIGN KEY (launch_ident) REFERENCES data_launches(ident)
            )
        ;

        CREATE TABLE events_pythonlog
            ( ident INTEGER PRIMARY KEY
            , command TEXT
            , message TEXT
            , funcname TEXT
            , filename TEXT
            , lineno INT
            , content TEXT
            , mark_id INT
            )
        ;
    """

    create_views = """
        CREATE VIEW view_launches AS
        SELECT events.ident AS event_ident, data_launches.*
        FROM events
        INNER JOIN data_launches
            ON events.reference = data_launches.ident
            AND events.kind = 2
        ORDER BY event_ident
        ;

        CREATE VIEW view_pythonlog AS
        SELECT events.ident AS event_ident, events_pythonlog.*
        FROM events
        INNER JOIN events_pythonlog
            ON events.reference = events_pythonlog.ident
            AND events.kind = 4
        ORDER BY event_ident
        ;

        CREATE VIEW view_devmem_summary AS
        SELECT events.ident as event_ident, events_devmem_summary.*
        FROM events
        INNER JOIN events_devmem_summary
            ON events.reference = events_devmem_summary.ident
            AND events.kind = 1
        ORDER BY event_ident
        ;

        CREATE VIEW view_devmem_buf AS
        SELECT events.ident as event_ident, events_devmem_buf.is_allocation, data_buffers.*
        FROM events
        INNER JOIN events_devmem_buf
            ON events.reference = events_devmem_buf.ident
            AND events.kind = 0
        INNER JOIN data_buffers
            ON data_buffers.ident == events_devmem_buf.buffer_ident
        ORDER BY event_ident
        ;

        CREATE VIEW view_launches_bufs AS
        SELECT 
            data_launches_bufs.launch_ident,
            data_launches_bufs.offset,
            data_launches_bufs.[index],
            data_launches_bufs.synapse_name,
            data_buffers.ident,
            data_buffers.addr, data_buffers.size,
            data_buffers.unknown, data_buffers.meta,
            data_buffers.event_malloc, data_buffers.event_free,
            data_buffers.event_first_launch, data_buffers.event_last_launch
        FROM
            data_launches_bufs
        INNER JOIN data_buffers
            ON data_buffers.ident = data_launches_bufs.buffer_ident
        ORDER BY [index]
        ;

        CREATE VIEW view_events AS
        SELECT
            events.ident as event_ident,
            events.tid,
            events.timestamp,
            event_kind.name
        FROM
            events
        INNER JOIN event_kind
            ON events.kind = event_kind.ident
        ORDER BY events.ident
        ;
    """

    insert_version = """
        INSERT INTO meta
            (version)
        VALUES
            (20240206)
        ;
    """

    insert_enums = """
        INSERT INTO event_kind
            (ident, name)
        VALUES
            (0, 'devmem_buf'),
            (1, 'devmem_summary'),
            (2, 'recipe_launch'),
            (3, 'recipe_finished'),
            (4, 'python')
        ;
    """

    cleanup = """
        VACUUM;
        PRAGMA vacuum;
        PRAGMA optimize;
    """


class Opening:
    read_version = """
        SELECT version from meta
    """

    xconfigure = """
        PRAGMA foreign_keys = ON;
        PRAGMA synchronous = OFF;
        PRAGMA journal_mode = OFF;
    """

    configure = """
        PRAGMA foreign_keys = ON;
    """

    count_events = """
        SELECT COUNT(*) from events
    """


class EventsInserting:
    insert_devmem_summary = """
        INSERT INTO events_devmem_summary
            (ident, used, workspace, persistent, tag)
        VALUES
            (:ident, :used, :workspace, :persistent, :tag)
    """

    insert_devmem_buf = """
        INSERT INTO events_devmem_buf
            (ident, buffer_ident, is_allocation)
        VALUES
            (:ident, :buffer_ident, :is_allocation)
    """

    insert_event = """
        INSERT INTO events
            (ident, timestamp, tid, kind, reference)
        VALUES
            (:ident, :timestamp, :tid, :kind, :reference)
    """


class Buffers:
    insert_buffer = """
        INSERT INTO data_buffers
            (ident, addr, size, event_malloc, event_free, event_first_launch, event_last_launch, unknown, meta)
        VALUES
            (:ident, :addr, :size, :event_malloc, :event_free, :event_first_launch, :event_last_launch, :unknown, :meta)
    """

    query_buffers = """
        SELECT ident, addr, size, meta, unknown, event_malloc, event_free, event_first_launch, event_last_launch FROM data_buffers
    """

    update_buffer_events = """
        UPDATE data_buffers
        SET event_malloc = :event_malloc, event_free = :event_free, event_first_launch = :event_first_launch, event_last_launch = :event_last_launch
        WHERE ident = :ident
    """

    update_buffer_meta = """
        UPDATE data_buffers
        SET meta = :meta
        WHERE ident = :ident
    """


class Launches:
    insert_launch = """
        INSERT INTO data_launches
            (ident, workspace, handle, meta, recipe_name, event_launch, event_finished)
        VALUES
            (:ident, :workspace, :handle, :meta, :recipe_name, :event_launch, :event_finished)
    """

    insert_launch_buf = """
        INSERT INTO data_launches_bufs
            (launch_ident, buffer_ident, [index], offset, synapse_name)
        VALUES
            (?, ?, ?, ?, ?)
    """

    update_launch_events = """
        UPDATE data_launches
        SET event_launch = :event_launch, event_finished = :event_finished
        WHERE ident = :ident
    """

    query_launch_by_launch_id = """
        SELECT event_ident, ident, workspace, handle, recipe_name, meta, event_launch, event_finished FROM view_launches
        WHERE :launch_ident = ident
        LIMIT 1
    """

    query_launch_by_event_id = """
        SELECT event_ident, ident, workspace, handle, recipe_name, meta, event_launch, event_finished FROM view_launches
        WHERE :event_ident = event_ident
        LIMIT 1
    """

    query_launch_bufs_by_launch_id = """
        SELECT 
            launch_ident,
            offset, [index], synapse_name,
            ident, addr, size, meta,
            event_malloc, event_free,
            event_first_launch, event_last_launch
        FROM view_launches_bufs
        WHERE launch_ident = :launch_ident
    """


class Python:
    insert_python = """
        INSERT INTO events_pythonlog
            (ident, command, message, funcname, filename, lineno, content, mark_id)
        VALUES
            (:ident, :command, :message, :funcname, :filename, :lineno, :content, :mark_id)
        ;
    """

    query_python_log = """
        SELECT event_ident, command, message, funcname, filename, lineno, content, mark_id
        FROM view_pythonlog
        WHERE :begin <= event_ident AND event_ident < :end
        ORDER BY event_ident
    """

    query_python_log_by_mark_id = """
        SELECT event_ident, command, message, funcname, filename, lineno, content, mark_id
        FROM view_pythonlog
        WHERE :mark_id == mark_id
        ORDER BY event_ident
    """


class Query:
    query_events = """
        SELECT * FROM view_events
        WHERE :begin <= event_ident AND event_ident < :end
        ORDER BY event_ident
    """

    query_devmem_summary = """
        SELECT event_ident, used, workspace, persistent, tag FROM view_devmem_summary
        WHERE :begin <= event_ident AND event_ident < :end
        ORDER BY event_ident
    """

    query_devmem_summary_tag = """
        SELECT event_ident, used, workspace, persistent, tag FROM view_devmem_summary
        WHERE :begin <= event_ident AND event_ident < :end AND tag = :tag
        ORDER BY event_ident
    """

    query_launches = """
        SELECT event_ident, ident, workspace, handle, event_launch, event_finished, recipe_name FROM view_launches
        WHERE :begin <= event_ident AND event_ident < :end
        ORDER BY event_ident
    """

    query_devmem_bufs = """
        SELECT event_ident, is_allocation, ident, addr, size, 
            event_malloc, event_free, event_first_launch, event_last_launch,
            unknown FROM view_devmem_buf
        WHERE :begin <= event_ident AND event_ident < :end
    """

    query_devmem_bufs_full = """
        SELECT event_ident, is_allocation, ident, addr, size, event_malloc, event_free, event_first_launch, event_last_launch, meta, unknown FROM view_devmem_buf
        WHERE :begin <= event_ident AND event_ident < :end
        ORDER BY event_ident
    """
