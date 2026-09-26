#!/usr/bin/env python3
"""Transcribe every voice line in sound/web with ElevenLabs speech-to-text and compare it with
the script in gen_sound.py, so a garbled or swapped take is caught without listening to 40 files.
Usage: set -a; . ./.env; set +a; python3 sound/check_voice.py [name ...]"""
import json, os, re, sys, subprocess
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_sound import LINES, WEB
KEY = os.environ.get("ELEVENLABS_API_KEY") or sys.exit("ELEVENLABS_API_KEY is not set")
norm = lambda s: re.sub(r"[^a-z0-9 ]", "", s.lower().replace("-", " ")).split()
NUM = {"2": "two", "3": "three", "4": "four", "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine", "10": "ten", "11": "eleven", "12": "twelve"}
def words(s): return [NUM.get(w, w) for w in norm(s)]
def one(n):
    r = subprocess.run(["curl", "-s", "https://api.elevenlabs.io/v1/speech-to-text", "-H", "xi-api-key: " + KEY,
                        "-F", "model_id=scribe_v1", "-F", "language_code=en", "-F", "tag_audio_events=false",
                        "-F", "file=@" + os.path.join(WEB, n + ".mp3")], capture_output=True, text=True)
    try: got = json.loads(r.stdout)["text"]
    except Exception: return n, None, r.stdout[:200]
    ok = words(got) == words(re.sub(r"\[[^\]]*\]", "", LINES[n]["text"]))   # an audio tag ("[yawns]") is heard, not said
    return n, ok, got
names = sys.argv[1:] or sorted(LINES)
bad = 0
with ThreadPoolExecutor(max_workers=3) as ex:
    for n, ok, got in ex.map(one, names):
        bad += not ok
        print("%s %-13s %s" % ("ok  " if ok else "DIFF", n, got if not ok else ""), ("   wanted: " + LINES[n]["text"]) if not ok else "")
print("%d of %d lines match the script" % (len(names) - bad, len(names)))
