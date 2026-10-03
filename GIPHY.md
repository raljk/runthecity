# Live GIF reactions

Trash talk uses live GIPHY Search results for the game's cash, power, victory, police, betrayal, deal, robbery, and payback themes, arranged in two rows of four choices. A separate Distractions section offers Emote, Booty, Sexy, and Party mode in one row. All searches retain the `pg-13` rating ceiling. Both ordinary reactions and targeted distractions use GIFs; the old illustrated reactions and four splat choices are no longer offered or loaded. Whispers remain.

## Configuration and publishing

Create a Web **API** app at https://developers.giphy.com/dashboard/ and set `window.RTC_GIPHY_API_KEY` in `giphy-config.js`. This is a public browser key, not a server secret. Never copy any other keys from `.env` into published files. The static game does not read `.env` at runtime.

Publish `index.html`, `giphy.js`, `giphy-config.js`, and `art/talk/powered-by-giphy.png` together with the existing assets. The official static attribution mark came from https://media.giphy.com/giphy-attribution-marks.zip and is displayed in the picker and separately in the screen corner while reactions are visible.

Beta keys currently allow 100 API calls per hour. Apply for production access in the GIPHY dashboard before a public launch; GIPHY reviews the integration and discusses pricing. Search is submitted explicitly rather than on every keystroke. Each request loads 12 results. More GIFs requests the next page.

## Behaviour

- Requests and media loads go directly from the browser to GIPHY. No server proxy or stored media catalogue is used. Closing the picker cancels in-flight requests and discards its results; reopening requests fresh results for Get paid. GIPHY ranks results for each topic; these are live searches, not a filtered global Trending feed. An empty search returns to Get paid.
- Results use GIPHY's `pg-13` rating ceiling, preserve provider order, and keep media URLs intact. Anonymous per-page analytics report views, clicks, and successful sends.
- Search input, selection and results survive game redraws. Reduced motion displays the provider's still rendition. Missing credentials, offline access, API limits and failed requests show recoverable states without blocking play.
- The relay carries a small GIF metadata packet, never image bytes. The host and each receiver validate the media host, path, dimensions, rating and field types. GIFs retain the five-per-12-seconds / 1.2-second reaction cooldown. Game state and undo do not include GIFs.
- A sent GIF appears locally and on the table / board-view screens for a few seconds, without a frame, background, or name footer. Its original aspect ratio and any transparency are preserved. A single GIPHY credit appears in the screen corner while GIFs are visible; it does not intercept clicks. Other players' phone controls remain clear.
- Under **Distract [player]**, **Choose a distraction GIF** opens the same picker in a clearly labelled targeting mode. A selection goes to that player's board and travels toward their seat on the table screen. It is limited to once per sender per turn and one per recipient every six seconds. The chosen recipient and turn are fixed; a turn change invalidates the selection rather than silently retargeting it. Distractions are unavailable on your own turn, during a fight, or after the turn clock expires.
- Targeted GIFs retain the existing `splat` message kind with validated GIF metadata and a turn token; old art-only packets are rejected. The recipient's overlay stays inside the board, preserves its media element across redraws, and fades after 4.2 seconds of playback (with a bounded three-second load wait). Reload host and player pages together when publishing this update.

## Local verification

The existing `dev/` folder is intentionally ignored by Git. Focused checks live in `dev/giphy-client.test.js` and `dev/gif-game-test.js`:

```sh
node --test dev/giphy-client.test.js
node dev/gif-game-test.js
node dev/unit.js
node dev/guide.js
python3 dev/check.py index.html
```

API documentation: https://developers.giphy.com/docs/api/
