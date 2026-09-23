#!/usr/bin/env python3
"""Write sound/board.html: every clip in sound/web on one page, grouped by when the game plays it,
with the words or the prompt that made it, so a take can be judged and sent back for another.
Usage: python3 sound/board.py   (then open sound/board.html)"""
import base64, html, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_sound import SFX, LINES, WEB, HERE

meta = json.load(open(os.path.join(WEB, "meta.json")))
WHEN = {
    "reel_spin": "The dice machine starts turning", "reel_stop": "Each reel stops (twice per roll)",
    "payout": "A roll that pays somebody", "seven": "A seven comes up",
    "card_whoosh": "A card leaves a block, the bank or a hand", "card_land": "A card lands in a hand",
    "siren": "The police are sent to a block", "tape": "The tape goes up round it",
    "steal": "A card is taken after the police move, then a taunt", "discard": "Someone drops half their hand",
    "build_street": "A street is laid", "build_op": "An operation opens, then one of the v_op lines", "build_holding": "An operation becomes a major holding",
    "trade_offer": "A trade offer goes on the table", "trade_yes": "Someone will take your offer (your phone)",
    "trade_no": "Someone passes on your offer (your phone)", "deal": "Two players swap cards, then one of the v_deal lines", "bank": "A trade with the bank",
    "turn": "A new turn starts (table)", "your_turn": "It is your move (your phone)", "join": "Someone takes a seat",
    "leave": "Someone leaves the table", "start": "The game starts, and again when the city opens; the ambience comes back up as it fades",
    "tension": "Someone reaches nine points", "win": "Someone wins", "undo": "The table undoes a move",
    "ui_tap": "Any button", "ui_fold": "Opening or folding a section", "ui_deny": "Tapping a button that is not ready yet",
    "ui_pick": "Picking a spot or a block on the board", "ui_confirm": "The big action buttons (roll, place, build, end turn)",
    "amb_city": "Loops quietly under the table screen",
    "card_buy": "A skill or talent bought at the market", "crate": "The crate shakes when an upgrade draws a card",
    "reveal": "The crate opens on a common or uncommon card", "reveal_big": "The crate opens on a rare or legendary card, then the announcer",
    "card_play": "Any skill or talent played, before its own flourish", "tipoff": "Tip-off played", "lucky": "Lucky Streak played, and its third reel stops",
    "legend": "Local Legend", "silver": "Silver Tongue played", "connections": "Connections played", "shakedown": "Shakedown played",
    "roadcrew": "Road Crew played", "paidoff": "Paid Off played", "fight_bell": "The crews walk out for a street fight",
    "punch": "A hit of 1 to 4", "punch_big": "A hit of 5 or more", "whiff": "A haymaker that misses", "block": "A hit stopped by Pull strings",
    "patch": "Patch up", "hype": "Hype", "pull": "Pull strings", "backup": "Backup arrives", "backoff": "A crew backs off",
    "ko": "A knockout", "fight_end": "A fight won on points, or by backing off",
}
GROUPS = [
    ("The dice", ["reel_spin", "reel_stop", "payout", "seven"]),
    ("Cards", ["card_whoosh", "card_land", "discard", "steal"]),
    ("The police", ["siren", "tape", "v_cop_1", "v_cop_2", "v_cop_3"]),
    ("Building", ["build_street", "build_op", "build_holding"]),
    ("Trading", ["trade_offer", "trade_yes", "trade_no", "deal", "bank"]),
    ("Turns and the game", ["join", "leave", "start", "turn", "your_turn", "tension", "win", "undo"]),
    ("Buttons", ["ui_tap", "ui_fold", "ui_pick", "ui_confirm", "ui_deny"]),
    ("The city at night", ["amb_city"]),
    ("Skills and talents", ["card_buy", "crate", "reveal", "reveal_big", "card_play", "tipoff", "lucky", "legend", "silver", "connections", "shakedown", "roadcrew", "paidoff"]),
    ("The street fight", ["fight_bell", "punch", "punch_big", "whiff", "block", "patch", "hype", "pull", "backup", "backoff", "ko", "fight_end"]),
    ("Announcer: skills and talents", [k for k in LINES if k.startswith("v_c_")] + ["v_pick", "v_rare", "v_legendary", "v_ko", "v_taken", "v_held"]),
    ("Announcer: the roll", ["v_sum_%d" % n for n in range(2, 13)]),
    ("Announcer: whose move", [k for k in LINES if k.startswith("v_up_")]),
    ("Announcer: the winner", [k for k in LINES if k.startswith("v_win_")]),
    ("Announcer: moments", ["v_start", "v_tie", "v_place", "v_open", "v_discard", "v_taunt_1", "v_taunt_2", "v_taunt_3", "v_offer", "v_deal", "v_deal_2", "v_deal_3", "v_deal_4", "v_op_1", "v_op_2", "v_op_3", "v_op_4", "v_tower", "v_nine"]),
]

def row(n):
    path = os.path.join(WEB, n + ".mp3")
    if not os.path.exists(path): return ""
    uri = "data:audio/mpeg;base64," + base64.b64encode(open(path, "rb").read()).decode()
    if n in LINES:
        words, when = "“%s”" % LINES[n]["text"], "Police radio, when the police move" if n.startswith("v_cop") else ""
    else:
        words, when = SFX[n]["text"], WHEN.get(n, "")
    return ('<li><button type="button" data-src="%s" aria-label="Play %s"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5.5v13l10.5-6.5z"/></svg></button>'
            '<div><p class="nm"><code>%s</code><span>%.1f s</span></p>%s<p class="words">%s</p></div></li>'
            % (uri, n, n, meta.get(n, 0), ('<p class="when">%s</p>' % html.escape(when)) if when else "", html.escape(words)))

body = "".join('<section><h2>%s</h2><ul>%s</ul></section>' % (html.escape(t), "".join(row(n) for n in names)) for t, names in GROUPS)
page = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Run the City sound board</title>
<style>
:root{--bg:#080b12;--panel:#111624;--ink:#e7ecf7;--muted:#8793ad;--line:#222b40;--accent:#ff2e93;--accent-ink:#16030b}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:860px;margin:0 auto;padding:28px 16px 64px}
h1{font-size:1.6rem;margin:0 0 6px}
.lede{color:var(--muted);margin:0 0 24px;max-width:60ch}
h2{font-size:.78rem;font-weight:700;text-transform:uppercase;letter-spacing:.09em;color:var(--muted);margin:28px 0 8px}
ul{list-style:none;margin:0;padding:0;display:grid;gap:8px}
li{display:flex;gap:14px;align-items:flex-start;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px}
li button{flex:none;width:44px;height:44px;border-radius:50%;border:0;background:var(--accent);color:var(--accent-ink);cursor:pointer;display:grid;place-items:center}
li button svg{width:20px;height:20px;fill:currentColor}
li button[aria-pressed=true]{background:var(--ink)}
li div{min-width:0}
p{margin:0}
.nm{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}
.nm code{font-weight:700;font-size:.95rem}
.nm span,.words{color:var(--muted);font-size:.85rem}
.when{font-size:.9rem}
.words{margin-top:2px}
</style></head><body><main>
<h1>Run the City sound board</h1>
<p class="lede">Every sound the game plays, grouped by when it plays. Each one shows the words or the prompt that made it. To redo one, say its name (the code in bold) and what is wrong with it.</p>
@@BODY@@
</main>
<script>
let cur = null, btn = null;
document.addEventListener('click', e => {
  const b = e.target.closest('button[data-src]'); if (!b) return;
  if (cur) { cur.pause(); if (btn) btn.setAttribute('aria-pressed', 'false'); }
  if (btn === b) { cur = btn = null; return; }
  cur = new Audio(b.dataset.src); btn = b; b.setAttribute('aria-pressed', 'true');
  cur.onended = () => { b.setAttribute('aria-pressed', 'false'); if (btn === b) cur = btn = null; };
  cur.play();
});
</script></body></html>""".replace("@@BODY@@", body)
out = os.path.join(HERE, "board.html")
open(out, "w", encoding="utf-8").write(page)
print("wrote %s, %d KB" % (out, len(page.encode()) // 1024))
