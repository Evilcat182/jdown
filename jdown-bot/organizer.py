from pathlib import Path
import os
import shutil
import fnmatch
from guessit import guessit
from plex import plex_scan_library
from settings import DEBUG
import state

PREFIX = "[Organizer]"
VIDEO_EXTENSIONS = {".mkv", ".mp4", ".avi", ".m4v", ".mov", ".wmv"}
MEDIA_CONFIDENCE_FIELDS = {"screen_size", "source", "video_codec", "audio_codec"}
MOVIE_DESTINATION = os.getenv("MOVIE_DESTINATION", "/output/done")
SERIES_DESTINATION = os.getenv("SERIES_DESTINATION", "/output/done")
DELETE_SOURCE = os.getenv("DELETE_SOURCE", "0") == "1"


excludes = [
    {
        "Pattern": "*.nfo",
        "Dir": False,
        "CS": False
    },
    {
        "Pattern": "*.jpg",
        "Dir": False,
        "CS": False
    },
    {
        "Pattern": "*.txt",
        "Dir": False,
        "CS": False
    },
    {
        "Pattern": "*.url",
        "Dir": False,
        "CS": False
    },
    {
        "Pattern": "proof",
        "Dir": True,
        "CS": False
    },
    {
        "Pattern": "sample",
        "Dir": True,
        "CS": False
    }
]


def _get_excluded(path: str, settings: list = excludes) -> set:
    """Return a set of paths to exclude from copying based on cleanup settings."""
    excluded = set()
    root = Path(path)
    for rule in settings:
        pattern = rule["Pattern"]
        match_dirs = rule["Dir"]
        case_sensitive = rule["CS"]
        for entry in sorted(root.rglob("*")):
            cmp_name = entry.name if case_sensitive else entry.name.lower()
            cmp_pattern = pattern if case_sensitive else pattern.lower()
            if not fnmatch.fnmatch(cmp_name, cmp_pattern):
                continue
            if entry.is_dir() != match_dirs:
                continue
            excluded.add(entry)
            if DEBUG:
                print(f"{PREFIX} Excluding '{entry}' from copy")
    return excluded


def _is_excluded(path: Path, excluded: set) -> bool:
    return path in excluded or any(p in excluded for p in path.parents)


def _find_videos(path: Path, excluded: set = None) -> list[Path]:
    result = []
    for f in path.rglob("*"):
        if not f.is_file() or f.suffix.lower() not in VIDEO_EXTENSIONS:
            continue
        if excluded and _is_excluded(f, excluded):
            continue
        result.append(f)
    return result


def _files_differ(src: Path, dst: Path) -> bool:
    """Compare by size and modification time only (no content read)."""
    ss = src.stat()
    ds = dst.stat()
    return ss.st_size != ds.st_size or ss.st_mtime > ds.st_mtime


def _safe_copy(src: Path, dst: Path) -> bool:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        if not _files_differ(src, dst):
            if DEBUG:
                print(f"{PREFIX} '{dst.name}' is up to date, skipping")
            return False
        label = " (updated)"
    else:
        label = ""
    shutil.copy2(str(src), str(dst))
    print(f"{PREFIX} '{src.name}' -> '{dst}'{label}")
    return True


def _resolve_content_root(src: Path) -> Path:
    """If src contains only a single subdirectory and no direct files, return that subdirectory."""
    entries = list(src.iterdir())
    if len(entries) == 1 and entries[0].is_dir():
        return entries[0]
    return src


def _copy_extras(src: Path, out_dir: Path, excluded: set = None):
    """Copy all non-video files that are not excluded, preserving relative paths."""
    for f in src.rglob("*"):
        if not f.is_file():
            continue
        if f.suffix.lower() in VIDEO_EXTENSIONS:
            continue
        if excluded and _is_excluded(f, excluded):
            continue
        _safe_copy(f, out_dir / f.relative_to(src))


def _organize_movie(src: Path, dest: Path, info: dict, excluded: set = None) -> bool:
    title = info.get("title", src.name)
    year = info.get("year")
    screen_size = info.get("screen_size")

    folder_name = f"{title} ({year})" if year else title
    out_dir = dest / folder_name

    moved = False
    for video in _find_videos(src, excluded):
        parts = [title.replace(" ", ".")]
        if year:
            parts.append(str(year))
        if screen_size:
            parts.append(screen_size)
        filename = ".".join(parts) + video.suffix.lower()
        if _safe_copy(video, out_dir / filename):
            moved = True
    _copy_extras(src, out_dir, excluded)
    return moved


def _organize_series(src: Path, dest: Path, info: dict, excluded: set = None) -> bool:
    title = info.get("title", src.name)
    year = info.get("year")
    folder_name = f"{title} ({year})" if year else title
    out_base = dest / folder_name

    moved = False
    for video in _find_videos(src, excluded):
        ep_info = dict(guessit(video.name))
        season = ep_info.get("season", info.get("season", 1))
        episode = ep_info.get("episode")
        screen_size = ep_info.get("screen_size", info.get("screen_size"))

        season_dir = out_base / f"Season {season:02d}"

        ep_title = ep_info.get("title", title)
        parts = [ep_title.replace(" ", ".")]
        if episode is not None:
            parts.append(f"S{season:02d}E{episode:02d}")
        else:
            parts.append(f"S{season:02d}")
        if screen_size:
            parts.append(screen_size)
        filename = ".".join(parts) + video.suffix.lower()

        if _safe_copy(video, season_dir / filename):
            moved = True
    _copy_extras(src, out_base, excluded)
    return moved


def organize(src: Path):
    src = Path(src)

    if not src.is_dir():
        print(f"{PREFIX} Warning: '{src}' is not a directory, skipping")
        return

    print(f"{PREFIX} Processing '{src.name}'...")

    info = dict(guessit(src.name))
    media_type = info.get("type")

    if not MEDIA_CONFIDENCE_FIELDS.intersection(info):
        print(f"{PREFIX} '{src.name}' does not look like media, skipping")
        return

    excluded = _get_excluded(src)
    content_root = _resolve_content_root(src)

    print(f"{PREFIX} Copying files from '{src.name}'...")
    if media_type == "movie":
        moved = _organize_movie(content_root, Path(MOVIE_DESTINATION), info, excluded)
    elif media_type == "episode":
        moved = _organize_series(content_root, Path(SERIES_DESTINATION), info, excluded)
    else:
        print(f"{PREFIX} Unknown type, skipping")
        return
    print(f"{PREFIX} Finished copying '{src.name}'")

    if moved and state.plex_scan_enabled.is_set():
        if media_type == "movie":
            plex_scan_library("movie")
        elif media_type == "episode":
            plex_scan_library("show")

    if DELETE_SOURCE:
        try:
            shutil.rmtree(src)
            print(f"{PREFIX} Removed source '{src.name}'")
        except Exception as exc:
            print(f"{PREFIX} Could not remove source '{src.name}': {exc}")
