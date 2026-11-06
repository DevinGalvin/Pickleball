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

`index.html` is generated from the demo artifact by `build-live.py` (kept with the Claude session). Edit there, rebuild, push.
