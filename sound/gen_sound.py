#!/usr/bin/env python3
"""Generate Run the City's sound with the ElevenLabs API: effects, UI sounds, the city
ambience, the announcer and the police dispatcher.

Reads ELEVENLABS_API_KEY from the environment (never hard-code it). Usage:
    set -a; . ./.env; set +a; python3 sound/gen_sound.py [name ...]
With no names it generates everything that is not already in sound/raw/, then
processes every raw file into sound/web/ (trimmed, levelled, mono MP3).
    python3 sound/gen_sound.py --process     # only re-run the processing
    python3 sound/gen_sound.py --force NAME  # throw away NAME's raw take and make a new one
"""
import json, os, subprocess, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
RAW, WEB = os.path.join(HERE, "raw"), os.path.join(HERE, "web")
API = "https://api.elevenlabs.io/v1"

ANNOUNCER = "N2lVS1w4EtoT3dr4eOWO"   # Callum: husky, gravelly, an edge to it. The city's fixer calling the game.
DISPATCH = "EXAVITQu4vr4xnSDxMaL"    # Sarah: level and professional, then pushed through a police radio.
TTS_MODEL = "eleven_multilingual_v2" # steadier than v3 on one-word lines, which most of these are
SFX_MODEL = "eleven_text_to_sound_v2"

# ---------------------------------------------------------------- effects
# kind sets how a file is levelled and encoded (see LEVEL). d = seconds asked for,
# p = prompt influence (higher sticks closer to the words, lower is more varied).
DRY = " Close-up, dry studio recording, no music, no voices."
# Impacts come back from the generator almost all below 150 Hz, which a phone cannot play at all:
# keep the thud and add a saturated copy of it (220 Hz-3 kHz), the crunch a small speaker can carry.
PUNCHY = ("highpass=f=45,asplit=2[dry][sat];[sat]lowpass=f=260,volume=20dB,asoftclip=type=tanh,"
          "highpass=f=220,lowpass=f=3000,volume=%sdB[h];[dry][h]amix=inputs=2:normalize=0")
SFX = {
    # the dice machine: a one-armed bandit whose two reels stop one after the other
    # digital and kept low (asked for 2026-09-23): the reels are an electronic flicker, not a one-armed bandit
    # generated as a loop, so the ticking runs evenly the whole two seconds instead of bursting and dying
    "reel_spin":  dict(kind="fx", lu=-27, d=2.2, p=0.65, loop=True, post="lowpass=f=6500",
        text="Digital slot machine reels spinning: a continuous, steady stream of soft rapid electronic ticks, evenly spaced, over a light synthetic whir, the same all the way through, clean video game sound. No bells, no mechanical parts, no music."),
    "reel_stop":  dict(kind="fx", lu=-26, d=0.5, p=0.7, text="A soft digital reel stop: one short clean electronic click with a tiny low blip underneath, like a digital counter locking into place, interface sound. No mechanical parts, no music."),
    "payout":     dict(kind="fx", d=1.2, p=0.5, text="Short bright casino payout chime: three quick rising bell tones with a soft electric shimmer, clean, no voice."),
    # a bass drone rather than a stinger (asked for 2026-09-23); the growl on top is what a phone speaker can actually play
    # the sub-bass alone is nearly silent on a phone or laptop, so a saturated copy adds its harmonics
    # (200 Hz-2 kHz) back in: the ear hears the growl and fills in the low note
    "seven":      dict(kind="fx", lu=-20, d=3.5, p=0.65,
        post="highpass=f=35,asplit=2[dry][sat];[sat]lowpass=f=180,volume=24dB,asoftclip=type=tanh,highpass=f=200,lowpass=f=2000,volume=1dB[h];[dry][h]amix=inputs=2:normalize=0",
        text="Ominous deep bass drone: one sustained low synth bassline note that swells in and slowly fades out, with a gritty low growl in its upper harmonics, dark and tense. No melody, no drums, no hits, no siren."),
    # cards in the air
    # soft and airy, not sharp or metallic (asked for 2026-09-23): the prompt does most of it, and the
    # processing takes the hiss off the top and the edge off the attack (post, fade_in)
    "card_whoosh": dict(kind="fx", d=0.6, p=0.75, post="highpass=f=150,lowpass=f=5500,lowpass=f=5500", fade_in=0.04, unring=True,
        text="A short gentle gust of air, like a soft breath blown past a microphone: a smooth airy swish, noise only. No tone, no whistle, no ring, no click." + DRY),
    "card_land":  dict(kind="fx", d=0.5, p=0.7, post="lowpass=f=6000,lowpass=f=6000", unring=True,
        text="A single playing card landing softly on a thick felt table: one dull, muted papery tap, warm and soft, no metallic ring, no click, no rattle." + DRY),
    # the police
    "siren":      dict(kind="fx", d=1.8, p=0.6, text="American police car siren giving a short yelp and two quick whoops, on a city street at night, slightly distant, with street reverb."),
    "tape":       dict(kind="fx", d=1.0, p=0.6, text="Plastic police barrier tape pulled fast off a roll and stretched tight: crinkly plastic unspooling." + DRY),
    "squelch_in": dict(kind="fx", d=0.5, p=0.7, text="Police radio squelch: a short burst of static then a click as the channel opens, walkie-talkie."),
    "squelch_out": dict(kind="fx", d=0.5, p=0.7, text="Walkie-talkie transmission ending: a click and a short chirp of static, police radio."),
    # a card taken, not a pocket picked; the taunt that follows it is a voice line (v_taunt_*)
    "steal":      dict(kind="fx", d=0.6, p=0.7, text="A single playing card snatched out of someone's hand: a quick crisp card slide and a sharp flick as it is pulled away." + DRY),
    # digital, not paper (asked for 2026-09-23)
    "discard":    dict(kind="fx", d=0.8, p=0.65, text="A digital discard: a quick descending electronic swoosh with a few soft glitchy blips, like cards dissolving off a screen, clean interface sound. No paper, no music."),
    # building
    "build_street": dict(kind="fx", d=1.2, p=0.5, text="Road crew laying a street at night: a short burst of a jackhammer, then the heavy rumble of a road roller, brief."),
    # asked 2026-09-23: a system coming online, and the announcer says something different each time (v_op_*)
    "build_op":   dict(kind="fx", d=1.6, p=0.6, text="A futuristic system start-up sound: a quick rising digital power-up sweep, soft electronic boot chimes and a warm hum settling in, like a computer console coming online. Clean interface sound, no voice."),
    "build_holding": dict(kind="fx", d=2.8, p=0.55, text="Skyscraper construction site: heavy steel beams clanging into place, a pneumatic rivet gun bursting, a tower crane motor hauling, ending on one huge deep steel boom, big and cinematic."),
    # trading
    "trade_offer": dict(kind="fx", d=0.6, p=0.6, text="Short notification chime from a retro flip phone: two soft electronic beeps, clean, no voice."),
    "trade_yes":  dict(kind="ui", d=0.7, p=0.7, text="A single bright positive notification ding: one clean pleasant bell tone with a short sparkle, cheerful, interface sound."),
    # mid register on purpose: it plays on the phone of whoever made the offer, and a phone cannot play a low synth
    "trade_no":   dict(kind="ui", d=0.9, p=0.7, post="highpass=f=120",
        text="A short bum-bamm fail sound played on a muted trombone in its middle register: two descending notes, the second lower and held a little longer, soft and comical, clear on a small phone speaker."),
    # a celebration, then one of the v_deal lines
    "deal":       dict(kind="fx", d=1.8, p=0.6, text="Celebration: a champagne bottle cork pops loudly, the champagne fizzes and pours, and a cash register rings cha-ching."),
    "bank":       dict(kind="fx", d=1.2, p=0.7, text="An old cash register at a cashier's till: a quick ka-ching bell, then the cash drawer sliding shut with a solid thunk." + DRY),
    # turns and the game
    "turn":       dict(kind="fx", d=1.5, p=0.5, text="Smooth film-noir jazz sting: a muted trumpet plays a short sly two-note phrase over one brushed snare tap, very short, dry."),
    "your_turn":  dict(kind="ui", d=0.8, p=0.6, text="Smooth two-note synth chime notification, warm neon tone, rising, clean and gentle, interface sound."),
    "join":       dict(kind="fx", d=0.8, p=0.7, text="A warm positive arrival chime: a bright two-note rising ding, friendly and welcoming, clean interface sound."),
    "leave":      dict(kind="fx", d=1.0, p=0.7, text="A soft log-out sound: a short descending three-note digital chime that powers down gently, clean interface sound."),
    # a hyped sting that dissolves into the city: the page lets the ambience come back up under its tail
    "start":      dict(kind="fx", d=6, p=0.55, fade_out=1.5, text="A very short hyped music intro: a punchy trap beat with a booming 808 bass, a snare roll and a bright synth stab, big energy for three seconds, then it dissolves with a long reverb into distant night city ambience, traffic and light rain."),
    "tension":    dict(kind="fx", d=2.0, p=0.5, text="Suspense sting: a low pulsing heartbeat bass hit under a rising high string swell, short, tense, cinematic."),
    "win":        dict(kind="fx", d=4.5, p=0.5, text="Triumphant jazzy big band brass fanfare ending on a cymbal crash, gangster movie victory, celebratory, short."),
    "undo":       dict(kind="fx", d=0.8, p=0.6, text="A cassette tape rewinding quickly: a short high-pitched mechanical squeal and whirr, ending in a click." + DRY),
    # interface
    "ui_tap":     dict(kind="ui", d=0.5, p=0.7, text="A very soft short click of a small plastic button, subtle interface tap, clean." + DRY),
    # the most common tap there is (every section, the key, the speaker): asked shorter and softer 2026-09-24,
    # so it is capped at 0.15 s and levelled well under the other taps; the page plays it at full volume
    "ui_fold":    dict(kind="ui", lu=-36, d=0.5, p=0.75, post="highpass=f=250,lowpass=f=5000,atrim=0:0.15", fade_out=0.06,
        text="A tiny soft tick of a paper card flipping over: very short and quiet, a subtle muted interface click with a hint of paper, nothing else." + DRY),
    "ui_deny":    dict(kind="ui", d=0.5, p=0.6, text="A soft short muted double buzz, gentle low error interface sound, clean." + DRY),
    "ui_pick":    dict(kind="ui", d=0.5, p=0.7, text="A tiny glassy blip, soft high interface select sound, clean." + DRY),
    "ui_confirm": dict(kind="ui", d=0.5, p=0.7, text="A satisfying firm interface confirm click with a soft low thunk, clean." + DRY),
    # ---- skills and talents (added 2026-09-23, with the card system) ----
    # the market and the crate an upgrade draws from
    "card_buy":   dict(kind="fx", d=0.9, p=0.65, text="A quick deal at a market stall: a few banknotes counted into a hand, then a playing card slid briskly across a wooden counter." + DRY),
    "crate":      dict(kind="fx", d=0.7, p=0.65, text="A small wooden crate rattling and shaking as something inside knocks about, one short burst." + DRY),
    "reveal":     dict(kind="fx", d=1.2, p=0.6, text="A card flipped over to reveal a prize: a crisp card flip followed by a bright magical shimmer and a sparkle chime."),
    "reveal_big": dict(kind="fx", d=2.2, p=0.55, text="A legendary prize revealed: a card flips, then a huge glittering jackpot shimmer with a rising angelic choir swell and a deep boom, triumphant."),
    # a card played: the slap, then the card's own flourish (Rewind borrows the tape rewind from undo)
    "card_play":  dict(post=PUNCHY % 0, kind="fx", d=0.7, p=0.7, text="A playing card slammed face up onto a table with force: a sharp whoosh and a heavy slap." + DRY),
    "tipoff":     dict(kind="fx", d=1.4, p=0.65, text="An old payphone: a coin drops in, a few rotary dial clicks, then the receiver is slammed back on the hook." + DRY),
    "lucky":      dict(kind="fx", d=1.3, p=0.6, text="A lucky jackpot chime: sparkling bells tumbling upward with a shower of coins, bright and magical."),
    "legend":     dict(fade_out=0.4, kind="fx", d=2.2, p=0.55, text="A crowd bursts into cheers and applause with a short triumphant brass hit, like a hometown hero walking in."),
    "silver":     dict(kind="fx", d=1.4, p=0.6, text="A smooth sly saxophone lick: a short charming jazz phrase, like a smooth talker winning someone over."),
    "connections": dict(fade_out=0.3, kind="fx", d=1.0, p=0.65, text="A Rolodex spun and one card flicked out, then a telephone line clicking through." + DRY),
    "shakedown":  dict(kind="fx", d=1.2, p=0.65, text="Intimidation: a fist pounds a wooden table twice, hard, then knuckles crack." + DRY),
    "roadcrew":   dict(fade_out=0.45, kind="fx", d=1.4, p=0.6, text="A road crew rolls out: a foreman's sharp whistle, then a diesel truck engine starting up and revving."),
    "paidoff":    dict(kind="fx", d=1.0, p=0.65, text="A thick envelope of banknotes slapped down on a desk and slid across, then a drawer quietly closing." + DRY),
    # the street fight
    "fight_bell": dict(kind="fx", d=1.8, p=0.6, text="A boxing ring bell rings three times, ding ding ding, and a rowdy crowd roars."),
    "punch":      dict(post=PUNCHY % 2, kind="fx", d=0.5, p=0.7, text="A single solid punch landing on a body: a quick whoosh then a meaty thud, cinematic fight sound effect." + DRY),
    "punch_big":  dict(post=PUNCHY % 2, kind="fx", d=0.8, p=0.65, text="A massive haymaker punch landing: a big whoosh then a crunching heavy impact with a deep boom, cinematic fight sound effect." + DRY),
    "whiff":      dict(post="highpass=f=250", kind="fx", d=0.5, p=0.7, text="A punch that misses: one fast swoosh of a fist cutting through empty air." + DRY),
    "block":      dict(post=PUNCHY % 7, kind="fx", d=0.5, p=0.7, text="A punch blocked hard: one solid dull thud against a raised guard." + DRY),
    "patch":      dict(kind="fx", d=0.9, p=0.65, text="Patching up a wound: a strip of medical tape ripped off a roll and slapped on, then a soft healing chime." + DRY),
    "hype":       dict(kind="fx", d=1.2, p=0.6, text="A crowd hypes up a fighter: a stadium air horn blast and a rising roar."),
    "pull":       dict(kind="fx", d=1.0, p=0.65, text="Strings pulled behind the scenes: a quick mysterious shimmer and a low whoosh, like a shield going up."),
    "backup":     dict(fade_out=0.35, kind="fx", d=1.4, p=0.6, text="Backup arrives: car doors slamming and several people running in fast on pavement."),
    "backoff":    dict(post=PUNCHY % 0, kind="fx", d=1.0, p=0.65, text="Someone backs off and runs away: quick footsteps hurrying off on wet pavement, fading into the distance."),
    "ko":         dict(fade_out=0.5, kind="fx", d=2.2, p=0.55, text="A knockout: a heavy body hits the floor, the boxing bell clangs rapidly, and the crowd erupts in a huge roar."),
    "fight_end":  dict(kind="fx", d=1.8, p=0.6, text="A fight ends: the boxing bell rings twice and the crowd cheers and applauds."),
    # ---- turf war (release 5, 2026-09-26): turf won and lost (the owner's phone and the table), a building knocked down
    # the first prompt gave only hiss above 5 kHz (small 0.1): nothing a phone can play, so the power-up is asked for warm and low
    "turf_on":    dict(fade_out=0.3, kind="fx", d=1.6, p=0.65, text="A warm power-up swell: a deep electric hum rising smoothly in pitch into a bright glowing chord, like a whole city block of neon lighting up at once, ending on a soft clean chime. No voices."),
    "turf_off":   dict(fade_out=0.35, kind="fx", d=1.4, p=0.6, text="Neon lights shorting out: a crackle, a fizzing spark, and the electric hum dying away to silence. No music, no voices."),
    "crumble":    dict(fade_out=0.5, kind="fx", d=2.0, p=0.55, text="A small building being knocked down: timber cracking, bricks tumbling, a window shattering, then dust settling. No music, no voices."),
    # ---- crashes in the traffic (added 2026-09-24): scenery, heard only from the table ----
    # a driver who has just seen it, too late; then the hit, and the fuel going up a moment later
    "crash_skid": dict(kind="fx", d=1.1, p=0.7, post="highpass=f=180", fade_out=0.15,
        text="Car tyres screeching hard on asphalt as a driver slams on the brakes: one sharp, loud, high skid squeal, about a second long, on a city street at night. No crash, no music."),
    "crash_hit":  dict(post=PUNCHY % 2, fade_out=0.35, kind="fx", d=1.8, p=0.65,
        text="Two cars smash into each other at speed: one violent crunch of twisting metal and shattering glass with a heavy thud, then broken glass and small debris tinkling onto the road. No explosion, no music."),
    "crash_boom": dict(post=PUNCHY % 1, fade_out=0.9, kind="fx", d=3.5, p=0.6,
        text="A crashed car's fuel tank explodes: a big deep booming explosion with a fiery whoosh, burning debris clattering down onto the street, then flames crackling. Cinematic, no music."),
    # a car piling into the wreck: smaller, no fire
    "crash_bump": dict(post=PUNCHY % 3, fade_out=0.2, kind="fx", d=0.9, p=0.7,
        text="A car rear-ends a wrecked car: one short hard crunch of bending metal and a little broken glass falling." + DRY),
    # somebody stuck behind it
    "horn_1":     dict(kind="fx", d=0.9, p=0.7, fade_out=0.1,
        text="An annoyed driver stuck in traffic honks a car horn twice: two short sharp beeps of an ordinary car horn, city street at night. No music."),
    "horn_2":     dict(kind="fx", d=1.4, p=0.7, fade_out=0.15,
        text="An impatient driver leans on the car horn: one long angry honk of an ordinary car horn, about a second, city street at night. No music."),
    # ---- the lights coming on (release 1, 2026-09-26): set-up is done, the plain map goes dark and the city
    # powers up block by block; this runs under it and melts into amb_city, which fades in at the same time ----
    # take 4 of the second prompt: a steady sweep from 170 Hz up through the middle over four seconds, as the blocks
    # light; the top is taken down 6 dB so the whine it ends on stays soft
    "lights_on":  dict(kind="fx", lu=-23, d=5.0, p=0.7, fade_in=0.3, fade_out=1.2, post="highshelf=f=4000:g=-6",
        text="Power coming back on across a city at night: a big electric power-up sweep that rises slowly in pitch like generators spinning up, a warm mid-range electric whine swelling louder, soft clicks and buzzing as rows of lights flicker on one after another, then it settles into a calm steady hum. Cinematic sci-fi power-up. No music, no voices, no explosions, no static noise."),
    # the city at night, under everything on the table screen
    "amb_city":   dict(kind="amb", d=20, p=0.4, loop=True, text="Night city ambience heard from a rooftop: a steady distant traffic hum, the occasional far-off car horn, a faint distant siren, light rain drizzle, a soft electric neon buzz. No music, no voices."),
    # ---- pace (release 2, 2026-09-26): the turn clock and the standings ----
    # the room hears the last ten seconds go (the table screen, one tick a second), and the phone whose time it
    # is beeps the last three; then the buzzer. A hurry-up's ten seconds start with a stopwatch.
    # the take ticks four times in its half second: only the first, once a second, is a clock
    "clock_tick": dict(kind="fx", d=0.5, p=0.75, post="atrim=0:0.09", fade_out=0.03,
        text="A single crisp tick of a mechanical stopwatch: one short dry click, clean, close-up." + DRY),
    "clock_beep": dict(kind="fx", d=0.5, p=0.75, post="atrim=0:0.26", fade_out=0.05,
        text="One short clean electronic countdown beep in a mid-high pitch, like a digital timer's last seconds: a single pure tone, interface sound." + DRY),
    "time_up":    dict(kind="fx", d=1.2, p=0.7, fade_out=0.1,
        text="A game show time's-up buzzer: one short loud harsh electronic buzz, about a second long, then silence. No music, no voices."),
    "hurry_start": dict(kind="fx", d=1.6, p=0.6, fade_out=0.2,
        text="A digital alarm going off: four fast urgent beeps climbing in pitch, mid-range electronic tones like a countdown warning on a game show, clean interface sound. No music, no voices."),
    # the standings card sliding onto the table's board
    "score_sting": dict(kind="fx", d=1.4, p=0.6, fade_out=0.25,
        text="A short scoreboard update sting for a sports broadcast: a quick electric flicker, then two bright rising synth-brass notes in the middle register, punchy and clean, like a neon scoreboard lighting up. No voices."),
    # ---- trash talk (release 3, 2026-09-26): a sound bite with each sticker that flies from a seat on the table
    # screen (e_*, the room hears them), the whisper arriving on its one phone, and the splats landing on the
    # phone of the player whose turn it is (s_*, that phone and the table). Our own bites, short, never a meme clip.
    "e_cheer":    dict(kind="fx", d=1.5, p=0.6, fade_out=0.3,
        text="A small excited crowd cheering and whooping for a second, a few people at a party, bright and happy, fading quickly. No music."),
    "e_boo":      dict(kind="fx", d=1.5, p=0.6, fade_out=0.3,
        text="A small crowd booing for a second, a few people at a party going booo, playful and theatrical, fading quickly. No music."),
    "e_lol":      dict(kind="fx", d=1.4, p=0.55, fade_out=0.2,
        text="A cartoon mocking laugh: a quick high teasing hee-hee-hee ha-ha from a comedy character, playful, one voice, short. No music, no words."),
    # no take was a slow clap (the first was one clap, four more were steady applause), so raw/e_clap.mp3 is composed
    # from the first take's one clean clap (raw/_prev/e_clap.mp3, 0.50-0.95 s): four of it, each a little lower and
    # quieter, the gaps growing (0.2, 0.24, 0.3 s), like trade_no. --force would replace it with a generated take.
    "e_clap":     dict(kind="fx", d=2.4, p=0.8, fade_out=0.2,
        text="Slow sarcastic applause from one person: clap... clap... clap... clap. Four separate loud hand claps, half a second apart, in a quiet room, nothing between them." + DRY),
    "e_crickets": dict(kind="fx", d=2.0, p=0.7, fade_in=0.1, fade_out=0.4,
        text="Awkward silence: a few crickets chirping alone in a quiet empty room at night, nothing else. No music, no voices."),
    "e_rain":     dict(kind="fx", d=1.4, p=0.6, fade_out=0.2,
        text="Making it rain: a stack of paper banknotes riffled fast and thrown into the air, notes fluttering down, with a bright cash register ka-ching at the start. No music, no voices."),
    "e_fire":     dict(kind="fx", d=1.2, p=0.6, fade_out=0.3,
        text="A big whoosh of flame bursting up, a quick fiery roar that crackles and dies away. No music, no voices."),
    "e_sweat":    dict(kind="fx", d=1.0, p=0.6, fade_out=0.15,
        text="A nervous cartoon gulp: one loud comedic swallow, a big gulp sound effect from an animated cartoon." + DRY),
    "e_cry":      dict(kind="fx", d=2.0, p=0.65, fade_out=0.3,
        text="A tiny sad violin playing three short mournful notes, thin and melodramatic, a comedy sad violin, solo. No voices."),
    "e_micdrop":  dict(kind="fx", d=1.6, p=0.65, fade_out=0.4,
        text="A microphone dropped on a wooden stage: a heavy hollow thud through a PA speaker with a short boom and a quick burst of feedback whine." + " No music, no voices."),
    "whisper":    dict(kind="fx", d=0.8, p=0.7, fade_in=0.03, fade_out=0.15, post="highpass=f=150,lowpass=f=6000",
        text="A folded paper note slid quickly across a table with a soft breathy psst: a short gentle paper swish and a soft whispered hiss, intimate and close." + DRY),
    "s_tag":      dict(kind="fx", d=1.0, p=0.7, fade_out=0.15,
        text="A spray paint can: two quick rattles of the ball inside, then one short sharp hiss of paint spraying." + DRY),
    "s_smoke":    dict(kind="fx", d=1.2, p=0.65, fade_out=0.3,
        text="A smoke bomb going off: a soft pop and a thick whooshing hiss of smoke billowing out, then trailing off. No music, no voices."),
    "s_glitter":  dict(kind="fx", d=1.2, p=0.6, fade_out=0.3,
        text="A glitter bomb bursting: a light party popper pop followed by a bright sparkling magical shimmer of tinkling glitter falling. No music, no voices."),
    "s_pigeon":   dict(kind="fx", d=1.2, p=0.65, fade_out=0.2,
        text="A city pigeon flapping its wings hard right next to the microphone, a loud flurry of feathers and one startled coo. No music, no voices."),
}

# ---------------------------------------------------------------- voices
COLOURS = ["red", "blue", "white", "orange", "green", "purple"]
SUMS = {2: "Two. Snake eyes.", 3: "Three.", 4: "Four.", 5: "Five.", 6: "Six.", 7: "Seven. The heat is on.",
        8: "Eight.", 9: "Nine.", 10: "Ten.", 11: "Eleven.", 12: "Twelve. Boxcars."}
LINES = {}
for n, t in SUMS.items():
    # the context around a line shapes how it is read: a number called over the table, not read off a list
    LINES["v_sum_%d" % n] = dict(text=t, prev="The dice stop spinning, and it comes up", next="")
for c in COLOURS:
    LINES["v_up_" + c] = dict(text="%s, you're up." % c.capitalize())
    LINES["v_win_" + c] = dict(text="%s runs this city." % c.capitalize(), style=0.55)
    # the name on its own, read as the start of a sentence (release 2: "Green" + "is one away")
    LINES["v_n_" + c] = dict(text=c.capitalize(), next="is one move away from running this city.", style=0.4)
LINES.update({
    "v_start":   dict(text="Everybody roll. High roller goes first."),
    "v_tie":     dict(text="It's a tie. Roll again."),
    "v_place":   dict(text="Stake your claim."),
    "v_open":    dict(text="The city is open for business."),
    "v_discard": dict(text="Too much heat. Anyone holding more than seven, drop half."),
    # the thief's taunt, on the table and on the phone of whoever was robbed
    "v_taunt_1": dict(text="I'll be taking that.", style=0.6, stab=0.35),
    "v_taunt_2": dict(text="Don't mind if I do.", style=0.6, stab=0.35),
    "v_taunt_3": dict(text="Thanks for the card, sucker.", style=0.6, stab=0.35),
    "v_offer":   dict(text="There's a deal on the table."),
    "v_deal":    dict(text="Pleasure doing business."),
    "v_deal_2":  dict(text="Now we're talking.", style=0.5),
    "v_deal_3":  dict(text="Shake on it. It's done.", style=0.5),
    "v_deal_4":  dict(text="Everybody eats tonight.", style=0.5),
    # an operation opens: one of these, never the same twice running
    "v_op_1":    dict(text="New operation, up and running.", style=0.45),
    "v_op_2":    dict(text="Lights on. Money coming in.", style=0.45),
    "v_op_3":    dict(text="That corner's taken.", style=0.5),
    "v_op_4":    dict(text="Another front. Fresh paint.", style=0.45),
    "v_tower":   dict(text="Another tower on the skyline."),
    "v_nine":    dict(text="Somebody's one move from running this city."),
    # skills and talents: a line for each card played, the fight's end, Lucky Streak, a rare draw
    "v_c_tipoff":  dict(text="Somebody made a call.", style=0.5),
    "v_c_luck":    dict(text="Feeling lucky?", style=0.55),
    "v_c_silver":  dict(text="Smooth talker.", style=0.55),
    "v_c_paidoff": dict(text="The cops look the other way.", style=0.5),
    "v_c_backup":  dict(text="Backup's here.", style=0.5),
    "v_c_shakedown": dict(text="Pay up. Everybody.", style=0.55),
    "v_c_fight":   dict(text="Street fight!", style=0.6, stab=0.35),
    "v_c_roadcrew": dict(text="Road crew's rolling.", style=0.5),
    "v_c_connections": dict(text="It's who you know.", style=0.5),
    "v_c_legend":  dict(text="A local legend.", style=0.55),
    "v_c_rewind":  dict(text="Let's run that back.", style=0.55),
    "v_ko":        dict(text="Knockout!", style=0.6, stab=0.35),
    "v_taken":     dict(text="That street just changed hands.", style=0.5),
    "v_held":      dict(text="They held their ground.", style=0.5),
    "v_pick":      dict(text="Pick your two.", style=0.5),
    "v_rare":      dict(text="Now that's a rare find.", style=0.55),
    "v_legendary": dict(text="Legendary.", style=0.6),
    # a pile-up in the traffic (three cars or more), now and then
    "v_crash_1":   dict(text="Somebody call a tow truck.", style=0.55),
    "v_crash_2":   dict(text="That's gonna leave a mark.", style=0.55),
    "v_crash_3":   dict(text="Nobody saw nothing.", style=0.55),
    # ---- pace (release 2, 2026-09-26) ----
    # the standings: a colour and what they did, said as two clips one after the other ("Green" + "is one away"),
    # so six names and a handful of phrases cover every player. Each part is read in the context of the other.
    "v_s_lead":    dict(text="takes the lead.", prev="Green", style=0.45),
    "v_s_leads":   dict(text="is out in front.", prev="Green", style=0.4),
    "v_s_one":     dict(text="is one away.", prev="Green", style=0.5),
    "v_s_two":     dict(text="is two away.", prev="Green", style=0.45),
    "v_s_half":    dict(text="is halfway there.", prev="Green", style=0.4),
    "v_s_tied":    dict(text="It's neck and neck at the top.", style=0.45),
    "v_s_round_1": dict(text="That's the round.", style=0.4),
    "v_s_round_2": dict(text="End of the round.", style=0.4),
    "v_s_round_3": dict(text="Round's done. Here's how it stands.", style=0.4),
    # the clock: a hurry-up's thirty seconds (or less, if that was all the turn had left), and the time running out
    # the hurry-up's calls are geed up (4 Oct 2026): its start, its last ten, and a turn that beats it
    "v_hurry":     dict(text="Everybody's waiting! Thirty seconds!", style=0.75, stab=0.3),
    "v_hurry_2":   dict(text="Here we go! Thirty seconds on the clock!", style=0.75, stab=0.3),
    "v_hurry_3":   dict(text="The table has spoken! Thirty seconds, let's go!", style=0.75, stab=0.3),
    "v_hurry_4":   dict(text="Oh, they're done waiting! Thirty seconds, make it count!", style=0.75, stab=0.3),
    "v_hurry_5":   dict(text="Clock's on! Thirty seconds! Go, go, go!", style=0.75, stab=0.3),
    "v_hurry_go":  dict(text="Everybody's waiting! Hurry it up!", style=0.75, stab=0.3),
    "v_hurry_go_2": dict(text="Come on, come on! The clock is running!", style=0.75, stab=0.3),
    "v_hurry_go_3": dict(text="The whole table wants you moving! Let's go!", style=0.75, stab=0.3),
    "v_ten_1":     dict(text="Ten seconds!", style=0.75, stab=0.3),
    "v_ten_2":     dict(text="Ten seconds left! Come on!", style=0.75, stab=0.3),
    "v_ten_3":     dict(text="Final ten! Move it, move it!", style=0.75, stab=0.3),
    "v_ten_4":     dict(text="Ten seconds! It's now or never!", style=0.75, stab=0.3),
    "v_beat_1":    dict(text="Made it! Just under the wire!", style=0.75, stab=0.3),
    "v_beat_2":    dict(text="Oh, and they beat the clock!", style=0.75, stab=0.3),
    "v_beat_3":    dict(text="With seconds to spare! What a finish!", style=0.75, stab=0.3),
    "v_beat_4":    dict(text="Phew! Just in time!", style=0.75, stab=0.3),
    "v_timeup_1":  dict(text="Time's up.", style=0.5),
    "v_timeup_2":  dict(text="That's time. Next.", style=0.5),
    # a slow turn gets a yawn or a dig; a quick one with a plan in it, a nod (v3 for the yawn: it reads the tag)
    "v_slow_1":    dict(text="[yawns] Any day now.", model="eleven_v3"),
    "v_slow_2":    dict(text="Take your time. The city can wait.", style=0.6, stab=0.35),
    "v_slow_3":    dict(text="Tick tock.", style=0.6, stab=0.35),
    "v_slow_4":    dict(text="I've seen glaciers move faster.", style=0.6, stab=0.35),
    "v_slow_5":    dict(text="While we're young.", style=0.6, stab=0.35),
    "v_fast_1":    dict(text="In and out. Clean.", style=0.5),
    "v_fast_2":    dict(text="Now that's a plan.", style=0.5),
    "v_fast_3":    dict(text="Fast money.", style=0.5),
    "v_fast_4":    dict(text="Somebody came prepared.", style=0.5),
    "v_fast_5":    dict(text="Smooth. Very smooth.", style=0.55),
    # ---- trash talk (release 3, 2026-09-26): now and then the announcer reads a whisper out loud: an intro, then
    # the colour and "says" ("Red" + "says"), then the phrase, each read in the context of the next so they splice.
    # The phrases are the fixed menu on the phones (a whisper can only be what the announcer has recorded).
    "v_icpt_1":    dict(text="Ooh, what's this? A little whisper.", style=0.6, stab=0.35),
    "v_icpt_2":    dict(text="Intercepted!", style=0.6, stab=0.35),
    "v_icpt_3":    dict(text="I'm reading your mail.", style=0.6, stab=0.35),
    "v_icpt_4":    dict(text="Passing notes, are we?", style=0.6, stab=0.35),
    "v_says":      dict(text="says:", prev="Red", next="Watch out.", style=0.45),
    # the whispers (redone 2026-09-27): quick street banter, nine situations of five lines, each quoted with relish
    # making a deal
    "v_w_youin":       dict(text="You in?", prev="And Red says:", style=0.55),
    "v_w_letstalk":    dict(text="Let's talk.", prev="And Red says:", style=0.55),
    "v_w_offer":       dict(text="What's your offer?", prev="And Red says:", style=0.55),
    "v_w_worth":       dict(text="Make it worth it.", prev="And Red says:", style=0.55),
    "v_w_wegood":      dict(text="We good?", prev="And Red says:", style=0.55),
    # agreeing
    "v_w_bet":         dict(text="Bet.", prev="And Red says:", style=0.55),
    "v_w_sayless":     dict(text="Say less.", prev="And Red says:", style=0.55),
    "v_w_imin":        dict(text="I'm in.", prev="And Red says:", style=0.55),
    "v_w_runit":       dict(text="Run it.", prev="And Red says:", style=0.55),
    "v_w_weregood":    dict(text="We're good.", prev="And Red says:", style=0.55),
    # turning it down
    "v_w_nah":         dict(text="Nah.", prev="And Red says:", style=0.55),
    "v_w_dreaming":    dict(text="You're dreaming.", prev="And Red says:", style=0.55),
    "v_w_tryagain":    dict(text="Try again.", prev="And Red says:", style=0.55),
    "v_w_nothappening": dict(text="Not happening.", prev="And Red says:", style=0.55),
    "v_w_dobetter":    dict(text="Do better.", prev="And Red says:", style=0.55),
    # claiming turf
    "v_w_myblock":     dict(text="My block.", prev="And Red says:", style=0.55),
    "v_w_keepwalking": dict(text="Keep walking.", prev="And Red says:", style=0.55),
    "v_w_wronghood":   dict(text="Wrong neighbourhood.", prev="And Red says:", style=0.55),
    "v_w_owncorner":   dict(text="Find your own corner.", prev="And Red says:", style=0.55),
    "v_w_rentsdue":    dict(text="Rent's due.", prev="And Red says:", style=0.55),
    # calling a bluff
    "v_w_youwont":     dict(text="You won't.", prev="And Red says:", style=0.55),
    "v_w_proveit":     dict(text="Prove it.", prev="And Red says:", style=0.55),
    "v_w_alltalk":     dict(text="All talk.", prev="And Red says:", style=0.55),
    "v_w_nicetry":     dict(text="Nice try.", prev="And Red says:", style=0.55),
    "v_w_iseeyou":     dict(text="I see you.", prev="And Red says:", style=0.55),
    # giving props
    "v_w_fairplay":    dict(text="Fair play.", prev="And Red says:", style=0.55),
    "v_w_clean":       dict(text="That was clean.", prev="And Red says:", style=0.55),
    "v_w_respect":     dict(text="Respect.", prev="And Red says:", style=0.55),
    "v_w_okseeyou":    dict(text="Okay, I see you.", prev="And Red says:", style=0.55),
    "v_w_bigmove":     dict(text="Big move.", prev="And Red says:", style=0.55),
    # talking trash
    "v_w_cooked":      dict(text="You're cooked.", prev="And Red says:", style=0.55),
    "v_w_holdthat":    dict(text="Hold that.", prev="And Red says:", style=0.55),
    "v_w_rough":       dict(text="That's rough.", prev="And Red says:", style=0.55),
    "v_w_quiet":       dict(text="Got real quiet.", prev="And Red says:", style=0.55),
    "v_w_comfy":       dict(text="Don't get comfy.", prev="And Red says:", style=0.55),
    # getting revenge
    "v_w_energy":      dict(text="Keep that energy.", prev="And Red says:", style=0.55),
    "v_w_coming":      dict(text="Your turn's coming.", prev="And Red says:", style=0.55),
    "v_w_oweyou":      dict(text="I owe you one.", prev="And Red says:", style=0.55),
    "v_w_pockets":     dict(text="Watch your pockets.", prev="And Red says:", style=0.55),
    "v_w_notdone":     dict(text="We're not done.", prev="And Red says:", style=0.55),
    # hurrying them up
    "v_w_yourmove":    dict(text="Your move.", prev="And Red says:", style=0.55),
    "v_w_anyday":      dict(text="Any day now.", prev="And Red says:", style=0.55),
    "v_w_clock":       dict(text="Clock's ticking.", prev="And Red says:", style=0.55),
    "v_w_lesschat":    dict(text="Less chat. Move.", prev="And Red says:", style=0.55),
    "v_w_playing":     dict(text="We playing or what?", prev="And Red says:", style=0.55),
    # a table going wild with stickers
    "v_crowd_1":   dict(text="Tough crowd tonight.", style=0.55),
    "v_crowd_2":   dict(text="The crowd is restless.", style=0.55),
    "v_crowd_3":   dict(text="Somebody's feeling it.", style=0.55),
    # a splat landing on the player whose turn it is
    "v_splat_1":   dict(text="Eyes on the board.", style=0.55),
    "v_splat_2":   dict(text="Dirty tricks.", style=0.6, stab=0.35),
    "v_splat_3":   dict(text="Don't let them rattle you.", style=0.55),
    # the dispatcher, heard over the police radio when the police are sent in
    "v_cop_1":   dict(text="All units, that block is taped off. Nobody in, nobody out.", voice=DISPATCH, radio=True),
    "v_cop_2":   dict(text="Dispatch to all cars. Shut that block down.", voice=DISPATCH, radio=True),
    "v_cop_3":   dict(text="Car twelve responding. Rolling tape now.", voice=DISPATCH, radio=True),
})

# ---- the Director (release 4, 2026-09-26): the announcer knows the city while the camera glides there.
# Said as three clips run close together: what is happening, which side of the table it is on, and the district
# ("Shots fired." + "Far side," + "up by the nightlife strip."). Each part is read in the context of the others.
DIR_WHAT = {"chase": "Car chase!", "robbery": "Robbery in progress.", "gangwar": "Shots fired.",
            "race": "Street racers.", "concert": "Party on the roof.", "fire": "Something's burning.",
            "giant": "What is that?"}                                   # the giant (release 6)
DIR_SIDE = {"far": "Far side,", "front": "Right down front,", "left": "Over on the left,", "right": "Over on the right,",
            "mid": "Right in the middle,"}
DIR_DIST = {"nightlife": "up by the nightlife strip.", "warehouse": "down by the freight yards.",
            "residential": "in the residential blocks.", "works": "out at the works.", "tower": "under the towers.",
            "deadzone": "way out by the dead zone."}
for k, t in DIR_WHAT.items():
    LINES["v_e_" + k] = dict(text=t, next="Far side, up by the nightlife strip.", style=0.55)
for k, t in DIR_SIDE.items():
    LINES["v_p_" + k] = dict(text=t, prev="Shots fired.", next="up by the nightlife strip.", style=0.45)
for k, t in DIR_DIST.items():
    LINES["v_d_" + k] = dict(text=t, prev="Shots fired. Over on the left,", style=0.45)
LINES.update({
    # the ladder: the world wakes up, then the camera starts to move
    "v_dir_wake":  dict(text="The city's waking up.", style=0.5),
    "v_dir_look":  dict(text="Let's take a closer look.", style=0.5),
    # story panels for moves that had no line of their own: the bank, a terminal, a card bought
    "v_bank_1":    dict(text="The bank always wins.", style=0.55),
    "v_bank_2":    dict(text="Cash at the window.", style=0.5),
    "v_port_1":    dict(text="Straight off the boat.", style=0.5),
    "v_port_2":    dict(text="Fresh off the docks.", style=0.5),
    "v_buy_1":     dict(text="Something from the back room.", style=0.55),
    "v_buy_2":     dict(text="Under the counter.", style=0.55),
})
# ---- turf war (release 5, 2026-09-26): the two cards that go after a building, what they do, and turf won and lost,
# said as a colour and a phrase ("Green" + "carves out their turf.") like the standings
LINES.update({
    "v_c_bustup":      dict(text="It's a bust up!", style=0.6, stab=0.35),
    "v_c_wrecking":    dict(text="Here comes the wrecking crew.", style=0.55),
    "v_down_bustup":   dict(text="That operation's closed for good.", style=0.5),
    "v_down_wrecking": dict(text="That's a few floors lighter.", style=0.55),
    "v_t_on_1":        dict(text="claims their turf.", prev="Green", style=0.5),
    "v_t_on_2":        dict(text="has walled off a slice of the city.", prev="Green", style=0.45),
    "v_t_off_1":       dict(text="just lost their turf.", prev="Green", style=0.5),
    "v_t_off_2":       dict(text="has had their line cut.", prev="Green", style=0.5),
})

# ---------------------------------------------------------------- showtime (release 6)
# The victory show: music under it, the towers going up as rockets, fireworks, the winner's crews firing into the
# air, the confetti truck in the parade; and the giant's footsteps and calls. All of it the table's (embed.py TABLE).
SFX.update({
    "st_music":   dict(kind="fx", music=True, d=52, text="Triumphant instrumental victory anthem for the winner's celebration in a "
        "neon-noir crime board game: a hard-hitting hip-hop beat with a booming 808 bass, big brass stabs, claps and a soaring synth "
        "lead, confident and celebratory like the finale of a gangster movie at night. It builds for the first few seconds, runs at "
        "full energy through the middle and ends on one big final hit that rings out. Instrumental only, no vocals, no words."),
    "st_rocket":  dict(post=PUNCHY % -2, kind="fx", d=7, p=0.5, fade_out=1.5, text="A rocket launch heard from the street: a deep ignition rumble and "
        "whoosh that builds into a roaring, crackling engine thrust, then fades away upward as the rocket climbs into the sky. "
        "Cinematic and powerful. No music, no voices."),
    "st_boom":    dict(kind="fx", d=3, p=0.55, fade_out=0.6, text="One firework going up and bursting: a short rising whistle, a big "
        "deep boom, then a shower of crackling sparkles fading away. Outdoors at night. No music, no voices."),
    "st_shots":   dict(kind="fx", d=3, p=0.5, fade_out=0.4, text="A gang celebrating a win by firing handguns into the air: a few "
        "quick bursts of pistol shots echoing between city buildings at night, with whoops and a cheer. No music."),
    "st_pop":     dict(kind="fx", d=2, p=0.55, fade_out=0.4, text="A confetti cannon firing: a sharp air cannon pop and a whoosh of "
        "paper confetti fluttering down, with a small crowd cheering. No music."),
    "giant_step": dict(post=PUNCHY % 8, kind="fx", d=1.6, p=0.6, fade_out=0.4, text="One enormous footstep of a giant walking machine landing on a "
        "city street: a deep, heavy, booming thud with a metallic clank, the ground shaking and small debris rattling. No music, "
        "no voices."),
    "giant_mech": dict(post=PUNCHY % -4, kind="fx", d=4, p=0.5, fade_out=0.6, text="A giant construction robot walking through a city: heavy "
        "hydraulic servos whining, pistons hissing and clanking, then a deep industrial foghorn blast. No music, no voices."),
    "giant_beast": dict(post=PUNCHY % 5, kind="fx", d=4.5, p=0.5, fade_out=0.8, text="A colossal unknown sea creature calling out across a city at "
        "night: a long, deep, eerie, echoing whale-like moan with a wet gurgle at the end. Not a lion, not a dinosaur roar. No music, "
        "no voices."),
})
LINES.update({
    "v_st_crew_1": dict(text="Light it up!", style=0.6),
    "v_st_crew_2": dict(text="Let the whole city hear it!", style=0.6),
    "v_st_count":  dict(text="Three. Two. One.", stab=0.6, style=0.4),
    "v_st_lift_1": dict(text="Liftoff!", style=0.6),
    "v_st_lift_2": dict(text="We have liftoff!", style=0.6),
    "v_st_orbit":  dict(text="Next stop, orbit.", style=0.5),
    "v_st_parade": dict(text="Clear the streets. Here comes the parade.", style=0.55),
    "v_st_face_1": dict(text="Look at that face.", style=0.55),
    "v_st_face_2": dict(text="Now that's a winner's smile.", style=0.55),
    "v_st_end":    dict(text="The city is yours. For now.", style=0.5),
    "v_giant_radio": dict(text="All units, be advised. We have a very large situation.", voice=DISPATCH, radio=True),
})

# ---------------------------------------------------------------- the coach (onboarding, 2026-09-27)
# The coach teaches a new player the game on their own phone: each move the first time it comes up, and the practice
# game from the front page. Said by the announcer, a notch calmer than his game calls. The page shows the same words
# as captions (COACH_SAY); embed.py puts the v_k_ clips in a pack of their own, fetched only by a phone being coached.
LINES.update({
    "v_k_hello":       dict(text="Welcome to the city. I'm your coach. The first time each move comes up, I'll show you what to tap, and talk you through it.", style=0.3, stab=0.55),
    "v_k_goal":        dict(text='The job is simple. First crew to ten points runs the city. Every operation you open is worth one point. A major holding is worth two.', style=0.3, stab=0.55),
    "v_k_rolloff":     dict(text='First, everybody rolls. Highest roll places first. Tap Roll the dice.', style=0.3, stab=0.55),
    "v_k_place_op":    dict(text='Set-up time. Tap a glowing corner to put down your first operation. Pick a corner that touches plenty of blocks.', style=0.3, stab=0.55),
    "v_k_place_pick":  dict(text='Red numbers, six and eight, come up the most. And try to touch different colours, so you collect all five kinds of card.', style=0.3, stab=0.55),
    "v_k_place_confirm": dict(text='Good spot. Now tap the button to place it.', style=0.3, stab=0.55),
    "v_k_place_street": dict(text='Now lay a street. Tap a glowing path next to your operation. Streets are how you reach new corners to build on.', style=0.3, stab=0.55),
    "v_k_place_second": dict(text='Your second operation. This one pays straight away: one card for every block it touches.', style=0.3, stab=0.55),
    "v_k_wait":        dict(text="It's someone else's turn now. You can't build, but when their dice hit your blocks, you still get paid. So keep watching.", style=0.3, stab=0.55),
    "v_k_roll":        dict(text="Your turn. Every turn starts with the dice. Tap Roll the dice. Every block on that number pays whoever's built around it.", style=0.3, stab=0.55),
    "v_k_paid":        dict(text="Payday! Your building touches that block, so the cards went into your hand. Down here is everything you're holding.", style=0.3, stab=0.55),
    "v_k_nopay":       dict(text="Nothing for you on that roll. It happens. Build around more numbers, and you'll get paid more often.", style=0.3, stab=0.55),
    "v_k_act":         dict(text="Now it's building time. This list shows what you can make. A lit card is one you hold. An empty outline is one you're still missing.", style=0.3, stab=0.55),
    "v_k_key":         dict(text='Not sure which block pays what? Tap Key, up top. Each colour of block pays its own card.', style=0.3, stab=0.55),
    "v_k_build_street": dict(text='A street costs one muscle and one product. Tap a glowing path, then tap Build.', style=0.3, stab=0.55),
    "v_k_build_op":    dict(text="An operation costs one muscle, one product, one talent and one cash. It goes on a free corner at the end of your street, and it's worth a point.", style=0.3, stab=0.55),
    "v_k_build_holding": dict(text="Upgrade an operation to a major holding, for two cash and three influence. It's worth two points, and it pays double.", style=0.3, stab=0.55),
    "v_k_trade_bank":  dict(text='Short a card? Trade at a terminal. Four of one kind buys one of any other. Build on the coast by a terminal, and you get a better rate.', style=0.3, stab=0.55),
    "v_k_offer":       dict(text="Or deal with the other crews. Pick what you'll give, and what you want. They answer on their phones, and you choose who to deal with.", style=0.3, stab=0.55),
    "v_k_answer":      dict(text="Someone's offering you a trade. Take it if it gets you closer to building something. Or pass. It costs you nothing either way.", style=0.3, stab=0.55),
    "v_k_end":         dict(text="When you've done all you want, tap End my turn, then Yes. The dice pass to the next crew.", style=0.3, stab=0.55),
    "v_k_seven":       dict(text='A seven! Nobody gets paid on a seven. Anyone holding more than seven cards loses half. And the police are on their way.', style=0.3, stab=0.55),
    "v_k_discard":     dict(text="You're holding more than seven cards, so you drop half. Tap the cards you can best spare, then drop them.", style=0.3, stab=0.55),
    "v_k_police":      dict(text='You rolled the seven, so you move the police. Tap a block. It stops paying until the police move on. Pick one where your rivals earn.', style=0.3, stab=0.55),
    "v_k_steal":       dict(text='Now lean on somebody with a building on that block. You take one of their cards, unseen.', style=0.3, stab=0.55),
    "v_k_robbed":      dict(text="The police are sitting on one of your blocks. It won't pay you, until somebody moves them on.", style=0.3, stab=0.55),
    "v_k_market":      dict(text='Skills and talents are special cards. Open the market to buy one. Each one bends the rules, once. You can play one a turn.', style=0.3, stab=0.55),
    "v_k_cardplay":    dict(text="You're holding a skill or talent. Tap Play a skill or talent to read it, and play it when the moment's right.", style=0.3, stab=0.55),
    "v_k_fight":       dict(text='Street fight! Each round, you both pick a move at the same time. A swing is free. The big hits cost cards. Knock their strength to zero, and you win.', style=0.3, stab=0.55),
    "v_k_luck":        dict(text='Lucky Streak! You threw three dice. Keep the two that pay you best.', style=0.3, stab=0.55),
    "v_k_clock":       dict(text="See the clock? When it runs out, the table finishes your turn for you. So don't hang about.", style=0.3, stab=0.55),
    "v_k_talk":        dict(text='One more thing. Tap the speech bubble up top, to throw stickers and whisper to the other crews. Trash talk is half the game.', style=0.3, stab=0.55),
    "v_k_players":     dict(text="Want the score? Open Players, to see everyone's points, and how many cards they're holding.", style=0.3, stab=0.55),
    "v_k_done":        dict(text="That's the lot. You know the streets now, so I'll go quiet. Good luck out there.", style=0.3, stab=0.55),
    "v_k_lx_intro":    dict(text="This is a practice game. The other two crews are run by the computer, and I'm rigging the dice a little, so you get to see everything. Nothing here counts.", style=0.3, stab=0.55),
    "v_k_lx_gift":     dict(text="Here. The bank's spotting you a few cards, so you can try building.", style=0.3, stab=0.55),
    "v_k_lx_short":    dict(text="You're one talent short of an operation. Trade four cash for it at a terminal. Tap Trade at a terminal.", style=0.3, stab=0.55),
    "v_k_lx_trade":    dict(text='Now try trading. Tap Trade at a terminal, and swap four of one kind for a card you need.', style=0.3, stab=0.55),
    "v_k_lx_seven":    dict(text="Watch this. Somebody's about to roll a seven.", style=0.3, stab=0.55),
    "v_k_lx_offer":    dict(text='Try a deal. Tap Offer the table a trade, and ask the other crews for a card you need.', style=0.3, stab=0.55),
    "v_k_lx_done":     dict(text="That's the practice done. You can roll, build, trade, and handle the police. Keep playing if you like, or go and start a real game.", style=0.3, stab=0.55),
})
# ---- end of the coach

# ---------------------------------------------------------------- levels and encoding
# How loud each kind is, and how it is encoded. Peaks never go above -1 dB.
# lu is the loudest 400 ms of the clip, K-weighted (LUFS, near enough to EBU R128's momentary
# loudness): how hard a sound hits the ear, which is what "too loud" is about. Levelling by the
# average (RMS) let short, sharp sounds hit as hard as the announcer and louder, which is how the
# first play-test heard it: "too loud and abrupt" (2026-09-25). So the announcer sets the level,
# the effects sit 4 dB and more under him, the busy ones (cards, reels, taps) well under that, and
# a sound can ask to sit lower or higher than its kind with its own lu. The loop keeps RMS.
LEVEL = {
    "fx":    dict(lu=-21, rate=44100, kbps=48),
    "ui":    dict(lu=-28, rate=44100, kbps=48),
    "voice": dict(lu=-17, rate=24000, kbps=40),
    "amb":   dict(rms=-26, rate=32000, kbps=32),
}
# A clip is encoded hot, at HOT or with its peak at -1 dB, whichever is lower, and played down to its lu by the page:
# the encoder drops the quiet highs it thinks nobody can hear, judged from full scale, so a sparkle encoded 5 dB
# down came out dull and 4 dB quieter still. process() measures what the encoder made and writes the difference
# to web/trims.json (dB); embed.py puts it in the page's index beside each clip.
HOT = -14
TRIMS = os.path.join(WEB, "trims.json")
# where each effect sits against its kind (lu), decided from measuring them all (2026-09-26):
# the moments of the game a little under the announcer, what a move sounds like under that, and
# the sounds that come in flurries or on every turn lowest of all
LOUD = {
    # the moments
    "win": -19, "seven": -20, "ko": -20, "reveal_big": -20, "punch_big": -20,
    "legend": -21, "build_holding": -21, "fight_bell": -21, "tension": -21, "crash_hit": -21, "crash_boom": -21,
    # a move, a card, a blow
    "siren": -22, "card_play": -22, "reveal": -22, "tipoff": -22, "lucky": -22, "silver": -22, "connections": -22,
    "shakedown": -22, "roadcrew": -22, "paidoff": -22, "punch": -22, "hype": -22, "backup": -22, "fight_end": -22,
    "your_turn": -22,
    # every turn, every trade, every build
    "turn": -23, "bank": -23, "build_street": -23, "build_op": -23, "trade_offer": -23, "join": -23, "steal": -23,
    "card_buy": -23, "crate": -23, "block": -23, "patch": -23, "pull": -23, "backoff": -23, "crash_bump": -23, "crash_skid": -23,
    # in flurries, or under everything else
    "payout": -24, "discard": -24, "leave": -24, "undo": -24, "tape": -24, "whiff": -24, "trade_yes": -24, "trade_no": -24,
    "card_whoosh": -26, "card_land": -26, "horn_1": -26, "horn_2": -26,
    # buttons
    "ui_tap": -29, "ui_pick": -29, "ui_confirm": -28, "ui_deny": -30,
    # the turn clock (release 2): the buzzer is a moment; the countdown's beeps must cut through on a phone, the
    # table's ticks sit well under everything; the standings sting is a move's worth
    "time_up": -21, "hurry_start": -22, "clock_beep": -23, "score_sting": -23, "clock_tick": -27,
    # trash talk (release 3): a sticker's bite sits under a move (several can fly at once), a splat is a move
    # on the phone it lands on, the whisper is private and soft
    "e_cheer": -24, "e_boo": -24, "e_lol": -24, "e_clap": -24, "e_crickets": -25, "e_rain": -24, "e_fire": -24,
    "e_sweat": -24, "e_cry": -24, "e_micdrop": -23, "whisper": -25,
    "s_tag": -22, "s_smoke": -22, "s_glitter": -22, "s_pigeon": -22,
    # turf war (release 5): turf won is a moment, lost a little under it; a building coming down is a blow
    "turf_on": -21, "turf_off": -23, "crumble": -21,
}
# a softer start for the sounds whose first instant is not the point (seconds of fade-in)
SOFT = {"start": 0.25, "legend": 0.06, "siren": 0.05, "hype": 0.04, "win": 0.03, "tension": 0.03,
        "build_holding": 0.02, "reveal_big": 0.02, "join": 0.01, "fight_end": 0.01}
# showtime (release 6)
LOUD.update({"st_music": -24, "st_rocket": -21, "st_boom": -22, "st_shots": -24, "st_pop": -24,
             "giant_step": -22, "giant_mech": -22, "giant_beast": -21})
SOFT.update({"st_music": 0.4, "st_rocket": 0.15, "giant_beast": 0.1, "giant_mech": 0.05})

# ---------------------------------------------------------------- game modes (release 9, 2026-09-27)
# The lobby's modes said out loud: each mode's first roll, a rush-hour round, the last round of a timed match, a
# chess bank running dry ("Green" + "is out of time..."), the auction (opened, and "Green" + "takes it. Sold!"), a
# hustle, time called; and the three clock-trick cards. The gavel is the table's (embed.py TABLE).
SFX.update({
    "gavel":      dict(kind="fx", d=1.2, p=0.65, fade_out=0.2, text="An auctioneer's wooden gavel striking the sound block twice, sharp and clear, in a small wood-panelled room. No voices, no music."),
})
LOUD.update({"gavel": -21})
LINES.update({
    "v_m_go_blitz":  dict(text="Blitz rules. Forty-five seconds a turn. Move!", style=0.6),
    "v_m_go_chess":  dict(text="Chess clock. Every second you spend comes out of your own pocket.", style=0.5),
    "v_m_go_match":  dict(text="The match clock is running. Top score when time's up takes the city.", style=0.5),
    "v_m_go_rush":   dict(text="Welcome to rush hour. The clocks are tight, and the market's open late.", style=0.55),
    "v_m_rushhour":  dict(text="Rush hour! Every clock is cut in half.", style=0.6, stab=0.35),
    "v_m_last":      dict(text="That's time! Last round. Make it count.", style=0.6),
    "v_m_bankout":   dict(text="is out of time. Sudden death.", prev="Green", style=0.5),
    "v_m_auction":   dict(text="The auction's open! Twenty seconds. Show me the cash.", style=0.6),
    "v_m_sold":      dict(text="takes it. Sold!", prev="Green", style=0.55),
    "v_m_hustle":    dict(text="Hustle pays. That's a free card.", style=0.55),
    "v_m_time":      dict(text="That's the match! The clock has spoken.", style=0.55),
    "v_c_overtime":  dict(text="Overtime! Thirty more seconds.", style=0.55),
    "v_c_stall":     dict(text="Stalling. Nobody's rushing this one.", style=0.5),
    "v_c_rush":      dict(text="Rush job! Somebody's in a hurry.", style=0.55),
})
# Safe House and Spy (2026-10-04): said by sndPlay as the card is played, like every card's line
LINES.update({
    "v_c_safehouse": dict(text="Safe house. The stash stays put.", style=0.5),
    "v_c_spy":       dict(text="Somebody's watching your hand.", style=0.55),
})


def post(path, body, out, query=""):
    key = os.environ.get("ELEVENLABS_API_KEY") or sys.exit("ELEVENLABS_API_KEY is not set")
    req = urllib.request.Request(API + path + query, data=json.dumps(body).encode(),
                                 headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                data = r.read()
            open(out, "wb").write(data)
            return len(data)
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:300]
            if e.code in (429, 500, 502, 503) and attempt < 3:
                time.sleep(3 + attempt * 4); continue
            raise RuntimeError("%s -> %d %s" % (os.path.basename(out), e.code, msg))


def gen_sfx(name, out=None):
    s = SFX[name]
    if s.get("music"):                                                 # a piece of music (release 6): Eleven Music, instrumental
        body = {"prompt": s["text"], "music_length_ms": int(s["d"] * 1000), "model_id": "music_v1", "force_instrumental": True}
        return post("/music", body, out or os.path.join(RAW, name + ".mp3"), "?output_format=mp3_44100_128")
    body = {"text": s["text"], "duration_seconds": s["d"], "prompt_influence": s["p"], "model_id": SFX_MODEL}
    if s.get("loop"): body["loop"] = True
    return post("/sound-generation", body, out or os.path.join(RAW, name + ".mp3"), "?output_format=mp3_44100_128")


def gen_voice(name):
    l = LINES[name]
    if l.get("model") == "eleven_v3":
        # v3 reads audio tags ("[yawns]"); it takes stability as 0, 0.5 or 1 and no context either side
        body = {"text": l["text"], "model_id": "eleven_v3", "seed": 7, "voice_settings": {"stability": 0.5, "similarity_boost": 0.8}}
        return post("/text-to-speech/%s" % l.get("voice", ANNOUNCER), body, os.path.join(RAW, name + ".mp3"), "?output_format=mp3_44100_128")
    body = {"text": l["text"], "model_id": TTS_MODEL, "seed": 7,
            "voice_settings": {"stability": l.get("stab", 0.45), "similarity_boost": 0.8, "style": l.get("style", 0.35), "use_speaker_boost": True}}
    if l.get("prev"): body["previous_text"] = l["prev"]
    if l.get("next"): body["next_text"] = l["next"]                    # what follows it (a name read as the start of a sentence)
    elif l.get("next") is not None and l.get("prev"): body["next_text"] = "."
    return post("/text-to-speech/%s" % l.get("voice", ANNOUNCER), body, os.path.join(RAW, name + ".mp3"), "?output_format=mp3_44100_128")


def unring(path, pre):
    """Equaliser notches for the narrow peaks that make a short sound ring like metal: any peak more
    than 10 dB above the spectrum around it, the worst three, each cut by how far it stands out."""
    import numpy as np
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-af", pre or "anull", "-ac", "1", "-ar", "44100", "-f", "f32le", "-"], capture_output=True)
    x = np.frombuffer(r.stdout, dtype=np.float32); x = x - x.mean() if len(x) else x
    if len(x) < 4096: return ""
    n = 4096; fr = np.lib.stride_tricks.sliding_window_view(x, n)[::1024] * np.hanning(n)
    spec = (np.abs(np.fft.rfft(fr, axis=1)) ** 2).mean(0) + 1e-12; f = np.fft.rfftfreq(n, 1 / 44100)
    band = np.where((f > 300) & (f < 12000))[0]; db = 10 * np.log10(spec)
    k = 60; notches = []
    for _ in range(3):
        med = np.array([np.median(db[max(0, i - k):i + k + 1]) for i in band])
        over = db[band] - med; j = int(over.argmax())
        if over[j] < 10: break
        fc = float(f[band[j]]); notches.append("equalizer=f=%d:t=q:w=8:g=-%d" % (fc, min(24, over[j])))
        lo, hi = band[max(0, j - 6)], band[min(len(band) - 1, j + 6)]
        db[lo:hi + 1] = med[j]                                          # flatten it so the next pass finds the next peak
    return ",".join(notches)


def ff(*args):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-y", *args], capture_output=True, text=True)
    if r.returncode: raise RuntimeError(r.stderr[-600:])
    return r.stderr


def stats(path, pre=""):
    """RMS and peak in dB of a file after an optional filter chain."""
    err = ff("-i", path, "-af", (pre + "," if pre else "") + "volumedetect", "-f", "null", "-")
    mean = float(err.split("mean_volume:")[1].split("dB")[0]); peak = float(err.split("max_volume:")[1].split("dB")[0])
    return mean, peak


def loudness(path, pre=""):
    """The loudest 400 ms of a file after an optional filter chain, K-weighted (a high shelf and a
    high pass, as in ITU-R BS.1770), in LUFS; and its sample peak in dB. A clip shorter than 400 ms
    is measured as if silence followed it, as a listener would hear it."""
    import numpy as np
    base = (pre + "," if pre else "") + "aformat=channel_layouts=mono,aresample=48000"
    def pcm(af):
        r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-af", af, "-f", "f32le", "-"], capture_output=True)
        return np.frombuffer(r.stdout, dtype=np.float32).astype(np.float64)
    x = pcm(base)
    peak = float(20 * np.log10(np.abs(x).max() + 1e-12)) if len(x) else -120.0
    k = pcm(base + ",highshelf=f=1681:g=4:t=q:w=0.7071,highpass=f=38:p=2")
    n = 19200
    if len(k) < n: k = np.concatenate([k, np.zeros(n - len(k))])
    c = np.concatenate([[0.0], np.cumsum(k * k)]); at = np.arange(0, len(k) - n + 1, 480)
    return float(-0.691 + 10 * np.log10(((c[at + n] - c[at]) / n).max() + 1e-12)), peak


def duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True)
    return float(r.stdout.strip())


def process(name, src=None, dst=None):
    src = src or os.path.join(RAW, name + ".mp3"); dst = dst or os.path.join(WEB, name + ".mp3")
    kind = "voice" if name in LINES else SFX[name]["kind"]
    L = dict(LEVEL[kind])
    if name in LOUD: L["lu"] = LOUD[name]
    if name in SFX and "lu" in SFX[name]: L["lu"] = SFX[name]["lu"]     # a sound that should sit lower than its kind
    if name in LINES and LINES[name].get("radio"): L["lu"] = L["lu"] - 1  # the radio's crunch makes it sound louder than it measures
    chain = []
    if kind == "amb":
        # a loop keeps its whole length and both ends, or the seam shows
        chain = ["aformat=channel_layouts=mono"]
    else:
        # trim the silence either side so a sound starts on the frame it is played,
        # then a short fade so a hard cut never clicks
        # speech trails off into quiet consonants ("up" ends on a soft p), so a voice keeps more of its tail
        head, tail = ((("-55dB", "0.02"), ("-62dB", "0.15")) if kind == "voice" else (("-48dB", "0.004"), ("-48dB", "0.06")))
        cut = lambda t: "silenceremove=start_periods=1:start_threshold=%s:start_silence=%s" % t
        chain = ["aformat=channel_layouts=mono", cut(head), "areverse", cut(tail), "areverse"]
        if name in LINES and LINES[name].get("radio"):
            # a police radio: telephone band, a little crunch, and the squelch either side
            chain += ["highpass=f=420", "lowpass=f=3200", "acompressor=threshold=-22dB:ratio=6:attack=3:release=60",
                      "volume=4dB", "asoftclip=type=tanh", "highpass=f=380", "lowpass=f=3400"]
        extra = SFX[name] if name in SFX else {}
        if extra.get("post"): chain.append(extra["post"])
        if extra.get("unring"):
            cut = unring(src, ",".join(chain))
            if cut: chain.append(cut)
        chain += ["afade=t=in:d=%s" % extra.get("fade_in", SOFT.get(name, 0.004)), "areverse", "afade=t=in:d=%s" % extra.get("fade_out", "0.06" if kind != "ui" else "0.02"), "areverse"]
    pre = ",".join(chain)
    if name in LINES and LINES[name].get("radio"):
        # squelch in + voice + squelch out, as one clip
        tmp = os.path.join(WEB, "_" + name + ".wav")
        ff("-i", src, "-af", pre, "-ar", "44100", tmp)
        a, b = os.path.join(WEB, "squelch_in.wav"), os.path.join(WEB, "squelch_out.wav")
        for s in ("squelch_in", "squelch_out"):
            ff("-i", os.path.join(RAW, s + ".mp3"), "-af", "aformat=channel_layouts=mono,silenceremove=start_periods=1:start_threshold=-48dB,areverse,silenceremove=start_periods=1:start_threshold=-48dB,areverse,atrim=0:0.35,afade=t=out:st=0.25:d=0.1,volume=-6dB", "-ar", "44100", os.path.join(WEB, s + ".wav"))
        ff("-i", a, "-i", tmp, "-i", b, "-filter_complex", "[0][1][2]concat=n=3:v=0:a=1", "-ar", "44100", tmp + ".cat.wav")
        os.replace(tmp + ".cat.wav", tmp); src, pre = tmp, ""
    if "lu" in L:
        lu, peak = loudness(src, pre)
        gain = min(HOT - lu, -1.0 - peak)                               # hot, and never limited: the transients stay as they were
    else:
        mean, peak = stats(src, pre)
        gain = min(L["rms"] - mean, -1.0 - peak + 6.0)
    lim = ",alimiter=limit=0.89:attack=1:release=30:level=false:latency=true" if gain > -1.0 - peak else ""
    chain_full = (pre + "," if pre else "") + "volume=%.2fdB" % gain + lim
    rate, kbps = L["rate"], L["kbps"]
    if name in LINES and LINES[name].get("radio"): rate, kbps = 16000, 24   # nothing above 3.4 kHz survives the radio anyway
    ff("-i", src, "-af", chain_full, "-ac", "1", "-ar", str(rate), "-c:a", "libmp3lame", "-b:a", "%dk" % kbps, dst)
    if src.endswith(".wav"): os.remove(src)
    if "lu" in L and os.path.abspath(os.path.dirname(dst)) == os.path.abspath(WEB):   # a clip the game plays (not a take being compared)
        got, _ = loudness(dst)
        trims = json.load(open(TRIMS)) if os.path.exists(TRIMS) else {}
        trims[name] = round(min(2.5, L["lu"] - got), 1)              # a peaky line may sit a dB low rather than clip when played up
        json.dump(trims, open(TRIMS, "w"), indent=1, sort_keys=True)
    return dst


def main():
    os.makedirs(RAW, exist_ok=True); os.makedirs(WEB, exist_ok=True)
    args = sys.argv[1:]
    only_process = "--process" in args
    force = "--force" in args
    names = [a for a in args if not a.startswith("--")]
    everything = list(SFX) + list(LINES)
    bad = [n for n in names if n not in everything]
    if bad: sys.exit("unknown: " + ", ".join(bad))
    todo = names or everything
    if not only_process:
        if force:
            for n in todo:
                p = os.path.join(RAW, n + ".mp3")
                if os.path.exists(p): os.remove(p)
        need = [n for n in todo if not os.path.exists(os.path.join(RAW, n + ".mp3"))]
        # the squelch has to exist before any radio line is put together
        need.sort(key=lambda n: 0 if n in SFX else 1)
        def one(n):
            try:
                size = gen_sfx(n) if n in SFX else gen_voice(n)
                print("  made %-16s %6d bytes" % (n, size)); return None
            except Exception as e:
                print("  FAILED %s: %s" % (n, e)); return n
        with ThreadPoolExecutor(max_workers=3) as ex:
            failed = [x for x in ex.map(one, need) if x]
        if failed: print("failed:", ", ".join(failed))
    meta = {}
    mp = os.path.join(WEB, "meta.json")
    if os.path.exists(mp): meta = json.load(open(mp))
    for n in everything:
        if not os.path.exists(os.path.join(RAW, n + ".mp3")): continue
        if names and n not in names and os.path.exists(os.path.join(WEB, n + ".mp3")) and not (n.startswith("v_cop") and any(x.startswith("squelch") for x in names)): continue
        try:
            dst = process(n)
            meta[n] = round(duration(dst), 3)
        except Exception as e:
            print("  could not process %s: %s" % (n, e))
    for f in os.listdir(WEB):
        if f.endswith(".wav"): os.remove(os.path.join(WEB, f))
    json.dump(meta, open(mp, "w"), indent=1, sort_keys=True)
    total = sum(os.path.getsize(os.path.join(WEB, n + ".mp3")) for n in meta if os.path.exists(os.path.join(WEB, n + ".mp3")))
    print("%d sounds in sound/web, %d KB" % (len(meta), total // 1024))


if __name__ == "__main__":
    main()
