# consolidate_camera_and_message_photos.py
from pathlib import Path
import shutil
import hashlib
from PIL import Image
import pillow_heif

# ------------------------------------------------------------
# CONFIGURE THESE
# ------------------------------------------------------------
PICTURES = Path("D:\\Users\\Msaus\\Pictures")

# Camera-photo consolidation
CAMERA_DEST = PICTURES / "_Scratch"     # my camera photos
CAMERA_SOURCE = PICTURES / "_Scratch3"  # jill's camera photos

# Message-download consolidation
MSG_DEST = PICTURES / "_Scratch2"       # my downloaded message photos
MSG_SOURCE = PICTURES / "_Scratch4"     # jill's downloaded message photos

# Empty these at the end
EMPTY_AT_END = [MSG_SOURCE, CAMERA_SOURCE]

DRY_RUN = False   # First run with True. Change to False after reviewing report.
VERBOSE = True
# ------------------------------------------------------------

HEIC_EXTS = {".heic", ".heif"}


def log(msg):
    if VERBOSE:
        print(msg, flush=True)


def count_files(folder: Path) -> int:
    return sum(1 for p in folder.iterdir() if p.is_file())


def unique_path(dest_folder: Path, filename: str) -> tuple[Path, bool]:
    """
    Return a non-conflicting path in dest_folder.
    If needed, append (1), (2), etc.
    """
    candidate = dest_folder / filename
    if not candidate.exists():
        return candidate, False

    stem = candidate.stem
    suffix = candidate.suffix

    i = 1
    while True:
        candidate = dest_folder / f"{stem} ({i}){suffix}"
        if not candidate.exists():
            return candidate, True
        i += 1


def copy_with_nonconflicting_name(src: Path, dest_folder: Path) -> tuple[Path, bool]:
    dest, renamed = unique_path(dest_folder, src.name)
    if not DRY_RUN:
        shutil.copy2(src, dest)
    return dest, renamed


def convert_heic_to_jpg(path: Path) -> Path:
    """
    Convert HEIC to JPG next to original file, then delete HEIC.
    """
    jpg_path, _ = unique_path(path.parent, path.stem + ".jpg")

    if not DRY_RUN:
        pillow_heif.register_heif_opener()
        img = Image.open(path)
        img = img.convert("RGB")
        img.save(jpg_path, "JPEG", quality=95)

        path.unlink()

    return jpg_path


def content_hash(path: Path) -> tuple[str, str]:
    """
    For readable images, hash decoded pixels.
    For everything else, hash exact file bytes.
    """
    try:
        with Image.open(path) as img:
            img = img.convert("RGB")
            h = hashlib.sha256()
            h.update(b"PIXELS")
            h.update(img.size[0].to_bytes(4, "little"))
            h.update(img.size[1].to_bytes(4, "little"))
            h.update(img.tobytes())
            return ("pixel", h.hexdigest())

    except Exception:
        h = hashlib.sha256()
        h.update(b"BINARY")

        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)

        return ("binary", h.hexdigest())
    

def iter_files(folder: Path):
    for p in folder.iterdir():
        if p.is_file():
            yield p


def convert_all_heic(folder: Path, report: dict):
    for p in list(iter_files(folder)):
        if p.suffix.lower() in HEIC_EXTS:
            log(f"Converting {p.name}...")
            new_path = convert_heic_to_jpg(p)
            report["heic_converted"] += 1
            report["details"].append(f"HEIC converted: {p} -> {new_path}")


def delete_duplicate_files(folders: list[Path], report: dict):
    """
    Delete duplicates across the given folders.

    Images are compared by decoded pixels.
    Non-images are compared by exact file bytes.
    """
    seen = {}

    for folder in folders:
        for p in list(iter_files(folder)):
            if p.suffix.lower() in HEIC_EXTS:
                continue

            try:
                log(f"Hashing {p.name}...")
                key = content_hash(p)
            except Exception as e:
                report["errors"].append(f"Could not hash {p}: {e}")
                continue

            if key in seen:
                log(f"Duplicate: {p.name}")
                report["duplicates_deleted"] += 1
                if folder == MSG_SOURCE:
                    report["msg_source_duplicates_deleted"] += 1
                elif folder == MSG_DEST:
                    report["msg_dest_duplicates_deleted"] += 1                

                report["details"].append(f"Duplicate deleted: {p} duplicate of {seen[key]}")
                if not DRY_RUN:
                    p.unlink()
            else:
                seen[key] = p


def consolidate_camera(report: dict):
    """
    Copy all camera files from CAMERA_SOURCE to CAMERA_DEST.
    Same filename but different photo/movie gets renamed.
    No pixel duplicate checking here.
    """
    CAMERA_DEST.mkdir(parents=True, exist_ok=True)

    for p in iter_files(CAMERA_SOURCE):
        log(f"Copying {p.name}...")
        dest, renamed = copy_with_nonconflicting_name(p, CAMERA_DEST)
        report["camera_files_copied"] += 1
        if renamed:
            log(f"   renamed to {dest.name}")
            report["name_conflicts_renamed"] += 1
        report["details"].append(f"Camera copied: {p} -> {dest}")


def consolidate_messages(report: dict):
    """
    Convert HEICs, delete pixel duplicates, then copy source message photos
    into destination with non-conflicting names.
    """
    MSG_DEST.mkdir(parents=True, exist_ok=True)

    convert_all_heic(MSG_DEST, report)
    convert_all_heic(MSG_SOURCE, report)

    delete_duplicate_files([MSG_DEST, MSG_SOURCE], report)

    for p in list(iter_files(MSG_SOURCE)):
        if p.suffix.lower() in HEIC_EXTS:
            continue

        log(f"Copying {p.name}...")
        dest, renamed = copy_with_nonconflicting_name(p, MSG_DEST)
        report["message_files_copied"] += 1
        if renamed:
            log(f"   renamed to {dest.name}")
            report["name_conflicts_renamed"] += 1
        report["details"].append(f"Message copied: {p} -> {dest}")


def validate_before_cleanup(report: dict):
    camera_remaining = count_files(CAMERA_SOURCE)
    msg_remaining = count_files(MSG_SOURCE)

    expected_camera_remaining = report["camera_source_start_files"]

    expected_msg_remaining = (
        report["msg_source_start_files"]
        - report["msg_source_duplicates_deleted"]
    )

    if camera_remaining != expected_camera_remaining:
        raise RuntimeError(
            f"Camera source accounting failed: "
            f"{camera_remaining} files remain, expected {expected_camera_remaining}"
        )

    if report["camera_files_copied"] != expected_camera_remaining:
        raise RuntimeError(
            f"Camera copy accounting failed: "
            f"{report['camera_files_copied']} copied, expected {expected_camera_remaining}"
        )

    if msg_remaining != expected_msg_remaining:
        raise RuntimeError(
            f"Message source accounting failed: "
            f"{msg_remaining} files remain, expected {expected_msg_remaining}"
        )

    if report["message_files_copied"] != msg_remaining:
        raise RuntimeError(
            f"Message copy accounting failed: "
            f"{report['message_files_copied']} copied, expected {msg_remaining}"
        )
    

def empty_folder(folder: Path, report: dict):
    for p in folder.iterdir():
        if p.is_file():
            report["files_deleted_at_end"] += 1
            report["details"].append(f"Final cleanup delete: {p}")
            if not DRY_RUN:
                p.unlink()


def write_report(report: dict):
    report_path = Path("photo_consolidation_report.txt")

    lines = []
    lines.append("PHOTO CONSOLIDATION REPORT")
    lines.append("==========================")
    lines.append(f"DRY_RUN: {DRY_RUN}")
    lines.append("")
    lines.append(f"Camera files copied:          {report['camera_files_copied']}")
    lines.append(f"Message files copied:         {report['message_files_copied']}")
    lines.append(f"HEIC files converted:         {report['heic_converted']}")
    lines.append(f"Duplicates deleted:           {report['duplicates_deleted']}")
    lines.append(f"Name conflicts renamed:       {report['name_conflicts_renamed']}")
    lines.append(f"Files deleted at final clean: {report['files_deleted_at_end']}")
    lines.append("")
    lines.append("DETAILS")
    lines.append("-------")
    lines.extend(report["details"])

    if report["errors"]:
        lines.append("")
        lines.append("ERRORS")
        lines.append("------")
        lines.extend(report["errors"])

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report written to: {report_path}")


def main():
    report = {
        "camera_source_start_files": 0,
        "msg_source_start_files": 0,
        "msg_source_duplicates_deleted": 0,
        "msg_dest_duplicates_deleted": 0,
        "camera_files_copied": 0,
        "message_files_copied": 0,
        "heic_converted": 0,
        "duplicates_deleted": 0,
        "name_conflicts_renamed": 0,
        "files_deleted_at_end": 0,
        "details": [],
        "errors": [],
    }

    report["camera_source_start_files"] = count_files(CAMERA_SOURCE)
    report["msg_source_start_files"] = count_files(MSG_SOURCE)

    log("=== Consolidating camera files ===")
    consolidate_camera(report)

    log("=== Consolidating message attachments ===")
    consolidate_messages(report)

    if not DRY_RUN:
        log("=== Validating file counts ===")
        validate_before_cleanup(report)

        log("=== Cleaning source folders ===")
        for folder in EMPTY_AT_END:
            empty_folder(folder, report)

    write_report(report)
    log("")
    log("Done.")
    log(f"  Camera files copied:     {report['camera_files_copied']}")
    log(f"  Message files copied:    {report['message_files_copied']}")
    log(f"  HEIC converted:          {report['heic_converted']}")
    log(f"  Duplicates deleted:      {report['duplicates_deleted']}")
    log(f"  Renamed on conflict:     {report['name_conflicts_renamed']}")

    print()
    input("I am finished.  You may close this window.")

if __name__ == "__main__":
    main()
