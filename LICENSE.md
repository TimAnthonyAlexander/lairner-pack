# License and credits

## Third-party assets (CC0 1.0, public domain)

- **Kenney, Blaster Kit 2.1** (https://kenney.nl/assets/blaster-kit), CC0 1.0.
  Meshes in `source/kenney/` are Kenney's; grenade-a, grenade-b, smoke and
  colormap.png are voxelized into the grenade and smoke models. The blaster
  and silencer meshes were the gun models until 2026-11-01; every gun is our
  own model now.
- **Kenney audio packs** (https://kenney.nl/assets): RPG Audio, Impact
  Sounds, Interface Sounds, Sci-fi Sounds, CC0 1.0. Used for reloads,
  dry fire, hit tick, headshot, knife, grenade bounce, explosions.
- **The Free Firearm Sound Library** (Ben Jaszczak et al.,
  https://opengameart.org/content/the-free-firearm-sound-library), CC0 1.0.
  Gunshots until 2026-11-01 (Walther PPQ, Ruger Mark III, 1911, Carl Gustav
  M45, PPSh, AK-47, AR-15); no longer in the pack.

CC0 needs no attribution; we credit them anyway. Thank you, Kenney and the
Free Firearm Sound Library team.

## Provided by Tim

- `df.headshot.kill` (`pack/assets/lairner/sounds/df/headshot_kill.ogg`) comes from a sound provided by Tim
  (`source/tim/headshot.m4a`), trimmed to 0.43-1.62 s and downmixed to mono by `tools/sounds.py`.
- `df.headshot.hit` (`pack/assets/lairner/sounds/df/headshot_hit.ogg`) comes from a sound provided by Tim
  (`source/tim/headshot_dmg.m4a`), trimmed to 0.05-0.45 s and downmixed to mono by `tools/sounds.py`.
- The gunshots (`pack/assets/lairner/sounds/df/<weapon>/shot_<n>.ogg`) are Tim's own recordings
  (2026-11-01, `source/tim/shots/`), downmixed to mono, trailing silence cut and peak -1 dB by `tools/sounds.py`.
- The D-Eagle, AK, G18, M4-S, USP-S, MAC-10 and MP9 models are our own (cubes on the shared palette).

## Everything else

Everything else in this repository (the knife, bomb and defuse kit models,
font glyphs, HUD icons, pack.png, the synthesized sounds, the tools and
the way the sources were converted) is by lairner
(https://github.com/TimAnthonyAlexander), © 2026 lairner, made for the
lairner Minecraft server (`play.lairner.com`).
