#!/usr/bin/env python3
"""RETIRED (2026-09-24): index.html now holds the engine, merged with the card system, and the clips
load from sound-*.bin. Edit index.html in place; this is kept only as a record of the first landing.

Put the sound engine into a copy of the page: CSS, the engine itself, the sound button in both
headers, and the one-line hooks in the animations and the renderers. Every edit is anchored on a
line that has to exist exactly once, so this can be run against whatever index.html is by the time
it lands (another chat may have changed it) and it stops, rather than guessing, if an anchor moved.
Then run sound/embed.py on the same file for the clips.
Usage: python3 sound/land.py page.html"""
import sys

CSS = r"""
/* ---------- sound: the speaker button and its panel ---------- */
.sndbtn{appearance:none;display:inline-grid;place-items:center;flex:none;width:34px;height:34px;padding:0;border:1px solid var(--line);border-radius:10px;background:transparent;color:var(--muted);cursor:pointer}
.sndbtn:hover,.sndbtn[aria-expanded=true]{color:var(--ink)}
.sndbtn[aria-expanded=true]{border-color:var(--accent)}
.sndpanel{position:fixed;right:max(12px,env(safe-area-inset-right,0px));top:58px;z-index:45;width:min(320px,calc(100vw - 24px));display:grid;gap:2px;
  padding:12px 10px 14px;background:var(--panel);border:1px solid var(--line);border-radius:14px;box-shadow:var(--shadow)}
.sndpanel h2{margin:2px 8px 6px}
.sndrow{appearance:none;display:flex;align-items:center;gap:14px;width:100%;min-height:52px;padding:8px;border:0;border-radius:10px;background:transparent;text-align:left;cursor:pointer}
.sndrow:hover{background:rgba(255,255,255,.04)}
.sndrow span{flex:1;display:grid;gap:1px}
.sndrow small{color:var(--muted);font-size:.8rem;line-height:1.3}
.sndsw{flex:none;position:relative;width:40px;height:24px;border-radius:99px;background:var(--off);transition:background .15s}
.sndsw::after{content:"";position:absolute;top:3px;left:3px;width:18px;height:18px;border-radius:50%;background:var(--ink);transition:transform .15s}
.sndrow[aria-checked=true] .sndsw{background:var(--accent)}
.sndrow[aria-checked=true] .sndsw::after{transform:translateX(16px)}
.sndvol{display:flex;align-items:center;gap:14px;min-height:48px;padding:4px 8px 0;font-weight:700}
.sndvol input{flex:1;min-width:0;accent-color:var(--accent)}
@media (prefers-reduced-motion:reduce){.sndsw,.sndsw::after{transition:none}}
"""

JS = r"""/* =====================================================================
   Sound
   Like the animations, every sound is worked out from the state on this
   screen and never sent: the relay protocol and validState know nothing of
   it. The clips are MP3s embedded at the foot of the page (sound/embed.py,
   made by sound/gen_sound.py) and decoded only after the first tap, the
   first moment a browser lets a page make a noise at all.

   Who hears what. The table screen, and any board view, is the room's
   speaker: the dice, the announcer, the police, the city at night. A phone
   plays what is about its owner (your turn, your cards, an offer to
   answer) and its own button taps, so a room with five phones in it does
   not roll the dice five times over. "Hear the whole table" gives a phone
   the table's sounds as well, for somebody playing from somewhere else.
   Nothing plays in a hidden tab, the same rule the animations keep.
   ===================================================================== */
const SND_DEFAULT = { fx: true, voice: true, amb: true, all: false, vol: 80 };
const SND_GAIN = { fx: 1, ui: 0.55, voice: 1, amb: 0.32 };
const SND = { ctx: null, master: null, bus: {}, data: null, buf: {}, dec: {}, last: {}, q: [], talking: 0, talkId: 0, amb: null, sig: null, open: false, pick: {}, melt: 0,
  prefs: Object.assign({}, SND_DEFAULT) };
(() => { const s = load('rtcity.snd'); if (s && typeof s === 'object') Object.keys(SND_DEFAULT).forEach(k => { if (typeof s[k] === typeof SND_DEFAULT[k]) SND.prefs[k] = s[k]; }); })();
const sndMe = () => (joinRoom && !WATCH ? PID : null);               // the seat this phone plays, if it is a phone
const sndTable = () => !joinRoom || WATCH;
const sndHearsTable = () => sndTable() || SND.prefs.all;
const sndAny = () => SND.prefs.vol > 0 && (SND.prefs.fx || (SND.prefs.voice && sndHearsTable()) || (SND.prefs.amb && sndTable()));

function sndUnlock() {
  if (SND.ctx) { if (SND.ctx.state === 'suspended') SND.ctx.resume().catch(() => {}); return; }
  if (!sndAny()) return;                                               // everything off: never make a context at all
  const AC = window.AudioContext || window.webkitAudioContext, el = document.getElementById('snd-data');
  if (!AC || !el) return;
  try {
    SND.data = JSON.parse(el.textContent);
    let c; try { c = new AC({ latencyHint: 'interactive' }); } catch (e) { c = new AC(); }
    SND.ctx = c;
    // a gentle compressor on the way out, so a flurry of cards under the announcer never clips
    const out = c.createDynamicsCompressor();
    out.threshold.value = -14; out.knee.value = 12; out.ratio.value = 4; out.attack.value = 0.004; out.release.value = 0.2;
    out.connect(c.destination);
    SND.master = c.createGain(); SND.master.connect(out);
    Object.keys(SND_GAIN).forEach(k => { const g = SND.bus[k] = c.createGain(); g.gain.value = 0; g.connect(SND.master); });
    sndLevels();
    // an empty buffer started inside the gesture is what finally unlocks iOS
    const s = c.createBufferSource(); s.buffer = c.createBuffer(1, 1, 22050); s.connect(c.destination); s.start(0);
    if (c.state === 'suspended') c.resume().catch(() => {});
    sndWarm(); sndAmb();
  } catch (e) { console.error(e); SND.ctx = null; }
}
['pointerdown', 'keydown', 'touchend'].forEach(t => document.addEventListener(t, sndUnlock, { capture: true, passive: true }));

function sndLevels() {
  const c = SND.ctx; if (!c) return;
  const p = SND.prefs, t = c.currentTime;
  SND.master.gain.setTargetAtTime(Math.pow(p.vol / 100, 1.6), t, 0.03);          // a slider that feels even to the ear
  SND.bus.fx.gain.setTargetAtTime(p.fx ? SND_GAIN.fx : 0, t, 0.03);
  SND.bus.ui.gain.setTargetAtTime(p.fx ? SND_GAIN.ui : 0, t, 0.03);
  SND.bus.voice.gain.setTargetAtTime(p.voice ? SND_GAIN.voice : 0, t, 0.03);
  if (!(SND.melt > performance.now()))                                // (the start sting is moving it by itself)
    SND.bus.amb.gain.setTargetAtTime(SND_GAIN.amb * (SND.talking ? 0.4 : 1), t, SND.talking ? 0.08 : 0.6);   // the city dips under the voice
}
function sndBuf(name) {
  if (SND.buf[name]) return Promise.resolve(SND.buf[name]);
  if (SND.dec[name]) return SND.dec[name];
  const b64 = SND.data && SND.data.clips[name];
  if (!b64 || !SND.ctx) return Promise.resolve(null);
  return (SND.dec[name] = new Promise(done => {
    let bytes;
    try { const bin = atob(b64); bytes = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i); } catch (e) { done(null); return; }
    const ok = b => { SND.buf[name] = b; done(b); }, bad = () => done(null);
    try { const p = SND.ctx.decodeAudioData(bytes.buffer, ok, bad); if (p && p.catch) p.catch(bad); } catch (e) { bad(); }
  }));
}
/* decode in the background, one clip at a time, the ones a tap needs first */
function sndWarm() {
  const names = Object.keys((SND.data && SND.data.clips) || {}), phone = !sndHearsTable();
  const first = ['ui_tap', 'ui_fold', 'ui_pick', 'ui_confirm', 'ui_deny', 'card_land', 'card_whoosh', 'your_turn', 'reel_spin', 'reel_stop'];
  const order = first.filter(n => names.includes(n)).concat(names.filter(n => !first.includes(n) && !(phone && /^(v_|amb_)/.test(n))));
  const next = () => { const n = order.shift(); if (n) sndBuf(n).then(() => setTimeout(next, 16)); };
  next();
}
/* One clip, now or `at` ms from now. `dur` cuts it short with a quick fade, `detune` (cents)
   varies a sound that repeats, and one name never starts twice within `gap` ms: a dozen cards
   landing together should sound like a handful, not a drum roll. */
function sfx(name, o = {}) {
  const c = SND.ctx;
  if (!c || c.state !== 'running' || document.hidden || !SND.prefs.fx) return;
  const cat = o.cat || (name.startsWith('ui_') ? 'ui' : 'fx'), now = performance.now();
  if (o.gap !== 0 && now - (SND.last[name] || 0) < (o.gap || 40)) return;
  SND.last[name] = now;
  const when = c.currentTime + (o.at || 0) / 1000, vol = o.vol == null ? 1 : o.vol;
  const go = b => {
    if (!b || SND.ctx !== c || c.currentTime > when + 0.25) return;  // decoded too late to mean anything
    const s = c.createBufferSource(), g = c.createGain(), t = Math.max(c.currentTime, when);
    s.buffer = b;
    if (o.detune && s.detune) s.detune.value = (Math.random() * 2 - 1) * o.detune;
    g.gain.setValueAtTime(vol, c.currentTime); s.connect(g); g.connect(SND.bus[cat]); s.start(t);
    if (o.dur) { const end = t + o.dur / 1000; g.gain.setValueAtTime(vol, Math.max(t, end - 0.12)); g.gain.linearRampToValueAtTime(0.0001, end); s.stop(end + 0.02); }
  };
  if (SND.buf[name]) go(SND.buf[name]); else sndBuf(name).then(go);
}
/* The announcer says one line at a time. A line that waited too long is dropped: the game has moved on.
   `mine` lets a phone say a line about its own owner (the taunt when you are robbed) without "Hear the whole table". */
function vox(name, o = {}) {
  if (!SND.ctx || !SND.prefs.voice || !(sndHearsTable() || o.mine) || document.hidden || !SND.data || !SND.data.clips[name]) return;
  SND.q.push({ name, until: performance.now() + (o.stale || 4000) });
  if (SND.q.length > 3) SND.q.splice(0, SND.q.length - 3);
  sndTalk();
}
function sndTalk() {
  if (SND.talking || !SND.ctx) return;
  const it = SND.q.shift();
  if (!it) { sndLevels(); return; }
  if (performance.now() > it.until) { sndTalk(); return; }
  const id = SND.talking = ++SND.talkId;
  sndLevels();
  sndBuf(it.name).then(b => {
    const c = SND.ctx, done = () => { if (SND.talking !== id) return; SND.talking = 0; setTimeout(sndTalk, 160); };
    if (!b || !c || document.hidden) { done(); return; }
    const s = c.createBufferSource(); s.buffer = b; s.connect(SND.bus.voice); s.start();
    s.onended = done; setTimeout(done, b.duration * 1000 + 300);     // a hidden tab may never say it ended
  });
}
/* the city at night, on a loop under the table screen */
function sndAmb() {
  const c = SND.ctx; if (!c) return;
  const want = sndTable() && SND.prefs.amb && SND.prefs.vol > 0 && !!G.state && !document.hidden;
  if (want && !SND.amb) {
    const mark = SND.amb = { pending: true };
    sndBuf('amb_city').then(b => {
      if (!b || SND.amb !== mark) return;
      // start past the silence an MP3 encoder puts at the front, or the loop hiccups there
      const d = b.getChannelData(0), lim = Math.min(d.length, b.sampleRate * 0.3);
      let i = 0; while (i < lim && Math.abs(d[i]) < 1e-4) i++;
      const from = i / b.sampleRate, s = c.createBufferSource(), g = c.createGain();
      s.buffer = b; s.loop = true; s.loopStart = from; s.loopEnd = Math.min(b.duration, from + (SND.data.meta.amb_city || b.duration));
      g.gain.setValueAtTime(0.0001, c.currentTime); g.gain.linearRampToValueAtTime(1, c.currentTime + 3);
      s.connect(g); g.connect(SND.bus.amb); s.start(0, from);
      SND.amb = { s, g };
    });
  } else if (!want && SND.amb) {
    const a = SND.amb; SND.amb = null;
    if (a.s) { a.g.gain.cancelScheduledValues(c.currentTime); a.g.gain.setTargetAtTime(0, c.currentTime, 0.25); a.s.stop(c.currentTime + 1.5); }
  }
}
document.addEventListener('visibilitychange', () => { sndAmb(); if (document.hidden) SND.q = []; });

/* ---------- the moments, as the animations play them ---------- */
/* the dice machine: the reels whirr, stop one after the other, and the number is called as the second lands */
function sndRoll(ev, t1, t2) {
  if (!SND.ctx || !sndHearsTable()) return;
  const quick = !!ev.quick;
  sfx('reel_spin', { dur: t2 + 60, vol: quick ? 0.5 : 0.75, gap: 0 });
  sfx('reel_stop', { at: t1, detune: 90, gap: 0, vol: 0.8 });
  sfx('reel_stop', { at: t2, detune: 90, gap: 0 });
  if (quick) return;
  setTimeout(() => {
    if (ev.sum === 7) sfx('seven'); else if (ev.pays.length) sfx('payout', { vol: 0.75 });
    vox('v_sum_' + ev.sum, { stale: 2500 });
  }, t2 + 40);
}
/* the police arrive: siren, tape, and the dispatcher over the radio. A phone hears it only if it is its own block. */
function sndRaid(hex) {
  const st = G.state, me = sndMe(), h = GEO.hexes[hex];
  if (!SND.ctx || !st || !h) return;
  const hit = !!me && h.vs.some(v => st.buildings[v] && st.buildings[v].pid === me);
  if (!sndHearsTable() && !hit) return;
  sfx('siren', { vol: sndHearsTable() ? 0.85 : 0.6 });
  sfx('tape', { at: 420, vol: 0.8 });
  if (sndHearsTable()) setTimeout(() => vox(sndOne(['v_cop_1', 'v_cop_2', 'v_cop_3']), { stale: 5000 }), 700);
}
function sndPing() { sfx('your_turn'); buzz([16, 70, 16]); }
/* one of several lines, never the one it picked last time */
function sndOne(list) {
  const k = list[0]; let i = Math.floor(Math.random() * list.length);
  if (list.length > 1 && i === SND.pick[k]) i = (i + 1 + Math.floor(Math.random() * (list.length - 1))) % list.length;
  SND.pick[k] = i; return list[i];
}
/* The start sting melts into the city: the ambience drops away under the hit and swells back
   up as the sting fades, then settles. sndLevels leaves it alone until then. */
function sndMelt(at) {
  const c = SND.ctx; if (!c || !SND.bus.amb) return;
  const g = SND.bus.amb.gain, t = c.currentTime + (at || 0) / 1000;
  SND.melt = performance.now() + (at || 0) + 7500;
  g.cancelScheduledValues(c.currentTime);
  g.setTargetAtTime(SND_GAIN.amb * 0.15, t, 0.08);
  g.setTargetAtTime(SND_GAIN.amb * 1.35, t + 2.6, 0.9);
  g.setTargetAtTime(SND_GAIN.amb, t + 6, 1.2);
}

/* ---------- the moments, from the state ---------- */
function sndSig(st) {
  const b = st.buildings || {}, ks = Object.keys(b);
  return { room: st.room, v: st.v, phase: st.phase, step: st.step, turn: st.turnNo + ':' + st.turnIdx, place: st.placeIdx, round: st.round,
    act: activePid(st), seats: st.players.map(p => p.pid), streets: Object.keys(st.streets || {}).length,
    ops: ks.filter(k => b[k].k === 's').length, holds: ks.filter(k => b[k].k === 'c').length,
    offer: st.offer ? JSON.stringify([st.offer.from, st.offer.give, st.offer.want]) : '', from: st.offer ? st.offer.from : null,
    replies: st.offer ? Object.assign({}, st.offer.replies) : {}, pend: Object.keys(st.pend || {}),
    vp: st.players.reduce((m, p) => { m[p.pid] = vpOf(st, p.pid); return m; }, {}),
    hands: st.players.reduce((m, p) => { m[p.pid] = RES_ORDER.map(r => p.hand[r] || 0); return m; }, {}),
    police: st.board.police, dice: st.dice ? st.dice.join('') : '', rolls: JSON.stringify(st.rolls || {}), log0: Array.isArray(st.log) ? String(st.log[0] || '') : '' };
}
/* Called beside fxObserve at the top of both renderers. Dice, cards and the police are voiced by
   the animations themselves (sndRoll, fxFly, fxLanded, sndRaid) so they land on the right frame;
   everything else is heard from here. */
function sndObserve(st) {
  if (!st) { SND.sig = null; return; }
  const was = SND.sig;
  if (was && was.v === st.v && was.room === st.room) return;          // same state, just another render
  let now; try { now = sndSig(st); } catch (e) { return; }
  SND.sig = now;
  if (!SND.ctx) return;
  sndAmb();
  if (!was || was.room !== now.room || document.hidden) return;
  try { sndPlan(st, was, now); } catch (e) { console.error(e); }
}
function sndPlan(st, was, now) {
  const T = sndHearsTable(), me = sndMe(), total = h => (h || []).reduce((a, b) => a + b, 0);
  /* A roll that is about to be animated must not be given away: anything that follows from it
     (a tie, who places first, dropping cards on a seven) waits until the reels have stopped. */
  const turnRoll = now.phase === 'turn' && now.dice && (!was.dice || was.turn !== now.turn);
  const hold = !FX.on ? 0 : turnRoll ? 2150 : was.phase === 'rolloff' && now.rolls !== was.rolls ? 1350 : 0;
  const later = fn => (hold ? setTimeout(fn, hold) : fn());
  if (now.log0 !== was.log0 && /^Undid/.test(now.log0)) { if (T) sfx('undo'); return; }
  if (/^Back in the lobby/.test(now.log0)) return;

  if (now.phase === 'lobby' && was.phase === 'lobby' && T) {
    if (now.seats.some(id => !was.seats.includes(id))) sfx('join');
    else if (was.seats.some(id => !now.seats.includes(id))) sfx('leave');
  }
  if (was.phase === 'lobby' && now.phase === 'rolloff') { if (T) { sfx('start'); sndMelt(0); setTimeout(() => vox('v_start'), 1200); } if (me) sndPing(); }
  if (was.phase === 'rolloff' && now.phase === 'rolloff' && now.round > was.round) later(() => { if (T) vox('v_tie'); if (me && (st.contenders || []).includes(me)) sndPing(); });
  if (was.phase === 'rolloff' && now.phase === 'place' && T) later(() => vox('v_place'));
  if (was.phase === 'place' && now.phase === 'turn' && T) { sfx('start', { vol: 0.7, at: 450 }); sndMelt(450); vox('v_open'); }

  // pieces going down: the table always hears it, a phone when it put them there
  if (T || (me && was.act === me)) {
    const also = now.ops > was.ops || now.holds > was.holds;
    if (now.holds > was.holds) { sfx('build_holding'); if (T) vox('v_tower', { stale: 3000 }); }
    else if (now.ops > was.ops) {
      sfx('build_op');
      // and a line with it, a different one each time; in set-up the announcer is already calling every placement
      if (T && now.phase === 'turn') setTimeout(() => vox(sndOne(['v_op_1', 'v_op_2', 'v_op_3', 'v_op_4']), { stale: 3000 }), 600);
    }
    if (now.streets > was.streets) sfx('build_street', { at: also ? 500 : 0 });
  }

  // whose move it is now
  const moved = (now.phase === 'place' && (was.phase !== 'place' || was.place !== now.place)) ||
    (now.phase === 'turn' && (was.phase !== 'turn' || was.turn !== now.turn));
  if (moved && now.act) {
    const p = playerOf(st, now.act);
    later(() => {
      // the first turn of the game already has the city opening under it
      if (T && p) { if (was.phase === 'turn') sfx('turn', { vol: 0.7 }); vox('v_up_' + p.color, { stale: 5000 }); }
      if (me && me === now.act) sndPing();
    });
  }

  // a seven: dropping cards, and the steal after the police move
  if (now.step === 'discard' && was.step !== 'discard') later(() => { if (T) vox('v_discard', { stale: 6000 }); if (me && now.pend.includes(me)) sndPing(); });
  if (was.step === 'discard') { const out = was.pend.filter(id => !now.pend.includes(id)); if (out.length && (T || out.includes(me))) sfx('discard'); }
  if (was.step === 'steal' && now.step !== 'steal' && now.phase === 'turn' && was.turn === now.turn) {
    const lost = Object.keys(now.hands).filter(id => total(now.hands[id]) < total(was.hands[id]));
    // the card goes, then the thief's taunt: on the table, and on the phone of whoever was robbed
    const taunt = () => setTimeout(() => vox(sndOne(['v_taunt_1', 'v_taunt_2', 'v_taunt_3']), { stale: 3000, mine: true }), 250);
    if (T) { sfx('steal'); taunt(); } else if (me && (me === was.act || lost.includes(me))) { sfx('steal'); if (lost.includes(me)) taunt(); }
  }

  // trading
  const changed = Object.keys(now.hands).filter(id => String(now.hands[id]) !== String(was.hands[id] || ''));
  if (now.offer && now.offer !== was.offer) {
    if (T) { sfx('trade_offer'); vox('v_offer', { stale: 3000 }); } else if (me && me !== now.from) { sfx('trade_offer'); buzz([12, 50, 12]); }
  } else if (now.offer && now.offer === was.offer && me && me === now.from) {
    Object.keys(now.replies).forEach(id => { if (!(id in was.replies)) sfx(now.replies[id] ? 'trade_yes' : 'trade_no', { cat: 'fx', gap: 0 }); });
  }
  if (was.offer && !now.offer && changed.length >= 2) {
    // the cork, then a line once the fizz is going
    if (T) { sfx('deal'); setTimeout(() => vox(sndOne(['v_deal', 'v_deal_2', 'v_deal_3', 'v_deal_4']), { stale: 3000 }), 700); }
    else if (me && changed.includes(me)) sfx('deal');
  }
  // a trade with the bank: one hand down 2 to 4 of one thing and up 1 of another, and nothing built
  if (now.phase === 'turn' && changed.length === 1 && changed[0] === was.act && (T || me === was.act) &&
      now.streets === was.streets && now.ops === was.ops && now.holds === was.holds) {
    const d = now.hands[was.act].map((n, i) => n - ((was.hands[was.act] || [])[i] || 0)), down = d.filter(x => x < 0), up = d.filter(x => x > 0);
    if (down.length === 1 && down[0] <= -2 && down[0] >= -4 && up.length === 1 && up[0] === 1) sfx('bank');
  }

  // one move from the top, and the top
  if (now.phase === 'turn' && T && Object.keys(now.vp).some(id => now.vp[id] === WIN_VP - 1 && (was.vp[id] || 0) < WIN_VP - 1)) {
    sfx('tension', { at: 400 }); vox('v_nine', { stale: 5000 });
  }
  if (now.phase === 'over' && was.phase !== 'over') {
    const p = playerOf(st, st.win);
    if (T || (me && me === st.win)) sfx('win', { at: 450 });
    if (T && p) setTimeout(() => vox('v_win_' + p.color, { stale: 6000 }), 1600);
  }

  // no animation to hang the dice, cards and police on (reduced motion): the result, a card, the siren
  if (!FX.on) {
    if (T && now.phase === 'turn' && st.dice && (!was.dice || was.turn !== now.turn)) {
      const sum = st.dice[0] + st.dice[1];
      sfx('reel_stop'); if (sum === 7) sfx('seven'); vox('v_sum_' + sum, { stale: 2500 });
    }
    const up = Object.keys(now.hands).filter(id => total(now.hands[id]) > total(was.hands[id]));
    if (up.length && (T || up.includes(me))) sfx('card_land', { at: 250 });
    if (now.phase === 'turn' && was.police !== now.police && now.police !== policeHome(st.board)) sndRaid(now.police);
  }
}

/* ---------- taps ---------- */
document.addEventListener('click', ev => {
  if (!SND.ctx) return;
  const t = ev.target.closest && ev.target.closest('button, a.btn, [role=switch]');
  if (!t) return;
  sfx(t.matches('.sechead, .keybtn, .sndbtn') ? 'ui_fold'
    : t.matches('.btn.big, [data-p=join], [data-p=offsend], [data-h=start], [data-h=confirm], [data-h=rollturn], [data-h=endturn]') ? 'ui_confirm' : 'ui_tap', { detune: 70, gap: 30 });
}, true);
// a disabled button is a "not yet": say so, quietly (browsers that send nothing to a disabled button stay silent)
document.addEventListener('pointerdown', ev => { if (SND.ctx && ev.target.closest && ev.target.closest('button:disabled')) sfx('ui_deny', { gap: 300 }); }, true);

/* ---------- the speaker button and its panel ---------- */
const SPK = on => '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path d="M3.5 9.2h3.8L12 5.5v13l-4.7-3.7H3.5z" fill="currentColor"/>' +
  (on ? '<path d="M15.5 9a4.2 4.2 0 0 1 0 6M18.2 6.4a8 8 0 0 1 0 11.2" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"/>'
    : '<path d="M15.8 9.6l4.6 4.8M20.4 9.6l-4.6 4.8" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"/>') + '</svg>';
const sndBtnHTML = () => `<button type="button" class="sndbtn" data-snd="open" aria-expanded="${SND.open}" aria-controls="snd-panel" aria-label="Sound: ${sndAny() ? 'on' : 'off'}" title="Sound">${SPK(sndAny())}</button>`;
function sndPanelHTML() {
  const p = SND.prefs, table = sndTable();
  const row = (k, name, what) => `<button type="button" class="sndrow" data-snd="${k}" role="switch" aria-checked="${!!p[k]}"><span><b>${name}</b><small>${what}</small></span><i class="sndsw" aria-hidden="true"></i></button>`;
  return `<h2>Sound on this ${table ? 'screen' : 'phone'}</h2>` +
    row('fx', 'Effects', table ? 'Dice, cards, the police, building, buttons' : 'Your turn, your cards, offers, a taunt when you are robbed, buttons') +
    (table ? '' : row('all', 'Hear the whole table', 'The dice, the police and the announcer here too, for playing from somewhere else')) +
    (table || p.all ? row('voice', 'Announcer', 'Calls each roll and whose turn it is') : '') +
    (table ? row('amb', 'City at night', 'Traffic and rain under the game') : '') +
    `<label class="sndvol">Volume<input type="range" min="0" max="100" step="5" value="${p.vol}" data-snd="vol" aria-label="Volume"></label>`;
}
function sndPanel(open) {
  SND.open = open;
  let el = document.getElementById('snd-panel');
  if (!open) { if (el) el.remove(); }
  else {
    if (!el) { el = document.createElement('div'); el.id = 'snd-panel'; el.className = 'sndpanel'; el.setAttribute('role', 'group'); el.setAttribute('aria-label', 'Sound'); document.body.appendChild(el); }
    el.innerHTML = sndPanelHTML();
    const b = document.querySelector('.sndbtn'), r = b && b.getBoundingClientRect();
    if (r && r.bottom > 0) el.style.top = Math.round(r.bottom + 8) + 'px';
  }
  document.querySelectorAll('.sndbtn').forEach(b => { b.setAttribute('aria-expanded', String(open)); b.setAttribute('aria-label', 'Sound: ' + (sndAny() ? 'on' : 'off')); b.innerHTML = SPK(sndAny()); });
}
function sndSave() { store('rtcity.snd', SND.prefs); sndUnlock(); sndLevels(); sndAmb(); sndPanel(SND.open); }
document.addEventListener('click', ev => {
  const t = ev.target.closest && ev.target.closest('[data-snd]');
  if (!t) { if (SND.open && !(ev.target.closest && ev.target.closest('#snd-panel'))) sndPanel(false); return; }
  const k = t.dataset.snd;
  if (k === 'open') { sndPanel(!SND.open); return; }
  if (k === 'vol' || !(k in SND_DEFAULT)) return;
  SND.prefs[k] = !SND.prefs[k]; sndSave();
  if (SND.prefs[k] && k === 'all') sndWarm();                          // the announcer's lines were skipped on a phone until now
  // let them hear what they just turned on
  if (SND.prefs[k] && k === 'voice') vox('v_place', { stale: 1500 });
  if (SND.prefs[k] && k === 'fx') sfx('ui_confirm');
});
document.addEventListener('input', ev => { if (ev.target.dataset && ev.target.dataset.snd === 'vol') { SND.prefs.vol = +ev.target.value || 0; sndUnlock(); sndLevels(); sndAmb(); } });
document.addEventListener('change', ev => { if (ev.target.dataset && ev.target.dataset.snd === 'vol') { sndSave(); sfx('card_land', { gap: 0 }); } });
document.addEventListener('keydown', ev => { if (ev.key === 'Escape' && SND.open) { sndPanel(false); const b = document.querySelector('.sndbtn'); if (b) b.focus(); } });

"""

EDITS = [
    # styles, at the end of the page's own stylesheet
    ("</style>\n</head>", CSS.strip("\n") + "\n</style>\n</head>"),
    # the engine, just before the delegated events
    ("/* =====================================================================\n   Events (delegated)",
     JS + "/* =====================================================================\n   Events (delegated)"),
    # both renderers hear the state as the animations see it
    ("  fxObserve(st);\n  if (!$('#h-banner')) renderHostShell();", "  fxObserve(st); sndObserve(st);\n  if (!$('#h-banner')) renderHostShell();"),
    ("  fxObserve(st);\n  if (!$('#p-main')) {", "  fxObserve(st); sndObserve(st);\n  if (!$('#p-main')) {"),
    # the speaker button in the table's header and the phone's
    ("${hostKeyHTML()}<span id=\"h-status\" class=\"pill\">", "${hostKeyHTML()}${sndBtnHTML()}<span id=\"h-status\" class=\"pill\">"),
    ("<span id=\"p-key\" style=\"display:contents\"></span></header>", "<span id=\"p-key\" style=\"display:contents\"></span>${sndBtnHTML()}</header>"),
    # the animations call their sounds on the frame they happen
    ("  const t1 = quick ? 800 : 1150, t2 = quick ? 1200 : 1950;\n", "  const t1 = quick ? 800 : 1150, t2 = quick ? 1200 : 1950;\n  sndRoll(ev, t1, t2);\n"),
    ("function fxRaid(ev) {\n", "function fxRaid(ev) {\n  sndRaid(ev.hex);\n"),
    ("      anim.onfinish = land; anim.oncancel = land;\n",
     "      anim.onfinish = land; anim.oncancel = land;\n      if (i < 8) sfx('card_whoosh', { at: i * 95 + 120, gap: 0, detune: 60, vol: 0.7 - i * 0.07 });\n"),
    ("    buzz(10);\n  } else if (f.to.pid) {", "    buzz(10); sfx('card_land', { detune: 60 });\n  } else if (f.to.pid) {"),
    ("    if (b) { b.classList.remove('bump'); void b.offsetWidth; b.classList.add('bump'); }\n  }\n}",
     "    if (b) { b.classList.remove('bump'); void b.offsetWidth; b.classList.add('bump'); }\n    sfx('card_land', { detune: 60, vol: 0.8 });\n  }\n}"),
    # picking a spot, or a block for the police
    ("  if (WATCH) return false;\n  if (joinRoom) renderPlayer(); else renderHost();", "  if (WATCH) return false;\n  sfx('ui_pick', { detune: 60 });\n  if (joinRoom) renderPlayer(); else renderHost();"),
    # (anchored on the lines before the choice, which the card build rewrote; policeBlocks only exists there)
    ("    const i = near !== null ? near : hex ? +hex.dataset.hex : null;\n    if (i !== null) {\n",
     "    const i = near !== null ? near : hex ? +hex.dataset.hex : null;\n    if (i !== null) {\n"
     "      sfx(i !== G.state.board.police && (typeof policeBlocks !== 'function' || policeBlocks(G.state, activePid(G.state)).includes(i)) ? 'ui_pick' : 'ui_deny', { detune: 60 });\n"),
]

path = sys.argv[1]
s = open(path, encoding="utf-8").read()
if "function sndObserve" in s: sys.exit("%s already has the sound engine" % path)
for old, new in EDITS:
    n = s.count(old)
    if n != 1: sys.exit("anchor found %d times, expected once:\n%s" % (n, old[:160]))
    s = s.replace(old, new)
open(path, "w", encoding="utf-8").write(s)
print("sound engine landed in %s (%d edits)" % (path, len(EDITS)))
