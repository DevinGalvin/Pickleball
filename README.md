# Pickle League

Weekly pickleball league app: check-in, court rotation, tap-to-score, standings, playoffs, history.

- Static page, hosted on GitHub Pages.
- Data lives in one Firebase Realtime Database document (`/league/data`). Any phone with the link can view.
- Two tiers. The group PIN (`/pin`) runs a night: check in, score, end the night. The organizer code (`/admin`) fixes saved scores, deletes nights, edits the roster and runs the season. See `RULES.md`.
- Each phone is asked "Who are you?" once. Your name sits top right; tap it to see your role, who the organizers are, and to become one.
- Install on a phone: open the link in Safari, Share, Add to Home Screen.

## Editing the app

`rally-night.html` is the source (the Claude artifact is a stale copy). `build-live.py` adds the Firebase sync, the group and admin PIN gates and the PWA head and writes `index.html`. Edit the source, run `python3 build-live.py`, commit both, push.

## Courts

With 8 or more checked in, the check-in screen offers a second court. It is never on by default because that court isn't always free. Two courts play as rounds: both scores go in, then the next round is drawn. Flip it on or off mid-night from the Players screen; any score already saved in the round is kept.

## Late arrivals and hand-picked games

- Running late: under the check-in roster, "Anyone running late?" marks a checked-in player as late. He counts as coming but is never drawn. On the court screen he shows in the Sitting panel with "Here now"; one tap puts him in the next draw, level with whoever has played least so he isn't run every game to catch up.
- Drawn but not there: Change on the matchup, "Someone isn't here yet", marks him late and redraws that game.
- Pick the players: Change on the matchup, "Pick the players". Two taps for Side A, two for Side B. It counts in the rotation like any drawn game.
- Leaving or arriving mid-night: "Who's here" on the court screen has "Someone's done for the night" and "Someone just got here". Neither sends anyone back to check-in. Tapping a name in the Sitting panel also offers "Done for the night".
- A night nobody ended: from 6am the next morning, the first phone to open the app is asked to save it to History (or clear it if nothing was scored).

## Night recap

- Tapping a night in History opens its recap. "The night" is the same for everyone: Night MVP, the final board, the closest game and the biggest win, best pair (3+ games together), beat the spread, standings movers, then every game. "Your night" shows only when the name on this phone played: record, games in order, best partner, +/- next to each partner, and the standings move.
- Nothing is stored for the recap. It is worked out from the saved scores, so a corrected score corrects it.
- Share to the group sits under "The night" only and sends one picture of the night. "Your night" has no share button. Where a phone can't share pictures it copies the night as text.
- The recap sheet: the first time a phone opens the app after a night ends, it shows that night once, then "See full recap". Only the latest night, only if that name played (a phone with no name gets the night's MVP), never once the next night has started or after 3 days (`RECAP_DAYS`), never for a playoff night, and never twice (`pickle-recap-seen` on the phone). The phone that ends the night lands on the full recap instead.

## Stats

- Player page: current streak, record over the last ten games, and nights finished as Night MVP.
- History always opens on Records (Nights is the other half of the toggle). Records is an infographic of seven panels: streaks (win, hot hand, cold spell), the Night MVP race, best and worst night, partners (Dream team and Bad chemistry: the best and worst win record for a pair with 3+ games together; before any pair has 3, the pair closest to it), the longest game, the bagel shop (11-0s served and eaten) and iron man. It covers all seasons and only finished nights. Shapes and type only: no player faces. Player names are in the body face, here and in the night recap; the display face is for numbers and page titles.
- Night MVP is the best +/- of the night; ties go to more wins, then fewer games. There is no minimum number of games.
