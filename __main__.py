import os
import shutil
import subprocess
import pathlib
import argparse
import sys
import webbrowser
import threading
import re
from pprint import pformat
from concurrent.futures import ThreadPoolExecutor

import requests

from objects import Season
import utils

supported_hosts = ["VOE"]

# PARSER
tools_description = "A tool to download entire seasons on bs.to"
parser = argparse.ArgumentParser(prog="bs.to-downloader", description=tools_description)

parser.add_argument("url", help="the url of the season")
parser.add_argument("host", help="the video host (currently only 'VOE')", default="VOE", nargs="?")
parser.add_argument("--start", help="first episode number", default=0, type=int)
parser.add_argument("--end", help="last episode number", default=9999, type=int)
parser.add_argument("--out", help="output directory", default="output")
parser.add_argument("--flat", help="put all seasons into the base directory", action="store_true")
parser.add_argument("--dry", help="show what could have been downloaded", action="store_true")
parser.add_argument("--json", help="output json data", action="store_true")
parser.add_argument("-v", "--verbose", help="verbose", action="store_true")

args = parser.parse_args()
print("args:", args)

# LOAD EPISODE LIST
if args.verbose:
    print(f"Extracting data from {args.url}...")
s = Season(args.url)

print("Title:", pformat(s.title))
print("Season:", pformat(s.season))
print("Language:", pformat(s.language))
print(f"All episodes ({len(s.episodes)}):")
for ep in s.episodes:
    print(" ", str(ep).ljust(60), list(ep.hosts.keys()))

host_select = supported_hosts[0]  # Default auf VOE
print(f"Selected host: {host_select}")

# Filtere Episoden mit dem unterstützten Host
episodes_select = [ep for ep in s.episodes if host_select in ep.hosts]
episodes_select = [ep for ep in episodes_select if args.start <= ep.id <= args.end]

if not episodes_select:
    print("No episodes selected.")
    quit()

print(f"Selected episodes ({len(episodes_select)}):")
for ep in episodes_select:
    print(" ", ep)

# DRY RUN EXIT
if args.dry:
    print("Dry run complete.")
    quit()

print("Please solve CAPTCHAs if needed and copy-paste the host-url, then press enter:")
for ep in episodes_select:
    webbrowser.open(s.base + "/" + ep.hosts[host_select])
    ep.host_url = input(f"  {ep}: ").strip()

# CRAWL HOST SITES
match host_select:
    case "VOE":
        import host.voe
        for ep in episodes_select:
#            ep.video_url = host.voe.resolve(ep.host_url)
            ep.filetype = "mp4"
    case _:
        print("ERROR: Unsupported host")
        quit()

# OUTPUT
outpath = pathlib.Path(args.out).joinpath(utils.safe_filename(s.series_str))
outpath.mkdir(parents=True, exist_ok=True)

if args.json:
    import json
    data = {
        "title": s.title,
        "season": s.season,
        "language": s.language,
        "host_select": host_select,
        "episodes_select": [{"title": ep.title, "id": ep.id, "host_url": ep.host_url, "video_url": ep.video_url} for ep in episodes_select]
    }
    filepath = outpath.joinpath(utils.safe_filename(f"{s.id_str}.json"))
    with filepath.open("w") as file:
        file.write(json.dumps(data, indent=4))

# DOWNLOAD
sepath = outpath if args.flat else outpath.joinpath(utils.safe_filename(s.season_str))
sepath.mkdir(parents=True, exist_ok=True)

downloads = [(ep.video_url, sepath.joinpath(utils.safe_filename(f"{s.season_str}.{ep.episode_str}.{ep.filetype}"))) for ep in episodes_select]

for ep in episodes_select:
    print(f"Converting {ep} to MP4...")

    # Hole die m3u8-URL von voe.py
    m3u8_url = host.voe.resolve(ep.host_url)

    if not m3u8_url:
        print("Failed to resolve m3u8 URL.")
        continue

    # Bestimme den Ausgabepfad für das MP4
    output_file = sepath.joinpath(utils.safe_filename(f"{s.season_str}.{ep.episode_str}.{ep.title}.mp4"))

    # Konvertiere mit ffmpeg
    success = host.voe.convert_to_mp4(m3u8_url, output_file)

    if not success:
        print(f"Failed to convert {ep} to MP4.")
        continue

print("All conversions complete.")
