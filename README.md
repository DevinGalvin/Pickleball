# Pickle League

Weekly pickleball league app: check-in, court rotation, tap-to-score, standings, live bracket, history.

- Static page, hosted on GitHub Pages.
- Data lives in one Firebase Realtime Database document (`/league/data`). Any phone with the link can view.
- Two PINs. The group PIN (`/pin`) runs a night: check in, score, end the night. The admin PIN (`/admin`) fixes saved scores, deletes nights, edits the roster and runs the season. See `RULES.md` for the rules and setup.
- Install on a phone: open the link in Safari, Share, Add to Home Screen.

## Editing the app

`rally-night.html` is the source (the Claude artifact is a stale copy). `build-live.py` adds the Firebase sync, the group and admin PIN gates and the PWA head and writes `index.html`. Edit the source, run `python3 build-live.py`, commit both, push.

## Courts

With 8 or more checked in, the check-in screen offers a second court. It is never on by default because that court isn't always free. Two courts play as rounds: both scores go in, then the next round is drawn. Flip it on or off mid-night from the Players screen; any score already saved in the round is kept.

## Late arrivals and hand-picked games

- Running late: under the check-in roster, "Anyone running late?" marks a checked-in player as late. He counts as coming but is never drawn. On the court screen he shows in the Sitting panel with "Here now"; one tap puts him in the next draw, level with whoever has played least so he isn't run every game to catch up.
- Drawn but not there: Change on the matchup, "Someone isn't here yet", marks him late and redraws that game.
- Pick the players: Change on the matchup, "Pick the players". Two taps for Side A, two for Side B. It counts in the rotation like any drawn game.
