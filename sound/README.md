# Sound

The scripts that make Run the City's sound with the ElevenLabs API: every effect, button sound,
the city ambience, the announcer and the police dispatcher. Only these scripts are in the repo.
The audio they make (`raw/`, `web/`), the audition pages and the API key stay on the machine that
made them. What the game plays is published as the two packs beside the page, `sound-fx.bin` and
`sound-table.bin`.

Every command reads `ELEVENLABS_API_KEY` from the environment. Keep it in the repo's git-ignored
`.env`, and never in the page or a script:

    set -a; . ./.env; set +a

| Script | What it does |
|---|---|
| `gen_sound.py` | Holds every prompt and voice line. Generates what is missing into `raw/`, then trims, levels and encodes each clip into `web/`. `--force NAME` redoes one, `--process` only re-levels. |
| `takes.py` | Makes several takes of a sound, measures them (how metallic, airy, bright, bass-heavy, whether a phone speaker can play it, which way the pitch goes) and uses the best. `--use NAME K` swaps takes; `takes.html` compares them. |
| `check_voice.py` | Runs every voice line back through speech-to-text and compares it with the script. |
| `embed.py` | Packs `web/` into `sound-fx.bin` (all a phone can play) and `sound-table.bin` (the announcer, the dice machine, the ambience), and writes their index into `index.html`. |
| `board.py` | Writes `board.html`, a page to audition every clip. |
| `land.py` | Retired: the one-off script that first put the sound engine into the page. |

**Levels (2026-09-26).** Clips are levelled by how hard they hit the ear, not by their average: the
loudest 400 ms, K-weighted (`loudness()` in `gen_sound.py`, about EBU R128's momentary loudness).
The announcer sets the level (-17), the effects sit 4 dB and more under him (`LOUD`), the busy ones
(cards, reels, taps) lower still. Every clip is encoded hot, near full scale, because the MP3 encoder
throws away quiet highs it thinks nobody can hear; `process()` then measures what it made and writes
how far down (or up) the page should play it to `web/trims.json`, which `embed.py` puts in the page's
index as each clip's fifth number. So a mix change is a change to `LOUD` and a `--process`, and the
page's own `vol` numbers only say what matters more in a moment. The page also softens every start,
dips everything under the announcer, and plays no more than four effects at once (three on a phone).

After changing a clip, run `python3 sound/embed.py index.html`. Then commit `index.html`,
`sound-fx.bin` and `sound-table.bin` together: the page's index carries a hash of each pack, and
a page whose packs do not match plays nothing.

Generation is not repeatable: the same prompt gives a different take each time. So the published
packs, not these scripts, are the record of what the game sounds like.

Needs Python 3 with numpy, and ffmpeg with libmp3lame.
