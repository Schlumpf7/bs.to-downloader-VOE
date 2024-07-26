import os
import shutil
import subprocess
import pathlib
import argparse
import sys
import webbrowser
from pprint import pformat

import requests

from objects import Season
import utils


supported_hosts = ["VOE"]

sys.argv=["url","https://bs.to/serie/The-Big-Bang-Theory-TBBT/1/de", "--start", "4"]
# PARSER
parser = argparse.ArgumentParser(
    prog="bs.to-downloader",
    description="A tool to download entire seasons on bs.to")


parser.add_argument("url", help="the url of the season")
parser.add_argument("host", help="the video host (currently only 'VOE')",
                    default="vivo", nargs="?")

parser.add_argument("--start", help="first episode number",
                    default=0, type=int)
parser.add_argument("--end", help="last episode number",
                    default=9999, type=int)

parser.add_argument("--out", help="output directory",
                    default="output")
parser.add_argument("--flat", help="put all seasons into the base directory",
                    action="store_true")
# parser.add_argument("--script",
#                     help="instead of downloading, generate a download script",
#                     action="store_true")

parser.add_argument("--dry", help="should what could have been downloaded",
                    action="store_true")
parser.add_argument("--json", help="output json data",
                    action="store_true")
parser.add_argument("-v", "--verbose", help="verbose",
                    action="store_true")


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

print("Available hosts:", s.all_hosts)

host_select = supported_hosts[0]  # args.host
print(f"Currently the only supported host is '{supported_hosts[0]}'")
print("Selected host:", pformat(host_select))

#creates list of episodes with supported hosts
episodes_select = [ep for ep in s.episodes if host_select in ep.hosts]
#thins out the list by start and end episode
episodes_select = [ep for ep in episodes_select
                   if args.start <= ep.id <= args.end]

if not episodes_select:  # no episodes selected / no episodes with supported host
    print("no episodes selected.")
    quit()

print(f"Selected episodes ({len(episodes_select)}):")
for ep in episodes_select:
    print(" ", ep)


# dry run exit
if args.dry:
    print("dry run complete.")
    quit()


print(("Please solve CAPTCHAs if needed and copy-paste the host-url, "
       "then press enter:"))
for ep in episodes_select:
    #hosts[host_selected] returns the second value of the host-tuple (see objects.py l.66)
    webbrowser.open(s.base + "/" + ep.hosts[host_select])
    ep.host_url = input(f"  {ep}: ").strip()


# CRAWL HOST SITES
match host_select:
    case "VOE":
        import host.voe
        for ep in episodes_select:
            ep.video_url=host.voe.resolve(ep.host_url)
            ep.filetype="mp4"
            
    case "vivo":
        import host.vivo
        for ep, url in zip(episodes_select, host.vivo.resolve([ep.host_url for ep in episodes_select])):
            ep.video_url = url[0]
            ep.filetype = url[1].split("/")[1]
    case _:
        print("ERROR")
        quit()


# OUTPUT
#create output directory (output argument + series title)
outpath = pathlib.Path(args.out).joinpath(utils.safe_filename(s.series_str))
print(f"Output directory: '{outpath.absolute()}'")
outpath.mkdir(parents=True, exist_ok=True)

if args.json:
    # data file
    import json
    data = {
        "title": s.title,
        "season": s.season,
        "language": s.language,
        "host_select": host_select,
        "episodes_select": [{"title": ep.title, "id": ep.id,
                             "host_url": ep.host_url,
                             "video_url": ep.video_url}
                            for ep in episodes_select]
    }
    filepath = outpath.joinpath(utils.safe_filename(f"{s.id_str}.json"))
    with filepath.open("w") as file:
        file.write(json.dumps(data, indent=4))


# DOWNLOAD
sepath = pathlib.Path()
if not args.flat:  # season path:
    sepath = outpath.joinpath(utils.safe_filename(s.season_str))

#create list of tuples (video_url, epidode_path)
downloads=[]
for ep in episodes_select:
    eppath=sepath.joinpath(utils.safe_filename(f"{s.season_str}.{ep.episode_str}.{ep.filetype}"))#path per episode (sepath/Series_string.episode_string.filetype)
    downloads.append((ep.video_url, eppath))


#legacy Download procedure for vivo
"""  #SCRIPT
scriptpath = outpath.joinpath(utils.safe_filename(f"Download {s.id_str}.sh"))
with scriptpath.open("w") as file:
    if not args.flat:
        file.write(f"mkdir -p \"{eppath}\"\n")
    for d in downloads:
        file.write(
            f"wget --no-check-certificate {d[0]} -O \"{d[1]}\"\n")
scriptpath.chmod(0o775)  # make download script executable
print(f"Generated download script '{scriptpath.name}'") 

# RUN DOWNLOAD SCRIPT
print("Downloading...")
cmds = [
    f"cd \"{outpath}\"",
    f"\"./{scriptpath.relative_to(outpath)}\""
]

if args.verbose:
    for cmd in cmds:
        print(f"$ {cmd}")
os.system(" && ".join(cmds))  """

#CREATE output dir
os.makedirs(sepath, exist_ok=True)

#SCRIPT FOR HLS FILES
for d in downloads:#downloading temporary files (segments+playlist)
    print("DOWNLOADING "+str(d[1]).split("\\")[-1])
    if d[0]==None:
        print("DOWNLOAD FAILED")
        continue
    if os.path.isdir("./tmp"): shutil.rmtree("./tmp")
    os.mkdir("./tmp")
    m3u8_filename = d[0][0].split('/')[-1].split("?")[0]
    i=0
    for link in d[0]:
        #TODO: MULTITHREAD THIS BITCH (its slow af)
        print("Downloading Segment "+str(i)+"/"+str(len(d[0])-1))
        i+=1
        local_filename = "./tmp/"+link.split('/')[-1].split("?")[0]
        f=open(local_filename, "wb")
        f.write(requests.get(link).content)
        f.close()

        #RE-FORMAT M3U8 file to just contain the file names(delete everything after .ts)
        f=open("./tmp/"+m3u8_filename)
        f_new=open("./tmp/"+m3u8_filename+"_new", "w")
        to_replace=""
        for line in f:
            if to_replace=="" and line.__contains__("?t"):
                to_replace="?t"+line.split("?t")[1][:-1]
            line=line.replace(to_replace, "")
            f_new.write(line)
        f.close()
        f_new.close()
        os.remove("./tmp/"+m3u8_filename)#remove old file
        os.rename("./tmp/"+m3u8_filename+"_new","./tmp/"+m3u8_filename)#rename new file

    #CONVERT m3u8 to mp4 using ffmpeg
    subprocess.run(["ffmpeg", "-y", "-i", "./tmp/"+m3u8_filename, "-acodec", "copy", "-vcodec", "copy", "-hide_banner", "-loglevel", "error", d[1]])
    shutil.rmtree("./tmp")
            
print("done.")
