from pathlib import Path
import os
import shutil
import fnmatch
from guessit import guessit
from plex import plex_scan_library

PREFIX = "[Organizer]"
VIDEO_EXTENSIONS = {".mkv", ".mp4", ".avi", ".m4v", ".mov", ".wmv"}
MEDIA_CONFIDENCE_FIELDS = {"screen_size", "source", "video_codec", "audio_codec"}
MOVIE_DESTINATION = os.getenv("MOVIE_DESTINATION","/output/done")
SERIES_DESTINATION = os.getenv("SERIES_DESTINATION","/output/done")


cleanup_settings = [
    {
        "Pattern": "*.nfo",
        "Dir": False,
        "CS": False
    },
    {
        "Pattern": "sample",
        "Dir": True,
        "CS": False
    }
]


def cleanup(path: str, settings: list = cleanup_settings):
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
            try:
                if match_dirs:
                    shutil.rmtree(entry)
                    print(f"{PREFIX} Removed dir '{entry}'")
                else:
                    os.remove(entry)
                    print(f"{PREFIX} Removed '{entry}'")
            except Exception as exc:
                print(f"{PREFIX} Error while removing '{entry}': {exc}")


def _find_videos(path: Path) -> list[Path]:
    return [f for f in path.rglob("*") if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS]


def _safe_move(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        print(f"{PREFIX} Warning: '{dst}' already exists, skipping")
        return
    shutil.move(str(src), str(dst))
    print(f"{PREFIX} '{src.name}' -> '{dst}'")


def _organize_movie(src: Path, dest: Path, info: dict):
    title = info.get("title", src.name)
    year = info.get("year")
    screen_size = info.get("screen_size")

    folder_name = f"{title} ({year})" if year else title
    out_dir = dest / folder_name

    for video in _find_videos(src):
        parts = [title.replace(" ", ".")]
        if year:
            parts.append(str(year))
        if screen_size:
            parts.append(screen_size)
        filename = ".".join(parts) + video.suffix.lower()
        _safe_move(video, out_dir / filename)


def _organize_series(src: Path, dest: Path, info: dict):
    title = info.get("title", src.name)
    year = info.get("year")
    folder_name = f"{title} ({year})" if year else title
    out_base = dest / folder_name

    for video in _find_videos(src):
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

        _safe_move(video, season_dir / filename)


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

    cleanup(src)

    import state
    if media_type == "movie":
        _organize_movie(src, Path(MOVIE_DESTINATION), info)
        if state.plex_scan_enabled.is_set():
            plex_scan_library("movie")
    elif media_type == "episode":
        _organize_series(src, Path(SERIES_DESTINATION), info)
        if state.plex_scan_enabled.is_set():
            plex_scan_library("show")
    else:
        print(f"{PREFIX} Unknown type, skipping")
        return

    try:
        shutil.rmtree(src)
        print(f"{PREFIX} Removed source '{src.name}'")
    except Exception as exc:
        print(f"{PREFIX} Could not remove source '{src.name}': {exc}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(f"{PREFIX} Error: path argument required", file=sys.stderr)
        sys.exit(1)
    organize(sys.argv[1])
