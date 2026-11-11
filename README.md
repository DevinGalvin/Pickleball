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
