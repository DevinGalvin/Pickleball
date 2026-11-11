# Database rules

Two tiers. The group PIN runs a night. The admin code changes anything already saved.

| | Group PIN | Admin code |
|---|---|---|
| Check in, courts, start the night | yes | yes |
| Score tonight, Undo, swap a matchup, End night | yes | yes |
| Add a player | yes | yes |
| Fix or delete a saved game (tonight or History) | no | yes |
| Delete a night | no | yes |
| Rename or remove a player | no | yes |
| Season settings, pairing, end the season | no | yes |

A corrected game carries a stamp everyone sees: "Edited by Evan, Nov 10, 7:42 PM · was 11–7".

## Setup

1. Firebase console → Realtime Database → Data. At the root, next to `pin`, add `admin` with the admin code as a lowercase string (a word is fine; the app lowercases what is typed, so capitals don't matter).
2. Rules tab → paste the block below → Publish.
3. In the app: tap your name (top right) → "I'm an organizer" → enter the code. Once per phone. The app calls this role Organizer; the database path is still `/admin`.

```json
{
  "rules": {
    ".read": false,
    ".write": false,
    "league": {
      "k": {
        ".write": "newData.isString() && newData.val() !== data.val() && ((root.child('pin').exists() && newData.val().beginsWith(root.child('pin').val() + ':')) || (root.child('admin').exists() && newData.val().beginsWith('A' + root.child('admin').val() + ':')))"
      },
      "data": {
        ".read": true,
        ".write": "newData.parent().child('k').isString() && newData.parent().child('k').val() !== data.parent().child('k').val() && root.child('admin').exists() && newData.parent().child('k').val().beginsWith('A' + root.child('admin').val() + ':')",
        "players": {
          ".write": "newData.parent().parent().child('k').isString() && newData.parent().parent().child('k').val() !== data.parent().parent().child('k').val() && root.child('pin').exists() && newData.parent().parent().child('k').val().beginsWith(root.child('pin').val() + ':')"
        },
        "tonight": {
          ".write": "newData.parent().parent().child('k').isString() && newData.parent().parent().child('k').val() !== data.parent().parent().child('k').val() && root.child('pin').exists() && newData.parent().parent().child('k').val().beginsWith(root.child('pin').val() + ':')"
        },
        "updatedAt": {
          ".write": "newData.parent().parent().child('k').isString() && newData.parent().parent().child('k').val() !== data.parent().parent().child('k').val() && root.child('pin').exists() && newData.parent().parent().child('k').val().beginsWith(root.child('pin').val() + ':')"
        },
        "nights": {
          "$i": {
            ".write": "!data.exists() && newData.exists() && newData.parent().parent().parent().child('k').isString() && newData.parent().parent().parent().child('k').val() !== data.parent().parent().parent().child('k').val() && root.child('pin').exists() && newData.parent().parent().parent().child('k').val().beginsWith(root.child('pin').val() + ':')"
          }
        }
      }
    }
  }
}
```

## What the rules enforce

- Anyone with the link can read `/league/data`. Nothing else is readable: not `/pin`, not `/admin`, not `/league/k`.
- Every write is one update that carries a fresh `/league/k`: `<PIN>:<nonce>` for the group, `A<admin code>:<nonce>` for an admin. `k` must differ from the stored one, so a saved token can't be replayed and a write that leaves `k` alone is rejected.
- Group token: may write `tonight`, `players`, and may create a night that doesn't exist yet (`nights/<next index>`, which is what End night does). It cannot change or delete an existing night, or touch `seasons` or `pairing`.
- Admin token: may write anything under `/league/data`.
- Hard-locked by the database: saved nights, seasons, pairing. Locked by the app only: fixing a game from tonight that is still in progress, and rename/remove on the roster. Someone with the group PIN and the skills to talk to the database directly could get past those two; once the night is ended it is hard-locked.
- Change either PIN by editing `/pin` or `/admin` in the console. Phones are asked for the new one on their next change.

Tested in the Firebase emulator (28 permission checks plus a two-phone run of the app).

## Who the app thinks you are

- On first open each phone is asked "Who are you?" and remembers the name. It is not a login and grants nothing; it lets the app show your role and put a name on a corrected score.
- `/league/data/organizers` is the list of organizer names everyone sees. An organizer phone adds its own name; only the organizer code can write it.

## Layout

```
/pin            "01950"               not readable
/admin          "....."               not readable
/league/data    { ...league... }      readable
/league/k       "01950:m3x9..."       not readable, rotates on every write
```
