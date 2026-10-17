# Device support

**Primary target: VMOS (virtual Android). No target is supported yet; nothing has been imported or booted.** [Certain]

| Target | Import custom ROM? | Format | Android / ABI (public info) | Status |
| --- | --- | --- | --- | --- |
| VMOS Pro (Android app) | Yes, "Import local ROM" [Likely] | .zip (zip-in-zip or zip-in-7z), internal storage, no spaces in path [Likely] | 4.4 (old app), 5.1.1, 7.1.2, 9.0; armv7 and/or arm64 [Likely] | **CONFIRMED primary target (Don uses VMOS Pro, 2026-10-17)**, not yet tested |
| VMOS Cloud (cloud phones) | Via their ROM community / publish flow [Likely] | Unknown | CloudROM-13/14 (Android 13/14) [Likely] | Needs VMOS collaborator access |
| VMOS Edge (box/PC host) | **No** — only signed official images [Likely, official docs] | Signed official image | Android 10/13/14/15 | Not viable for custom ROMs |
| Physical phones | — | — | — | Deferred |

Profiles: profiles/virtual-template.json (rejected by design until filled with a verified VMOS product/version).
Known gap: the validator currently requires android_api >= 28, which rejects VMOS Pro 5.1 (API 22) and 7.1.2 (API 25) ROMs; to be fixed in Phase V1.
Blocking input from Don (product = VMOS Pro, confirmed): app version, host phone model/ABI, and which guest Android version he uses.
