# Pickle League

Weekly pickleball league app: check-in, court rotation, tap-to-score, standings, playoffs, history.

- Static page, hosted on GitHub Pages.
- Data lives in one Firebase Realtime Database document (`/league/data`). Any phone with the link can view.
- Two tiers. The group PIN (`/pin`) runs a night: check in, score, end the night. The organizer code (`/admin`) fixes saved scores, deletes nights, edits the roster and runs the season. See `RULES.md`.
- Each phone is asked "Who are you?" once. Your name sits top right; tap it to see your role, who the organizers are, and to become one.
- Install on a phone: open the link in Safari, Share, Add to Home Screen.

## Editing the app

`rally-night.html` is the source (the Claude artifact is a stale copy). `build-live.py` adds the Firebase sync, the group and admin PIN gates and the PWA head and writes `index.html`. Edit the source, run `python3 build-live.py`, commit both, push.

## Type standard

The heavy display face (Barlow Condensed 800) comes in four sizes, set as variables at the top of the stylesheet. Use these and no others:

| Token | Size | For |
|---|---|---|
| `--t-hero` | 34px | The one big number on a screen, in the hero card only |
| `--t-title` | 24px | Page titles and a card's main number |
| `--t-num` | 20px | Numbers in rows, tiles and lists; buttons |
| `--t-tag` | 13px | Small caps tags |

- Player names are never in the heavy face: body face, weight 600, 15 to 24px.
- At most one hero-size number per screen.
- Exception: scoring on Game Night (names on the court, the score sheet and its pad, the result stamp) is sized to be read at arm's length, and the header logo is the logo.

## Courts

With 8 or more checked in, the check-in screen offers a second court. It is never on by default because that court isn't always free. Two courts play as rounds: both scores go in, then the next round is drawn. Flip it on or off mid-night from the Players screen; any score already saved in the round is kept.

## Late arrivals and hand-picked games

- Running late: under the check-in roster, "Anyone running late?" marks a checked-in player as late. He counts as coming but is never drawn. On the court screen he shows in the Sitting panel with "Here now"; one tap puts him in the next draw, level with whoever has played least so he isn't run every game to catch up.
- Drawn but not there: Change on the matchup, "Someone isn't here yet", marks him late and redraws that game.
- Pick the players: Change on the matchup, "Pick the players". Two taps for Side A, two for Side B. It counts in the rotation like any drawn game.
- Leaving or arriving mid-night: "Who's here" on the court screen has "Someone's done for the night" and "Someone just got here". Neither sends anyone back to check-in. Tapping a name in the Sitting panel also offers "Done for the night".
- A night nobody ended: from 6am the next morning, the first phone to open the app is asked to save it to History (or clear it if nothing was scored).

## Guests

- A guest is a one-night sub. On check-in, "+ Add a player or guest" asks for a name, then "Joining the league" or "Guest, just tonight". Mid-night, "Who's here" has "A guest just got here". Anyone with the group PIN can add one.
- He plays in the rotation like anyone else and shows on that night's board with a GUEST tag. He is never in the standings, Night MVP, the records, partners, rivals or Season Wrapped. Everyone else's games with him count as usual.
- How: guests live in `tonight.guests` (never in the roster) and each game one plays is stamped `gu:[name]`. `tally()` skips a stamped player unless asked for the whole night. The list empties when the night ends.
- No guests on playoff night. A game with a guest in it can't be the Longest game record.

## Season Wrapped

- The night recap for a whole season: champions (from the playoff night), final standings, then awards: most Night MVPs, most improved (rank at the halfway point against the final rank; needs 4 nights and a climb of 2+ spots), iron man, dream team (3+ games together), hot hand, best night. "Your season" shows when the name on this phone played: finish, record, best night, MVP nights, best partner, nemesis, favorite victim.
- Nothing is stored. It is worked out from that season's saved nights, so a corrected score corrects it. With no playoff night the top card is the season winner.
- Where: ending a season lands the organizer on it. Every other phone gets a sheet once, the next time it opens the app (`pickle-wrapped-seen` on the phone; not during a night, not after 14 days, `WRAP_DAYS`). It stays in History: the latest one above Records, each one above its own nights under Nights.
- Play the playoffs before ending the season, or the wrap has no champions.
- Share to the group sends the results as text.
- Type: names in the body face, award values too. The display face is only on the page title, the hero number and the standings column.

## Champions banners

- Every finished season that crowned champions gets a banner at the top of Playoffs, newest first. One banner hangs centered; with more they sit side by side and scroll. Tap one to open that season's wrap.
- Drawn in the page (no image): rod, pointed bottom, stitched trim, court blue, with the header's own ball as the emblem. Only CHAMPIONS is in the heavy face.
- Hidden while a playoff night is running. Nothing is stored: it comes from the same season facts as the wrap.

## Night recap

- Tapping a night in History opens its recap. "The night" is the same for everyone: Night MVP, the final board, the closest game and the biggest win, best pair (3+ games together), beat the spread, standings movers, then every game. "Your night" shows only when the name on this phone played: record, games in order, best partner, +/- next to each partner, and the standings move.
- Nothing is stored for the recap. It is worked out from the saved scores, so a corrected score corrects it.
- Share to the group sits under "The night" only and sends one picture of the night. "Your night" has no share button. Where a phone can't share pictures it copies the night as text.
- The recap sheet: the first time a phone opens the app after a night ends, it shows that night once, then "See full recap". Only the latest night, only if that name played (a phone with no name gets the night's MVP), never once the next night has started or after 3 days (`RECAP_DAYS`), never for a playoff night, and never twice (`pickle-recap-seen` on the phone). The phone that ends the night lands on the full recap instead.

## Stats

- Player page: current streak, record over the last ten games, and nights finished as Night MVP.
- Rivals on the player page: Nemesis (the opponent he has the worst record against) and Favorite victim (the best). Same sample rule as partners: 3+ games against, and only a losing or winning record counts.
- Standings arrows: a small ▲2 / ▼1 under the rank shows the move since the last night (season view only, from the second night on). No arrow means no move or a first night.
- Standings sparkline: a small gray line in each row is that player's running +/- over his last 20 games (`SPARK_GAMES`). The end dot is green or red for the net over that stretch. Season view only; no line until 3 games.
- History always opens on Records (Nights is the other half of the toggle). Records is an infographic of seven panels: streaks (win, hot hand, cold spell), the Night MVP race, best and worst night, partners (Dream team and Bad chemistry: the best and worst win record for a pair with 3+ games together; before any pair has 3, the pair closest to it), the longest game, the bagel shop (11-0s served and eaten) and iron man. It covers all seasons and only finished nights. Shapes and type only: no player faces. Player names are in the body face, here and in the night recap; the display face is for numbers and page titles.
- Streak callout: a player on 5+ straight wins this season (`STREAK_MIN`) gets a small lime W6 tag under his name on the court. When that streak is ended, the phone that saved the score shows "Kevin & Tom ended Joe's 6-game streak" for 4 seconds. Wins only; losing streaks stay in Records. Not on playoff night. The night recap gets a "Win streaks" card when a streak of 5+ is still going after that night or was ended during it (with who ended it).
- Night MVP is the best +/- of the night; ties go to more wins, then fewer games. There is no minimum number of games.
