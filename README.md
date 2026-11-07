# Pickle League

Weekly pickleball league app: check-in, court rotation, tap-to-score, standings, live bracket, history.

- Static page, hosted on GitHub Pages.
- Data lives in one Firebase Realtime Database document (`/league`). Any phone with the link can view; scoring needs the group PIN (`/pin`).
- Install on a phone: open the link in Safari, Share, Add to Home Screen.

## Firebase rules

Test mode rules expire after 30 days. In the Firebase console, Realtime Database, Rules tab, paste:

```json
{
  "rules": {
    ".read": true,
    ".write": true
  }
}
```

The link is the only secret. That's fine for a friends group; the PIN stops a forwarded link from editing, not a determined person.

## Editing the app

`rally-night.html` is the source (the Claude artifact is a stale copy). `build-live.py` adds the Firebase sync, PIN gate and PWA head and writes `index.html`. Edit the source, run `python3 build-live.py`, commit both, push.

## Courts

With 8 or more checked in, the check-in screen offers a second court. It is never on by default because that court isn't always free. Two courts play as rounds: both scores go in, then the next round is drawn. Flip it on or off mid-night from the Players screen; any score already saved in the round is kept.
