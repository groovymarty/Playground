import argparse
import hashlib
import os
import sqlite3
from pathlib import Path


DROPBOX_BLOCK_SIZE = 4 * 1024 * 1024  # 4 MB


def dropbox_content_hash(file_path: Path) -> str:
    """
    Compute Dropbox content_hash.

    Dropbox hashes each 4 MB block with SHA-256,
    concatenates those block hashes, then SHA-256 hashes that result.
    """
    block_hashes = []

    with file_path.open("rb") as f:
        while True:
            block = f.read(DROPBOX_BLOCK_SIZE)
            if not block:
                break
            block_hashes.append(hashlib.sha256(block).digest())

    return hashlib.sha256(b"".join(block_hashes)).hexdigest()


def file_is_in_dropbox(conn, content_hash: str, size: int) -> bool:
    row = conn.execute(
        """
        SELECT 1
        FROM dropbox_files
        WHERE content_hash = ?
          AND size = ?
        LIMIT 1
        """,
        (content_hash, size),
    ).fetchone()

    return row is not None


def find_example_dropbox_path(conn, content_hash: str, size: int):
    row = conn.execute(
        """
        SELECT path_display
        FROM dropbox_files
        WHERE content_hash = ?
          AND size = ?
        LIMIT 1
        """,
        (content_hash, size),
    ).fetchone()

    return row[0] if row else None


def get_dropbox_matches(conn, content_hash: str, size: int):
    rows = conn.execute(
        """
        SELECT path_display
        FROM dropbox_files
        WHERE content_hash = ?
          AND size = ?
        ORDER BY
          CASE
            WHEN lower(path_display) LIKE '/pictures/%' THEN 0
            ELSE 1
          END,
          path_display
        """,
        (content_hash, size),
    ).fetchall()

    return [row[0] for row in rows]

def scan_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        filenames.sort()

        folder = Path(dirpath)

        for filename in filenames:
            yield folder / filename


def print_report(cd_root: Path, db_path: Path, show_match_path: bool = False):
    conn = sqlite3.connect(db_path)

    current_folder = None
    total_files = 0
    matched_files = 0
    missing_files = 0
    error_files = 0

    for file_path in scan_files(cd_root):
        try:
            relative_path = file_path.relative_to(cd_root)
            folder = relative_path.parent
            filename = relative_path.name

            if folder != current_folder:
                current_folder = folder
                print()
                if str(folder) == ".":
                    print("/")
                else:
                    print(f"/{folder}")

            size = file_path.stat().st_size
            content_hash = dropbox_content_hash(file_path)

            total_files += 1
            matches = get_dropbox_matches(conn, content_hash, size)

            if matches:
                matched_files += 1

                in_pictures = any(
                    p.lower().startswith("/pictures/")
                    for p in matches
                )

                if in_pictures:
                    notation = f"**dropbox pictures** ({len(matches)} match{'es' if len(matches) != 1 else ''})"
                else:
                    notation = f"**dropbox** ({len(matches)} match{'es' if len(matches) != 1 else ''})"

                if show_match_path:
                    notation += f" -> {matches[0]}"
            else:
                missing_files += 1
                notation = "**NOT FOUND**"

            print(f"    {filename}    {notation}")

        except Exception as e:
            error_files += 1
            print(f"    {file_path.name}    **ERROR** {e}")

    conn.close()

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Scanned files:       {total_files}")
    print(f"Found in Dropbox:    {matched_files}")
    print(f"Not found:           {missing_files}")
    print(f"Errors:              {error_files}")


def main():
    parser = argparse.ArgumentParser(
        description="Scan CD/DVD/files and compare each file to Dropbox hash index."
    )

    parser.add_argument(
        "cd_root",
        help="Root folder or drive to scan, such as D:\\ or E:\\",
    )

    parser.add_argument(
        "--db",
        default="dropbox_file_index.sqlite",
        help="SQLite database file created by Dropbox index script.",
    )

    parser.add_argument(
        "--show-match-path",
        action="store_true",
        help="Show one Dropbox path where each matching file was found.",
    )

    args = parser.parse_args()

    cd_root = Path(args.cd_root)
    db_path = Path(args.db)

    if not cd_root.exists():
        raise SystemExit(f"CD/root path does not exist: {cd_root}")

    if not db_path.exists():
        raise SystemExit(f"Database file does not exist: {db_path}")

    print_report(
        cd_root=cd_root,
        db_path=db_path,
        show_match_path=args.show_match_path,
    )


if __name__ == "__main__":
    main()