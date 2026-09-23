#!/usr/bin/env python3
"""Several takes of a sound, measured, so one can be chosen without guessing, and the others kept to
compare. Takes go to sound/raw/takes/ and sound/web/takes/; sound/takes.html plays them side by side
with the take in use.

    set -a; . ./.env; set +a
    python3 sound/takes.py seven reel_spin --n 3   # make 3 takes of each, measure, use the best
    python3 sound/takes.py --use seven 2          # use take 2 instead (the old one is kept in raw/_prev/)
    python3 sound/takes.py --report               # measure again and rewrite takes.html

Then: python3 sound/embed.py index.html && python3 sound/board.py

What is measured, since nobody here can listen:
  ring    how far the loudest narrow peak (300 Hz-7 kHz) stands above its neighbours (dB). Metallic, tonal sounds ring;
          paper, air and cloth do not. Lower is less metallic.
  flat    spectral flatness, 0 to 1: noise-like (airy, papery) is high, tonal is low.
  bright  spectral centroid in Hz: where the weight of the sound sits. Sharp sounds sit high.
  bass    share of the energy below 150 Hz.
  small   share of the energy between 200 Hz and 4 kHz: what a phone or laptop speaker can play.
  hold    share of the sound, in 50 ms steps, within 12 dB of its loudest moment: a drone holds.
  onset   ms until it is within 6 dB of its loudest: a ding or a click should be near 0.
  rise    semitones from the strongest note of the first third to the last: a log-out falls, a start-up rises.
  fade    dB it has sunk by its last 15%: a sting that melts away ends low.
"""
import base64, html, json, os, shutil, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_sound import SFX, RAW, WEB, HERE, gen_sfx, process, duration

TR, TW, PREV = os.path.join(RAW, "takes"), os.path.join(WEB, "takes"), os.path.join(RAW, "_prev")
STATE = os.path.join(TW, "takes.json")      # which take each sound uses, and every take's numbers


def pcm(path, rate=44100):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(rate), "-f", "f32le", "-"], capture_output=True)
    return np.frombuffer(r.stdout, dtype=np.float32), rate


def measure(path):
    x, sr = pcm(path)
    if len(x) < 2048: return {}
    x = x - x.mean()                                                    # a DC offset reads as endless bass
    n = 2048; hop = 512
    frames = np.lib.stride_tricks.sliding_window_view(x, n)[::hop] * np.hanning(n)
    M = np.abs(np.fft.rfft(frames, axis=1)) + 1e-9
    P = M ** 2
    f = np.fft.rfftfreq(n, 1 / sr)
    w = P.sum(1); w = w / w.sum()                                       # louder frames count for more
    fb = (f > 150) & (f < 6000)                                         # flatness where these sounds live, not in the empty top octave
    flat = float((np.exp(np.log(P[:, fb]).mean(1)) / P[:, fb].mean(1)) @ w)
    ab = (f > 20) & (f < 16000)
    bright = float(((M[:, ab] * f[ab]).sum(1) / M[:, ab].sum(1)) @ w)
    spec = P.mean(0)
    tot = spec[ab].sum()
    bass = float(spec[(f > 20) & (f < 150)].sum() / tot)
    small = float(spec[(f >= 200) & (f < 4000)].sum() / tot)           # what a phone or laptop speaker can actually play
    band = (f > 300) & (f < 7000)                                       # where a ring sounds like metal; above it is MP3 debris
    db = 10 * np.log10(spec[band])
    k = 31                                                              # a peak against the median of ~1 kHz around it
    pad = np.pad(db, k, mode="edge")
    med = np.array([np.median(pad[i:i + 2 * k + 1]) for i in range(len(db))])
    ring = float((db - med).max())
    step = int(sr * 0.05)
    lv = 20 * np.log10(np.array([np.sqrt(np.mean(x[i:i + step] ** 2)) + 1e-9 for i in range(0, len(x) - step + 1, step)]))
    hold = float(np.mean(lv > lv.max() - 12))
    onset = int(np.argmax(lv > lv.max() - 6) * 50)                     # ms until it is (nearly) as loud as it gets
    tail = lv[int(len(lv) * 0.85):]
    fade = float(lv.max() - tail.mean()) if len(tail) else 0.0          # how far it has sunk by the end (dB)
    # which way the pitch goes: the strongest note in the first third against the last third, in semitones
    fl = 10 * np.log10(P.sum(1)); live = fl > fl.max() - 20
    pb = (f > 150) & (f < 4000)
    pk = f[pb][M[:, pb].argmax(1)]
    idx = np.where(live)[0]
    rise = 0.0
    if len(idx) >= 6:
        a, b = idx[: len(idx) // 3], idx[-(len(idx) // 3):]
        rise = float(12 * np.log2(np.median(pk[b]) / np.median(pk[a])))
    return dict(dur=round(len(x) / sr, 2), ring=round(ring, 1), flat=round(flat, 3), bright=int(bright), bass=round(bass, 3),
                small=round(small, 3), hold=round(hold, 2), onset=onset, fade=round(fade, 1), rise=round(rise, 1),
                rms=round(float(20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)), 1))


# what "best" means for each sound that has been asked for; anything else: least ringing
SCORE = {
    "seven":       lambda m: 3 * m["bass"] + m["hold"] - m["bright"] / 4000,
    "reel_spin":   lambda m: m["hold"] - m["ring"] / 40 - max(0, 2.0 - m["dur"]),     # it has to last the whole roll
    "reel_stop":   lambda m: -m["ring"] / 20 - m["dur"],
    "card_whoosh": lambda m: 2 * m["flat"] - m["ring"] / 15 - abs(m["bright"] - 3000) / 2500 - max(0, 0.25 - m["dur"]) * 4,
    "card_land":   lambda m: m["flat"] - m["ring"] / 12 - m["bright"] / 8000,
    "steal":       lambda m: m["flat"] - m["ring"] / 12 - m["dur"] / 2,
    "discard":     lambda m: -abs(m["dur"] - 0.6) - m["ring"] / 60,
    # asked 2026-09-23: dings that go up, a bum-bamm and a log-out that go down, a start-up that rises
    "trade_yes":   lambda m: -m["onset"] / 50 - abs(m["dur"] - 0.7) + min(max(m["rise"], -3), 7) / 7,
    "join":        lambda m: -m["onset"] / 50 - abs(m["dur"] - 0.8) + min(max(m["rise"], -3), 7) / 7,
    "trade_no":    lambda m: -m["onset"] / 50 - abs(m["dur"] - 0.9) + min(-m["rise"], 12) / 6 + 2 * m["small"],   # and a phone must play it
    "leave":       lambda m: -m["onset"] / 80 - abs(m["dur"] - 1.0) + min(-m["rise"], 12) / 6,
    "build_op":    lambda m: min(m["rise"], 12) / 6 - m["onset"] / 400 - abs(m["dur"] - 1.5) / 2,
    "build_holding": lambda m: 2 * m["flat"] + m["hold"] - abs(m["dur"] - 2.6) / 2 + m["small"],
    "deal":        lambda m: -m["onset"] / 60 + m["flat"] - abs(m["dur"] - 1.6) / 2,
    "bank":        lambda m: -m["onset"] / 60 - abs(m["dur"] - 1.0) / 2,
    "start":       lambda m: m["fade"] / 10 - abs(m["dur"] - 5.5) / 2 - m["onset"] / 1000,
    "ui_fold":     lambda m: -m["onset"] / 30 - m["ring"] / 20 - m["bright"] / 6000,   # on the beat, not ringing, not bright
    # the traffic crashing (2026-09-24): the hit and the blast are timed to the picture, so they must start at once
    "crash_hit":   lambda m: -m["onset"] / 30 + m["small"] + m["flat"] / 2 - abs(m["dur"] - 1.5) / 2,
    "crash_boom":  lambda m: -m["onset"] / 40 + m["small"] + m["bass"] / 2 - abs(m["dur"] - 3.2) / 3,
    "crash_bump":  lambda m: -m["onset"] / 30 + m["small"] - abs(m["dur"] - 0.7),
    "crash_skid":  lambda m: -m["onset"] / 80 + m["small"] - abs(m["dur"] - 0.9),
}
# anything without its own rule: starts on the beat, about as long as asked for, and a phone can play it
generic = lambda name: lambda m: -m["onset"] / 60 - abs(m["dur"] - SFX[name]["d"] * 0.85) / max(0.5, SFX[name]["d"]) + m["small"] / 2
score = lambda name, m: round(SCORE.get(name, generic(name))(m), 3) if m else -99


def load_state():
    return json.load(open(STATE)) if os.path.exists(STATE) else {}


def use(name, k, st):
    src = os.path.join(TR, "%s_%d.mp3" % (name, k))
    if not os.path.exists(src): sys.exit("no take %d of %s" % (k, name))
    os.makedirs(PREV, exist_ok=True)
    cur = os.path.join(RAW, name + ".mp3")
    keep = os.path.join(PREV, name + ".mp3")
    if os.path.exists(cur) and not os.path.exists(keep): shutil.copy(cur, keep)   # the very first take, kept once
    shutil.copy(src, cur)
    process(name)
    meta = json.load(open(os.path.join(WEB, "meta.json")))
    meta[name] = round(duration(os.path.join(WEB, name + ".mp3")), 3)
    json.dump(meta, open(os.path.join(WEB, "meta.json"), "w"), indent=1, sort_keys=True)
    st.setdefault(name, {})["use"] = k


def report(st):
    rows = []
    for name in sorted(st):
        takes = st[name].get("takes", {})
        prev = os.path.join(PREV, name + ".mp3")
        if os.path.exists(prev):
            tmp = os.path.join(TW, name + "_prev.mp3"); process(name, prev, tmp)
            takes["prev"] = measure(tmp)
        for k in list(takes):
            if k == "prev": continue
            out = os.path.join(TW, "%s_%s.mp3" % (name, k))
            process(name, os.path.join(TR, "%s_%s.mp3" % (name, k)), out)   # as the game would play it now
            takes[k] = measure(out)
        st[name]["takes"] = takes
        print("%s  (%s)" % (name, SFX[name]["text"][:70] + "..."))
        for k, m in sorted(takes.items(), key=lambda kv: (kv[0] == "prev", kv[0])):
            mark = "<- in use" if str(st[name].get("use")) == str(k) else ""
            print("   %-5s ring %5.1f flat %.3f bright %5d bass %.2f small %.2f hold %.2f onset %4d rise %+5.1f fade %4.1f %4.2fs score %6.3f %s"
                  % (k, m.get("ring", 0), m.get("flat", 0), m.get("bright", 0), m.get("bass", 0), m.get("small", 0), m.get("hold", 0),
                     m.get("onset", 0), m.get("rise", 0), m.get("fade", 0), m.get("dur", 0), score(name, m), mark))
        rows.append(name)
    json.dump(st, open(STATE, "w"), indent=1)
    # the page: each sound, the take in use first
    def clip(path):
        return "data:audio/mpeg;base64," + base64.b64encode(open(path, "rb").read()).decode()
    secs = []
    for name in rows:
        items = []
        for k, m in sorted(st[name]["takes"].items(), key=lambda kv: (str(st[name].get("use")) != str(kv[0]), kv[0] == "prev", kv[0])):
            path = os.path.join(TW, "%s_%s.mp3" % (name, k))
            if not os.path.exists(path): continue
            tag = "in the game" if str(st[name].get("use")) == str(k) else ("the old one" if k == "prev" else "take %s" % k)
            items.append('<li%s><button type="button" data-src="%s" aria-label="Play %s %s">&#9654;</button><div><b>%s</b>'
                         '<small>ring %s dB &middot; airy %s &middot; bright %s Hz &middot; bass %d%% &middot; %s s</small>%s</div></li>'
                         % (' class="on"' if tag == "in the game" else "", clip(path), name, tag, tag, m.get("ring"), m.get("flat"), m.get("bright"),
                            round(100 * m.get("bass", 0)), m.get("dur"),
                            "" if k == "prev" or tag == "in the game" else "<code>python3 sound/takes.py --use %s %s</code>" % (name, k)))
        secs.append('<section><h2>%s</h2><p class="p">%s</p><ul>%s</ul></section>' % (name, html.escape(SFX[name]["text"]), "".join(items)))
    page = TAKES_PAGE.replace("@@BODY@@", "".join(secs))
    open(os.path.join(HERE, "takes.html"), "w", encoding="utf-8").write(page)
    print("wrote sound/takes.html")


TAKES_PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Run the City takes</title><style>
:root{--bg:#080b12;--panel:#111624;--ink:#e7ecf7;--muted:#8793ad;--line:#222b40;--accent:#ff2e93;--accent-ink:#16030b}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:760px;margin:0 auto;padding:28px 16px 64px}h1{font-size:1.5rem;margin:0 0 6px}.lede,.p{color:var(--muted);margin:0 0 12px}
h2{font:700 1rem ui-monospace,Menlo,monospace;margin:28px 0 4px}ul{list-style:none;margin:0;padding:0;display:grid;gap:8px}
li{display:flex;gap:14px;align-items:center;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:10px 12px}
li.on{border-color:var(--accent)}li div{display:grid;gap:2px;min-width:0}small{color:var(--muted)}code{font-size:.8rem;color:var(--muted);overflow-wrap:anywhere}
button{flex:none;width:44px;height:44px;border-radius:50%;border:0;background:var(--accent);color:var(--accent-ink);font-size:16px;cursor:pointer}
button[aria-pressed=true]{background:var(--ink)}
</style></head><body><main><h1>Takes</h1>
<p class="lede">Each sound you asked to change, with the take now in the game first (outlined), the other new takes, and the old one. The numbers are measured: ring is how metallic, airy is how noise-like, bright is where the sound sits. To swap, tell me the take number.</p>
@@BODY@@</main><script>
let cur=null,btn=null;document.addEventListener('click',e=>{const b=e.target.closest('button[data-src]');if(!b)return;
if(cur){cur.pause();btn&&btn.setAttribute('aria-pressed','false')}if(btn===b){cur=btn=null;return}
cur=new Audio(b.dataset.src);btn=b;b.setAttribute('aria-pressed','true');cur.onended=()=>{b.setAttribute('aria-pressed','false');if(btn===b)cur=btn=null};cur.play()});
</script></body></html>"""


def main():
    a = sys.argv[1:]
    os.makedirs(TR, exist_ok=True); os.makedirs(TW, exist_ok=True)
    st = load_state()
    if "--use" in a:
        i = a.index("--use"); use(a[i + 1], int(a[i + 2]), st); report(st); return
    if "--report" in a: report(st); return
    n = int(a[a.index("--n") + 1]) if "--n" in a else 3
    names = [x for x in a if x in SFX]
    bad = [x for x in a if not x.startswith("--") and x not in SFX and not x.isdigit()]
    if bad: sys.exit("unknown: " + ", ".join(bad))
    jobs = []
    for name in names:
        have = [int(f.split("_")[-1][:-4]) for f in os.listdir(TR) if f.startswith(name + "_") and f[len(name) + 1:-4].isdigit()]
        start = max(have, default=0) + 1
        jobs += [(name, k) for k in range(start, start + n)]
    def one(job):
        name, k = job; raw = os.path.join(TR, "%s_%d.mp3" % job)
        try:
            gen_sfx(name, raw); process(name, raw, os.path.join(TW, "%s_%d.mp3" % job)); return job, True
        except Exception as e:
            print("  FAILED %s take %d: %s" % (name, k, e)); return job, False
    with ThreadPoolExecutor(max_workers=3) as ex:
        for (name, k), ok in ex.map(one, jobs):
            if ok: st.setdefault(name, {}).setdefault("takes", {})[str(k)] = {}
    # measure, then put the best take of each in the game
    for name in names:
        takes = {k: measure(os.path.join(TW, "%s_%s.mp3" % (name, k))) for k in st[name]["takes"] if k != "prev"}
        best = max(takes, key=lambda k: score(name, takes[k]))
        use(name, int(best), st)
    report(st)


if __name__ == "__main__":
    main()
