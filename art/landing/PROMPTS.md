# Run the City — poster artwork

## Standing hero restored — 2026-10-04

The hero uses the original `crews-poster.webp` (1536 × 1024) on desktop and mobile, with its original responsive sizing and a matching preload. The earlier image variants remain available locally.

## White crew leader pose correction — 2026-10-04

This earlier version used `crews-dynamic-v2.webp` (1536 × 1024, WebP quality 88, original generated alpha preserved); the generated master is saved locally as `crews-dynamic-v2.png`. Built-in ImageGen edited `crews-dynamic.png` to give the woman in white a natural forward stride, aligned torso, balanced arms, and proportional legs. The other five characters retain their composition and poses. The earlier dynamic assets remain available locally for comparison.

Final edit prompt:

```text
Use case: precise-object-edit.
Edit target: the supplied Run the City six-character hero foreground.
Change ONLY the pose of the silver-haired woman in WHITE in the foreground centre-right. Her current torso twist and oversized leg look anatomically awkward. Give her a confident, dynamic, anatomically natural athletic FORWARD STRIDE: chest and hips aligned in the same three-quarter direction toward the viewer, torso upright with a slight forward lean, her near leg stepping forward with a modest natural bend at the knee and a proportional white sneaker planted lower-right, her other leg trailing behind toward centre with a clearly connected hip-knee-ankle chain. One elbow bent naturally with her hand held near upper chest, the opposite arm swinging back beside the hip. Keep both shoulders relaxed, neck aligned, five natural fingers on each visible hand, and believable limb lengths. No extreme back arch, no backward torso rotation, no sideways reaching arm, no giant foreshortened shoe, no acrobatic split. Her jacket should sit naturally on BOTH shoulders, open at front over the original white top. Keep her original recognizable face, silver ponytail, white cropped jacket and white cargo trousers, accessories, cyan and magenta rim light, clothing textures and semi-realistic painterly rendering.
Maintain her approximate position, scale and visual prominence beside the red leader; her head stays near its current height and remains clearly visible. Make this a distinct upright striding silhouette that complements the red man's deep forward lunge, not a copy of his pose. Keep the other FIVE people exactly as shown: identical faces, expressions, hands, poses, outfits, colour, size, position, and layering. Green crouching left, orange leaping upper-left, red lunging centre-left, blue turning upper-right, purple pivoting right must not be redesigned, moved, or re-posed. Preserve composition, landscape 1536x1024 framing and existing neon rendering. Any gaps newly exposed around her body must be transparent or show the original neighbouring character only where appropriate. No added characters or props. Keep the real transparent alpha background including gaps between limbs; no backdrop or colour haze, no lettering or watermark.
```

## Dynamic hero poses — 2026-10-04

Generated with the built-in ImageGen tool. The initial dynamic hero used `crews-dynamic.webp` (1536 × 1024, original alpha preserved, WebP quality 88); the original generated master is saved locally as `crews-dynamic.png`. The six existing characters retain their faces, costumes, crew colours and neon lighting, with distinct action poses inspired by the user's three anime ensemble posters. The original assets remain available for the join section and entrance animation. Reference posters are not shipped.

Final prompt:

```text
Use case: compositing / stylized-concept.
Asset type: transparent six-character foreground artwork for the existing Run the City landing page, landscape 1536 x 1024.
Input image 1 is the EDIT TARGET and character identity/costume/rendering reference: the current six adult cyberpunk crew leaders. Input images 2, 3 and 4 are COMPOSITION AND POSE REFERENCES ONLY: take their dramatic diagonal action lines, strongly varied silhouettes, staggered head heights, foreshortening and layered ensemble-poster depth. Do not reproduce their characters, weapons, costumes, logos or text.
Primary request: completely re-pose this exact original six-person cast into a spectacular, dynamic ensemble action key visual. Preserve their recognizable faces, hairstyles, adult proportions and streetwear colour identities: green jacket man at left, orange jacket woman behind left, crimson long-coat man foreground centre-left, silver-haired white outfit woman foreground centre-right, cobalt jacket man behind right, curly-haired purple long-coat woman at right. Maintain the target's premium painterly semi-realistic 3D/cel-shaded cyberpunk finish and detailed fabrics, cyan edge lighting, hot magenta highlights and occasional acid yellow reflections.
Composition: an asymmetrical interlocking wedge, not a lineup. Six immediately different poses and six different lines of action. Green man very low in a deep sideways landing crouch, one hand near the ground and one knee bent outward. Orange woman higher and farther back in a bold airborne diagonal parkour leap, one knee sharply raised and the other leg trailing, one arm high overhead and the other extended back for balance. Red leader larger in front, in an aggressive forward diagonal lunge toward the viewer, torso leaning, one foreshortened forearm and open hand reaching forward, red coat tails flying backward. White leader twisting dynamically in the opposite direction in a wide split stance, torso rotating with head looking back toward the viewer, one arm extended sideways and the other bent high; silver ponytail and open white jacket swept into an arc. Cobalt man more upright in rear three-quarter back/profile view, turning his head over shoulder with weight on the back foot and one arm bent across torso, a clear still counterpoint to the leaping and crouching figures. Purple woman at far right in a sweeping lateral pivot/low lunge, one leg extended and one bent, one arm thrown outward, purple coat and curls sweeping far to the right. These must be six very different silhouettes; no repeated running poses, no synchronized arms, no fashion-model lineup.
Faces must remain readable and not hidden by others' limbs. Uneven head heights and depth: central leaders dominant, flanks supporting. Compact full-body group fills approximately 90% of the landscape frame, every person including shoes inside canvas, small transparent perimeter. Keep heads mostly in upper half but no isolated person extending vastly above rest. Anatomically believable hands, arms and legs, lively expressions and strong directional gaze.
MANDATORY actual transparent alpha background throughout all space outside people and gaps between limbs. No colour haze or gradient backdrop, no city, no floor, no environment, no panels or graphic dividers, no solid shadows behind the people, no lettering, no watermark, no weapons. Sharp detailed silhouettes, no baked motion blur. The existing website supplies the city and motion. Output only the new character group on genuine transparency.
```

Generated with the built-in ImageGen tool on 2026-09-26. The user's four poster references informed the palette, graphic print treatment, towering architecture, and illustrated crew styling. Reference images are not shipped with the site.

Published assets:

- `city-poster.jpg`: the final illustrated street-level city plate (JPEG encoding of the generated PNG, 1536 × 1024).
- `crews-poster.png`: the final transparent six-person foreground plate (1536 × 1024, original generated alpha preserved).
- `city-street.jpg`: a second illustrated environment for the deeper street chapters (JPEG encoding of the generated PNG, 1536 × 1024).
- `run-the-city.svg`: an original code-native vector wordmark with custom letter paths, not a generated raster image.

The logo lighting, parallax, scroll reveals, rain, fog, and controls are live HTML/CSS/JavaScript in `index.html`. Neon lettering, the helicopter mesh, and the koi, lucky-cat and ticker holograms reuse the game’s vector renderers. The soundtrack reuses `amb_city`, `start`, `horn_1`, `horn_2`, and `ui_confirm` from the existing sound packs.

## Final city prompt

Inputs: original generated city plate as the edit target; the user's cyan/pink illustrated street poster and yellow tower poster as visual references.

```text
Use case: style-transfer. Input image 1 is the EDIT TARGET: the original city background plate. Input images 2 and 3 are ART DIRECTION REFERENCES ONLY, not content to copy.
Transform the first city image into premium illustrated cyberpunk movie-poster key art: keep its extreme street-level looking-up camera, central immense tower, rain-wet pavement, architectural layout and separate environment-only composition exactly recognizable. Change the rendering from polished photoreal to a beautiful hybrid of cinematic 3D depth and bold painterly cel-shaded concept art. Follow reference 2's rich turquoise/cyan atmospheric depth, inky blue shadows, visible brush texture, rough printed edges, saturated magenta signs, and acid yellow-green light. Reference 3 contributes monumental tower scale and graphic silhouettes. The light should be brighter and more readable than the original dark background, rich teal haze filling the canyon and illuminated windows. Scattered hot pink and acid-yellow abstract billboard panels, fine overhead wires, slightly distressed print texture; maintain the sense of separate deep architectural planes. Central upper-middle tower front still has a relatively dark uncluttered area to put our own luminous website title on.
Keep a panoramic 1536x1024 environment plate, no characters, no prominent cars, no words, no lettering, no brand logos, no watermark, no UI. Do not reproduce the reference characters or their logos. Original Run the City world. This must still be a low-angle street canyon and a towering central skyscraper, not an aerial view.
```

## Final crew prompt

Inputs: original generated transparent crew plate as the edit target; the user's illustrated street and ensemble posters as style references; the final generated city plate as the lighting reference.

```text
Use case: style-transfer. Image 1 is the EDIT TARGET: isolated six-crew foreground. Images 2 and 3 are STYLE REFERENCES only. Image 4 is the background this cutout will be placed on; match its painterly cyberpunk neon lighting.
Re-render the six adult crew leaders of image 1 as striking original illustrated cyberpunk movie poster characters, a hybrid of deep 3D volumes and painterly cel-shaded concept art. More angular silhouettes, inky deep navy shadows, hand-painted fabric highlights, slight distressed print texture, eccentric futuristic street fashion with asymmetric jackets, interesting haircuts and subtle tech detailing. Keep their exact six gang colour identities and order: green, orange, crimson red, white, cobalt blue, royal purple. Keep the same full-body poses, ensemble silhouette, distinct faces, camera at knee height looking UP, full feet and proportional human anatomy. Cyan edges, hot magenta glow and acid-yellow highlights should make the clothes feel present in image 4. Preserve all six, the two central leaders and wider flanking cast. No weapons; the bold streetwear and attitude tell the story.
MANDATORY: genuine transparent alpha background, all pixels outside the six people transparent, including gaps between limbs. NO city, NO street, NO colored backdrop, NO floor, NO lettering, no logo or watermark. Keep the full isolated group inside a landscape 1536x1024 frame with a little transparent margin. Do not reproduce any existing characters from the style references. This is an original Run the City ensemble.
```

## Final street district prompt

Input: the final city plate as a style and world reference. Generated with the built-in ImageGen tool.

```text
Use case: stylized-concept. The supplied city artwork is a STYLE AND WORLD REFERENCE, not an edit target. Generate a new original 1536x1024 wide background plate that continues this same Run the City cyberpunk world at street level. We are now deep inside a narrow dense neon entertainment district: layered storefronts, recessed club entrances, immense buildings, overhead cables, stacked balconies, glowing empty billboard frames at different depths, a wet road running diagonally into the distant mist. Camera slightly low looking along and up the street, strong cinematic perspective, AAA rendered depth mixed with painterly graphic-novel cel shading and distressed print texture. Palette: ink navy and cyan haze, hot magenta storefront illumination, acid yellow highlights. Rich details at the left and right, clear relatively dark central midground for live text and holograms to be overlaid in HTML. Several blank cyan and pink translucent holographic panel shapes float near shop fronts in the distance. No people in foreground, no legible words or logos, no watermarks, no UI. Avoid making a copy of the original central tower composition: this is the street inside the city, a new chapter of the same movie poster. One continuous environment illustration.
```

## Hero entrance — 2026-09-27

Built-in ImageGen mode. Reference: existing `crews-poster.png`. Final asset: `art/landing/crews-running.webp` (transparent, 1400 × 630). Existing city and group images also have compressed WebP siblings, used by the website. The running sprite is split into independent left/right CSS layers, followed by one brief blur/flash and the original group pose. No video or animation loop.

Final prompt:

```text
Use case: stylized-concept. Create a transparent PNG sprite asset for this website's cinematic hero entrance, using the supplied six-person image as character/costume reference. Landscape wide canvas. Left half: the green jacket man, orange jacket woman and red coat man sprint dynamically to the RIGHT, towards center. Right half: white outfit woman, blue jacket man and purple coat woman sprint to the LEFT towards center. Entire bodies including shoes visible, bent legs in energetic running strides and arms pumping, slightly low street camera, matching realistic glossy neon cyberpunk rendered style and magenta/cyan rim light. Keep a clear transparent vertical gap at the exact center dividing the two trios so the website can independently move each half with CSS. Genuine transparent alpha background everywhere behind people, no floor, no scene, no smoke, no text, no logo. All six distinct identities and costume colours preserved. They run towards each other, not towards camera; view is three-quarter side profiles. Sharp silhouettes, no baked-in motion blur. This is the running phase only; the existing image remains final group pose.
```

Game artwork previously embedded as base64 in `index.html` now lives in `art/game/` using content-hashed filenames. Preserve these external references when regenerating art.

Hero timing revision: 0.95-second anime-style entrance; brief anticipation, fast dash with reused-sprite afterimages and radial speed lines, one brief flash, then a short group-pose shake. No additional raster assets.
