# Run the City — poster artwork

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
