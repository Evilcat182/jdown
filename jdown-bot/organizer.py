from pathlib import Path
import os
import re
import shutil
import fnmatch
from guessit import guessitk
from plex import plex_scan_library
from functions import log
import state

PREFIX = "[Organizer]"
VIDEO_EXTENSIONS = {".mkv", ".mp4", ".avi", ".m4v", ".mov", ".wmv"}
MEDIA_CONFIDENCE_FIELDS = {"screen_size", "source", "video_codec", "audio_codec"}
MOVIE_DESTINATION = os.getenv("MOVIE_DESTINATION", "/output/done")
SERIES_DESTINATION = os.getenv("SERIES_DESTINATION", "/output/done")

movie_settings = {
    "folder_template_name": "{title} {year_in_brackets}",
    "file_template_name": "{dotted_title}.{year}.{video_codec}.{screen_size}",
    "mandatory": ["title","dotted_title","year","video_codec","screen_size"]
}

series_settings = {
    "folder_template_name": "{title} {year_in_brackets}",
    "file_template_name": "{dotted_title}.{season_and_episode}.{dotted_episode_title}.{video_codec}.{screen_size}",
    "episode_folder_template_name": "{dotted_title}.{season_and_episode}.{dotted_episode_title}.{video_codec}.{screen_size}",
    "mandatory": ["title","dotted_title","season_and_episode","video_codec","screen_size"]
}

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
        "Pattern": "*.iso",
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

def _guessit(name: str):
    result = guessit(name)
    result["dotted_title"] = result["title"].replace(" ",".")
    if result.get("video_codec"):
        result["video_codec"] = result["video_codec"].replace(".","")
    if result.get("screen_size"):
        result["screen_size"] = result["screen_size"] if result["screen_size"].endswith("p") else f"{result["screen_size"]}p"
    if result.get("episode_title"):
        result["dotted_episode_title"] = result["episode_title"].replace(" ",".")
    if result.get("year"):
        result["year_in_brackets"] = f"({result["year"]})"
    if result.get("season") and result.get("episode"):
        result["season_and_episode"] = f"S{result["season"]:02}E{result["episode"]:02}"
    return result

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
            log(f"Excluding '{entry}' from copy", PREFIX, "debug")
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
            log(f"'{dst.name}' already exists, skipping", PREFIX, "warning")
            return False
        label = " (updated)"
    else:
        label = ""
    shutil.copy2(str(src), str(dst))
    log(f"'{src.name}' -> '{dst}'{label}", PREFIX)
    return True


def _resolve_content_root(src: Path) -> Path:
    """If src contains exactly one subdirectory and no direct video files, return that subdirectory."""
    entries = list(src.iterdir())
    subdirs = [e for e in entries if e.is_dir()]
    video_files = [e for e in entries if e.is_file() and e.suffix.lower() in VIDEO_EXTENSIONS]
    if len(subdirs) == 1 and not video_files:
        return subdirs[0]
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


def _check_mandatory(info: dict, mandatory: list) -> list[str]:
    return [f for f in mandatory if not info.get(f)]


def _render_template(template: str, info: dict, sep: str = ".") -> str:
    parts = []
    for seg in template.split(sep):
        keys = re.findall(r"\{(\w+)\}", seg)
        if not keys:
            parts.append(seg)
        elif all(info.get(k) for k in keys):
            parts.append(seg.format(**{k: info[k] for k in keys}))
        # else: optional field missing — skip segment to avoid empty tokens
    return sep.join(parts)


def _write_error(path: Path, lines: list[str]):
    error_file = path / "ORGANIZER-ERROR.txt"
    with error_file.open("a") as fh:
        fh.write(f"Path: {path.resolve()}\n")
        fh.writelines(lines)
        fh.write("\n")


def _organize_movie(src: Path, dest: Path, info: dict, videos: list[Path], excluded: set = None, error_path: Path = None) -> bool:
    ep = error_path or src

    if len(videos) > 1:
        lines = [f"Multiple video files found for a movie ({len(videos)} files):\n"]
        lines += [f"  - {v.name}\n" for v in videos]
        lines += ["Nothing was copied. Please verify the content and organize manually.\n"]
        _write_error(ep, lines)
        log(f"Multiple video files found in '{ep.name}', skipping", PREFIX, "warning")
        return False

    missing = _check_mandatory(info, movie_settings["mandatory"])
    if missing:
        video_info = dict(_guessit(videos[0].name))
        merged = {**info, **{k: v for k, v in video_info.items() if v is not None and not info.get(k)}}
        missing = _check_mandatory(merged, movie_settings["mandatory"])
        if not missing:
            log(f"Filled missing fields from video filename '{videos[0].name}'", PREFIX, "debug")
            info = merged
        else:
            _write_error(ep, ["The following mandatory fields could not be determined:\n"] + [f"  - {f}\n" for f in missing])
            log(f"Missing mandatory fields {missing} in '{ep.name}', skipping", PREFIX, "warning")
            return False

    folder_name = _render_template(movie_settings["folder_template_name"], info, sep=" ")
    out_dir = dest / folder_name

    moved = False
    for video in videos:
        filename = _render_template(movie_settings["file_template_name"], info, sep=".") + video.suffix.lower()
        if _safe_copy(video, out_dir / filename):
            moved = True
    _copy_extras(src, out_dir, excluded)
    return moved


def _organize_series(src: Path, dest: Path, info: dict, videos: list[Path], excluded: set = None, error_path: Path = None) -> bool:
    ep = error_path or src

    title_missing = _check_mandatory(info, ["title", "dotted_title"])
    if title_missing:
        _write_error(ep, ["The following mandatory fields could not be determined:\n"] + [f"  - {f}\n" for f in title_missing])
        log(f"Missing mandatory fields {title_missing} in '{ep.name}', skipping", PREFIX, "warning")
        return False

    folder_name = _render_template(series_settings["folder_template_name"], info, sep=" ")
    out_base = dest / folder_name

    # Pre-flight: validate all videos before copying anything
    merged_per_video: list[tuple[Path, dict]] = []
    for video in videos:
        ep_info = dict(_guessit(video.name))
        folder_info = dict(_guessit(video.parent.name)) if video.parent != src else {}
        merged = {**info,
                  **{k: v for k, v in folder_info.items() if v is not None},
                  **{k: v for k, v in ep_info.items() if v is not None}}
        merged["title"] = info["title"]
        merged["dotted_title"] = info["dotted_title"]
        missing = _check_mandatory(merged, series_settings["mandatory"])
        if missing:
            _write_error(ep, ["The following mandatory fields could not be determined:\n"] + [f"  - {f}\n" for f in missing])
            log(f"Missing mandatory fields {missing} in '{ep.name}', skipping", PREFIX, "warning")
            return False
        merged_per_video.append((video, merged))

    moved = False
    dir_mapping: dict[Path, Path] = {}
    for video, merged in merged_per_video:
        season = merged.get("season", 1)
        season_dir = out_base / f"Season {season:02d}"
        episode_folder_template = series_settings.get("episode_folder_template_name")
        if episode_folder_template:
            episode_dir = season_dir / _render_template(episode_folder_template, merged, sep=".")
        else:
            episode_dir = season_dir
        filename = _render_template(series_settings["file_template_name"], merged, sep=".") + video.suffix.lower()
        if _safe_copy(video, episode_dir / filename):
            moved = True
        dir_mapping[video.parent] = episode_dir

    # Copy extras, mapping each file to its nearest episode dir or out_base
    for f in src.rglob("*"):
        if not f.is_file() or f.suffix.lower() in VIDEO_EXTENSIONS:
            continue
        if excluded and _is_excluded(f, excluded):
            continue
        mapped_dir = next((dir_mapping[p] for p in [f.parent, *f.parent.parents] if p in dir_mapping and p != src), None)
        rel = f.relative_to(mapped_dir) if mapped_dir else f.relative_to(src)
        _safe_copy(f, (mapped_dir or out_base) / rel)

    return moved


def organize(src: Path):
    src = Path(src)

    if not src.is_dir():
        log(f"'{src}' is not a directory, skipping", PREFIX, "warning")
        return

    log(f"Processing '{src.name}'...", PREFIX)

    info = dict(_guessit(src.name))
    media_type = info.get("type")

    if not MEDIA_CONFIDENCE_FIELDS.intersection(info):
        log(f"'{src.name}' does not look like media, skipping", PREFIX, "warning")
        return

    excluded = _get_excluded(src)
    content_root = _resolve_content_root(src)
    videos = _find_videos(content_root, excluded)

    if not videos:
        _write_error(src, ["No video files found.\n"])
        log(f"No video files found in '{src.name}', skipping", PREFIX, "warning")
        return

    log(f"Copying files from '{src.name}'...", PREFIX)
    if media_type == "movie":
        moved = _organize_movie(content_root, Path(MOVIE_DESTINATION), info, videos, excluded, error_path=src)
    elif media_type == "episode":
        moved = _organize_series(content_root, Path(SERIES_DESTINATION), info, videos, excluded, error_path=src)
    else:
        log(f"'{src.name}' has unknown media type '{media_type}', skipping", PREFIX, "warning")
        return

    if moved:
        log(f"Finished copying '{src.name}'", PREFIX, "success")

    if moved and state.plex_scan_enabled.is_set():
        if media_type == "movie":
            plex_scan_library("movie")
        elif media_type == "episode":
            plex_scan_library("show")

    if moved and state.delete_source_enabled.is_set():
        try:
            shutil.rmtree(src)
            log(f"Removed source '{src.name}'", PREFIX)
        except Exception as exc:
            log(f"Could not remove source '{src.name}': {exc}", PREFIX, "error")
