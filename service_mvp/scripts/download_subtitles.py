from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

from env_config import cookie_status


def build_command(args: argparse.Namespace, cookie_file: Path | None) -> list[str]:
    command = [
        "yt-dlp",
        "--skip-download",
        "--sub-lang",
        args.lang,
        "--sub-format",
        "vtt",
        "-o",
        str(Path(args.output_dir) / "%(title)s [%(id)s].%(ext)s"),
    ]

    if args.auto_subs:
        command.append("--write-auto-subs")
    else:
        command.append("--write-subs")

    if cookie_file and not args.no_cookies:
        command.extend(["--cookies", str(cookie_file)])

    command.append(args.url)
    return command


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download YouTube subtitles with optional cookies from .env."
    )
    parser.add_argument("url", nargs="?", help="YouTube video URL.")
    parser.add_argument(
        "-o",
        "--output-dir",
        default=".",
        help="Directory for downloaded subtitle files.",
    )
    parser.add_argument("--lang", default="en", help="Subtitle language, default: en.")
    parser.add_argument(
        "--manual-subs",
        dest="auto_subs",
        action="store_false",
        help="Use manual subtitles instead of auto subtitles.",
    )
    parser.add_argument(
        "--no-cookies",
        action="store_true",
        help="Do not use the cookie file even if YTDLP_COOKIE_FILE exists.",
    )
    parser.add_argument(
        "--check-env",
        action="store_true",
        help="Only check whether YTDLP_COOKIE_FILE points to an existing file.",
    )
    parser.set_defaults(auto_subs=True)
    args = parser.parse_args()

    cookie_file, has_cookie = cookie_status()
    if args.check_env:
        if has_cookie:
            print(f"YTDLP_COOKIE_FILE found: {cookie_file}")
        elif cookie_file:
            print(f"YTDLP_COOKIE_FILE configured but file is missing: {cookie_file}")
        else:
            print("YTDLP_COOKIE_FILE is not configured.")
        return

    if not args.url:
        raise SystemExit("YouTube URL is required unless --check-env is used.")

    if not shutil.which("yt-dlp"):
        raise SystemExit("yt-dlp was not found in PATH.")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if has_cookie and not args.no_cookies:
        print(f"Using cookie file: {cookie_file}")
    elif cookie_file and not args.no_cookies:
        print(f"Cookie file missing, continuing without cookies: {cookie_file}")
    else:
        print("Continuing without cookies.")

    command = build_command(args, cookie_file if has_cookie else None)
    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
