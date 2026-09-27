# Run the City — graffiti reaction pack

Generated with the built-in ImageGen tool on 2026-09-27. This replaces the live artwork for all ten reaction stickers and four splats. Original generated alpha is preserved in transparent PNGs.

## Published assets

- `graffiti-reactions-a.png`: 971 × 1619, Big W / Cap / I'm dead / Aura + / Touch grass, three poses each.
- `graffiti-reactions-b.png`: 971 × 1619, Money talks / Let ’em cook / Cooked / Skill issue / Too easy, three poses each.
- `graffiti-splats.png`: 1086 × 1448, spray paint / smoke / glitter / pigeon, three poses each.
- `permanent-marker.ttf`: locally served Permanent Marker font. Source: https://fonts.gstatic.com/s/permanentmarker/v16/Fh4uPib9Iyv2ucM6pGQMWimMp004Hao.ttf . Apache 2.0 license included as `Permanent-Marker-LICENSE.txt`; upstream: https://github.com/google/fonts/tree/main/apache/permanentmarker .

The PNGs are the runtime layers. Explicit crop rectangles keep adjacent atlas artwork out of each pose. Live marker captions remain readable at different screen sizes. The earlier reaction sheets remain as previous versions; the game no longer requests them.

## Animation and responsiveness

Each table sticker responds immediately and lands at 480 ms, holding the first PNG pose throughout travel. Only after landing does the reaction play: a wind-up, the second pose at 800 ms, and the final pose at 1220 ms. A local impact burst and expressive squash/rotation accompany the pose changes. The caption appears after landing and stays with the final pose. Both hold until 2 seconds, then fade together over 200 ms; removal is at 2.2 seconds. There are no looping effects or videos.

A phone shows local feedback before closing the picker, independently of relay round-trip time; feedback lands at 320 ms, then plays the same reaction sequence and lasts 2.04 seconds, with the final pose and caption fading together. Reduced motion shows the final pose with a fade. Sticker sizes and positions are clamped to the viewport. Table splats land at 600 ms before their burst and aftermath poses, and last 3.2 seconds. Phone splats land at 672 ms before those poses and retain their 4.2-second, board-only, tap-through behavior. They resume at the correct frame after redraws.

Reaction audio is scheduled on the audio clock for the landing: 480 ms for table reactions, 600 ms for table splats, and 672 ms for splats received on a phone. Phones with whole-table audio use the same 480 ms reaction delay. Effects-off mode plays immediately because there is no travel.

Game screens preload all three PNGs and explicitly decode and retain them. Reaction sheets get high fetch priority; the splat sheet gets low priority. The marker font is warmed alongside them. Stable markup is cached. No new image fetch is needed when a warmed sticker is used.

Verification included all 42 frame transitions, landing-before-reaction checks for all 14 effects, 320px and 390px phone pickers, touch category controls, the existing 119 trash-talk checks, and a real touch-send path. At 390 × 844 with 4× browser CPU throttling, local feedback reached the next animation frame in 56.4 ms with zero post-tap image requests. This is a local test, not a guarantee for all devices or networks.

## Final generation prompts

### graffiti-reactions-a.png

```text
Use case: stylized-concept.
Asset type: production transparent PNG animation sprite atlas for Run the City, a neon street-crew board game.
Art direction: authentic contemporary graffiti sticker-bomb art and Gen Z meme visual language. Bold hand-drawn marker contours, aerosol overspray, distressed stencil fills, scratched chrome, wicked exaggerated gestures, spraypaint drips, angular wildstyle graphic shapes. Think stickers slapped on a skate deck or street sign, by a skilled graffiti artist. Thick midnight-black contours with uneven thin cream cut edges, rough analog print texture, acid-yellow, hot-pink, turquoise, cobalt and violet. High contrast readable at 90px. NOT glossy cute emoji / kawaii / soft friendly app-icon 3D. This should feel irreverent, rebellious, funny and stylish.
Layout contract: ONE tall atlas of exactly THREE EQUAL COLUMNS and FIVE EQUAL ROWS, 1536x2560 preferred. Fifteen separate square cells. Center each subject in its cell, with 15% transparent gutter on all four sides. Cells absolutely never touch. Each ROW is one sticker; its three columns are three ANIMATION FRAMES of the SAME identity: left anticipation/wind-up, middle hard impact/extreme expression, right held final pose. Keep camera, subject scale and anchor point consistent so the game can swap frames without jitter.
Transparency mandatory: actual alpha transparency behind and between ALL illustrations. No canvas color, no painted checkerboard, no wall, no page, no shadows behind the sheet, no grid, no panel backgrounds. Only isolated sticker silhouettes with their own small integrated paint flecks. Do not crop any subject at frame boundaries. No words or lettering except the explicitly requested single W or L glyph; game renders captions separately.

ROW 1 / BIG W: a large chunky chrome graffiti W character wearing a crooked acid-yellow three-point crown, with a dark gloved hand at each side. Frame 1 crouched/compressed W, fists lowered; frame 2 W punches both fists up and crown jumps with turquoise star impact ticks; frame 3 swaggering W and tilted crown, one raised fist. Only legible glyph is W. Very original graffiti tag silhouette.
ROW 2 / CAP: a cobalt-blue streetwear baseball cap with a face formed from painted slanted side-eye eyes under its brim and a pink gloved pointing hand. Frame 1 tilted cap peeking sideways; frame 2 cap leans forward and pointing finger calls someone out, strong skeptical eyes; frame 3 cap folded-brim scowl, dismissive pointing gesture. No lettering. The cap itself is the meme, not a yellow emoji face.
ROW 3 / I'M DEAD: wild magenta-and-bone laughing skull with a split neon checkerboard tongue, one small gold tooth and cyan tears, surrounded by rough ink laugh ticks. Frame 1 smirk; frame 2 huge cackling open jaw with tears shooting sideways; frame 3 skull tipped sideways, still laughing. Edgy graphic graffiti skull, no gore, not a round emoji.
ROW 4 / AURA: two streetwear hands doing a fist bump/dap, black fingerless gloves and oversized cyan and hot-pink sleeves; small chrome four-point star and acid-yellow graffiti halo behind the knuckles. Frame 1 fists approaching; frame 2 knuckles meet with explosive spraypaint spark; frame 3 locked dap with the gleaming star. Clean readable original street-hand gesture, not praying hands.
ROW 5 / TOUCH GRASS: deadpan lime-green patch of grass sprouting out of a battered purple high-top sneaker, with white slitted side-eye eyes on the sneaker tongue and a little spraypaint leaf. Frame 1 sneaker leans back; frame 2 plants down with two little dirt ticks and grass sprouts up; frame 3 sneaker sits unimpressed, thick grassy tuft. Graphic ironic street sticker, no cartoon insect.
Fifteen crisp isolated transparent sticker poses. NO caption boxes, NO extra words. Ensure all three poses in each row represent the identical subject.
```

### graffiti-reactions-b.png

```text
Use case: stylized-concept.
Asset type: production transparent PNG animation sprite atlas for Run the City, a neon street-crew board game.
Art direction: authentic contemporary graffiti sticker-bomb art and Gen Z meme visual language. Bold hand-drawn marker contours, aerosol overspray, distressed stencil fills, scratched chrome, wicked exaggerated gestures, spraypaint drips, angular wildstyle graphic shapes. Think stickers slapped on a skate deck or street sign, by a skilled graffiti artist. Thick midnight-black contours with uneven thin cream cut edges, rough analog print texture, acid-yellow, hot-pink, turquoise, cobalt and violet. High contrast readable at 90px. NOT glossy cute emoji / kawaii / soft friendly app-icon 3D. This should feel irreverent, rebellious, funny and stylish.
Layout contract: ONE tall atlas of exactly THREE EQUAL COLUMNS and FIVE EQUAL ROWS, 1536x2560 preferred. Fifteen separate square cells. Center each subject in its cell, with 15% transparent gutter on all four sides. Cells absolutely never touch. Each ROW is one sticker; its three columns are three ANIMATION FRAMES of the SAME identity: left anticipation/wind-up, middle hard impact/extreme expression, right held final pose. Keep camera, subject scale and anchor point consistent so the game can swap frames without jitter.
Transparency mandatory: actual alpha transparency behind and between ALL illustrations. No canvas color, no painted checkerboard, no wall, no page, no shadows behind the sheet, no grid, no panel backgrounds. Only isolated sticker silhouettes with their own small integrated paint flecks. Do not crop any subject at frame boundaries. No words or lettering except the explicitly requested single W or L glyph; game renders captions separately.

ROW 1 / MONEY TALKS: chunky roll of neon-lime banknotes with dark wraparound sunglasses, a little crooked chrome chain and pink gloved hands. Frame 1 holds a fan of notes close; frame 2 flings a few big loose notes up in boastful gesture; frame 3 smug money-roll character with a few floating notes. No numbers, no text. Bold graff icon.
ROW 2 / LET EM COOK: mysterious street-chef character shown from waist up in oversized charcoal hoodie and acid-yellow beanie, simple mask with two mischievous spraypaint eyes, holding a pan with a hot-pink flame. Frame 1 winds pan back; frame 2 flips a blazing orange and pink flame above pan; frame 3 confident held pan with a lively flame. Strong angular street silhouette, no raccoon/cat mascot, no lettering.
ROW 3 / COOKED: exhausted skeletal face half-melted into an oversized purple hoodie, anxious cyan eyes and a single fat neon sweat drop. Frame 1 tense hooded skull; frame 2 startled eyes and sweat exploding with jagged pink impact ticks; frame 3 slumped melting hood and deadpan exhausted expression. Expressive graffiti stencil creature, no gore.
ROW 4 / SKILL ISSUE: battered cartoon skateboard snapped in the middle into a giant angular L-like silhouette, with little hostile side-eye sticker eyes on its broken deck, checkerboard grip, cyan wheels and a magenta bandage. Frame 1 skateboard about to snap; frame 2 dramatic snapped board and a few rough acid-yellow impact dashes; frame 3 the two snapped halves arranged as a bold L-like sticker with unimpressed eyes. No text.
ROW 5 / TOO EASY: purple gloved streetwear hand dropping a scratched chrome microphone, with cyan cable loop and a small hot-pink graffiti crown motif. Frame 1 microphone held upright; frame 2 hand releases and microphone falls diagonally; frame 3 microphone lands slanted with a few rough acid-yellow impact arrows, gloved hand above in dismissive release. No words.
Fifteen crisp isolated transparent sticker poses. NO caption boxes, NO extra words. Ensure all three poses in each row represent the identical subject.
```

### graffiti-splats.png

```text
Use case: stylized-concept.
Asset type: transparent PNG three-frame spraypaint / graffiti screen-effect atlas for Run the City neon street-crew board game.
One 1536x2048 tall image divided into precisely THREE EQUAL COLUMNS and FOUR EQUAL ROWS. Each square cell centered with 15% empty transparent gutter on all sides, no content touching neighboring cells. Each row is one effect in 3 frames: incoming object, explosive impact, held aftermath. Actual transparent ALPHA outside every isolated object and between splatter / confetti particles. No background, no wall, no grid, no fake checkerboard.
Style: authentic sticker-bomb graffiti art, thick uneven midnight-black marker lines, aerosol overspray, distressed screen print, paint drips, sharp stenciled shapes. Acid yellow, hot pink, cyan, violet and chrome. Strong punchy street-skate style rather than glossy 3D emoji. Each frame is sharp and readable at 250px.
ROW 1 SPRAY PAINT: col 1 battered silver aerosol can with pink nozzle and a small paint jet, tipped toward viewer; col 2 violent neon-pink splash with cyan spray flecks and bold dark contour; col 3 broad irregular pink graffiti paint splat with thick drips and cyan flecks, transparent gaps. No words.
ROW 2 SMOKE: col 1 purple-and-black paint-stained smoke canister releasing small cyan smoke curl; col 2 big angular cyan/violet smoke explosion with inked spiral curls and a few stencil lightning marks; col 3 broad curling violet/cyan graffiti cloud broken by transparent holes, dissipating. No face.
ROW 3 GLITTER: col 1 hot-pink party popper with tiny chrome star emblem; col 2 graphic explosion of large chrome four-point stars, acid-yellow five-point stars, cyan and magenta paper shards and checkerboard confetti; col 3 loose falling graffiti-star confetti, airy transparent spaces. No words or numerals.
ROW 4 PIGEON: same rude chunky city pigeon in a tiny sideways purple cap and chrome chain, iridescent cyan neck, fierce side-eye, orange feet. Col 1 swoops toward viewer with wings tucked; col 2 both wings flung wide with graffiti impact ticks; col 3 puffs chest and gives unimpressed side-eye, wings down. Bold black marker stencil feathers with neon edges, no poop, no text.
Strict 12 isolated poses in 3 columns x 4 rows. Keep identity and framing consistent across each row, all cells separated by actual transparent space. No caption labels, no rectangles, no watermarks.
```
