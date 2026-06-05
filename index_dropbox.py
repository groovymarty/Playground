import os
import sqlite3
from datetime import datetime, timezone

import mydbx
from dropbox.files import FileMetadata, FolderMetadata, DeletedMetadata


DB_FILE = "dropbox_file_index.sqlite"


def init_db(db_path=DB_FILE):
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dropbox_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_hash TEXT NOT NULL,
            size INTEGER NOT NULL,
            path_lower TEXT NOT NULL UNIQUE,
            path_display TEXT,
            name TEXT,
            client_modified TEXT,
            server_modified TEXT,
            rev TEXT,
            indexed_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_hash_size
        ON dropbox_files (content_hash, size)
    """)
    conn.commit()
    return conn


def upsert_file(conn, entry: FileMetadata):
    now = datetime.now(timezone.utc).isoformat()

    conn.execute("""
        INSERT INTO dropbox_files (
            content_hash,
            size,
            path_lower,
            path_display,
            name,
            client_modified,
            server_modified,
            rev,
            indexed_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(path_lower) DO UPDATE SET
            content_hash = excluded.content_hash,
            size = excluded.size,
            path_display = excluded.path_display,
            name = excluded.name,
            client_modified = excluded.client_modified,
            server_modified = excluded.server_modified,
            rev = excluded.rev,
            indexed_at = excluded.indexed_at
    """, (
        entry.content_hash,
        entry.size,
        entry.path_lower,
        entry.path_display,
        entry.name,
        entry.client_modified.isoformat() if entry.client_modified else None,
        entry.server_modified.isoformat() if entry.server_modified else None,
        entry.rev,
        now,
    ))


def index_dropbox_folder(dbx, conn, dropbox_path=""):
    print(f"Scanning Dropbox folder: {dropbox_path or '/'}")

    result = dbx.files_list_folder(
        dropbox_path,
        recursive=True,
        include_deleted=False
    )

    file_count = 0
    folder_count = 0
    skipped_count = 0

    while True:
        for entry in result.entries:
            if isinstance(entry, FileMetadata):
                # Some Dropbox-native/export-only items may not have content_hash.
                if entry.content_hash:
                    upsert_file(conn, entry)
                    file_count += 1
                    if file_count % 1000 == 0:
                        conn.commit()
                        print(f"Indexed {file_count:,} files...")
                else:
                    skipped_count += 1

            elif isinstance(entry, FolderMetadata):
                folder_count += 1

            elif isinstance(entry, DeletedMetadata):
                pass

        conn.commit()

        if not result.has_more:
            break

        result = dbx.files_list_folder_continue(result.cursor)

    print()
    print(f"Done.")
    print(f"Files indexed:   {file_count:,}")
    print(f"Folders seen:    {folder_count:,}")
    print(f"Files skipped:   {skipped_count:,}")


def main():
    conn = init_db(DB_FILE)

    # Empty string means Dropbox root.
    index_dropbox_folder(mydbx.get_dropbox(), conn, "")

    conn.close()
    print(f"Database written to: {DB_FILE}")


if __name__ == "__main__":
    main()