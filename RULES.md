# Database rules

Paste this into Firebase console → Realtime Database → Rules → Publish.

```json
{
  "rules": {
    ".read": false,
    ".write": false,
    "league": {
      ".write": "root.child('pin').exists() && newData.child('k').isString() && newData.child('k').val().beginsWith(root.child('pin').val() + ':') && newData.child('k').val() !== data.child('k').val()",
      "data": { ".read": true }
    }
  }
}
```

What it does

- Anyone with the link can read `/league/data` (the whole league). Nothing else is readable, including `/pin` and `/league/k`.
- A write to `/league` is accepted only when it carries a `k` of the form `<PIN>:<nonce>` where `<PIN>` matches `/pin`, and that `k` differs from the one already stored. So a saved token cannot be replayed, and a write that leaves `k` alone (for example a PUT to `/league/data` by someone who found the URL) is rejected because the merged `k` equals the stored one.
- The PIN is changed by editing `/pin` in the console. Every phone will be asked for the new one on its next change.

Layout

```
/pin            "01950"               not readable
/league/data    { ...league... }      readable
/league/k       "01950:m3x9..."       not readable, rotates on every write
```
