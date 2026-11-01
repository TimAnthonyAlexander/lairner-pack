| `lairner:df/glock` | G18 | own |# lairner-pack
| `lairner:df/glock` | G18 | own |
| `lairner:df/glock` | G18 | own |Resource pack for the **Defusal** mode of the lairner Minecraft server
| `lairner:df/glock` | G18 | own |(`play.lairner.com`). Minecraft Java **26.3** (resource pack format 97).
| `lairner:df/glock` | G18 | own |The defusal server adds it on join and removes it on leave; the other
| `lairner:df/glock` | G18 | own |servers don't use it.
| `lairner:df/glock` | G18 | own |
| `lairner:df/glock` | G18 | own |**Download:** https://raw.githubusercontent.com/TimAnthonyAlexander/lairner-pack/main/dist/lairner-pack.zip
| `lairner:df/glock` | G18 | own |(SHA-1 in `dist/lairner-pack.zip.sha1`).
| `lairner:df/glock` | G18 | own |
| `lairner:df/glock` | G18 | own |![AK](previews/ak.png)
| `lairner:df/glock` | G18 | own |
| `lairner:df/glock` | G18 | own |## Contents (namespace `lairner`, all under `df/`)
| `lairner:df/glock` | G18 | own |
| `lairner:df/glock` | G18 | own |### Item models
| `lairner:df/glock` | G18 | own |
| `lairner:df/glock` | G18 | own |Set `item_model` on any base item, e.g. `minecraft:item_model="lairner:df/ak"`.
| `lairner:df/glock` | G18 | own |
| `lairner:df/glock` | G18 | own || id | Shown as | Source |
| `lairner:df/glock` | G18 | own ||---|---|---|
| `lairner:df/glock` | G18 | own || `lairner:df/glock` | G18 | Kenney blaster-k |
| `lairner:df/glock` | G18 | own || `lairner:df/usp` | USP | Kenney blaster-a + silencer-small |
| `lairner:df/glock` | G18 | own || `lairner:df/deagle` | D-Eagle | own |
| `lairner:df/glock` | G18 | own || `lairner:df/mac10` | M10 | Kenney blaster-c |
| `lairner:df/glock` | G18 | own || `lairner:df/mp9` | MP9 | Kenney blaster-i |
| `lairner:df/glock` | G18 | own || `lairner:df/ak` | AK | own |
| `lairner:df/glock` | G18 | own || `lairner:df/m4s` | M4-S | Kenney blaster-d + silencer-larger |
| `lairner:df/glock` | G18 | own || `lairner:df/knife` | Knife | own |
| `lairner:df/glock` | G18 | own || `lairner:df/bomb` | Bomb (C4) | own |
| `lairner:df/glock` | G18 | own || `lairner:df/kit` | Defuse kit | own |
| `lairner:df/glock` | G18 | own || `lairner:df/flashbang` | Flash | Kenney grenade-a, recolored white |
| `lairner:df/glock` | G18 | own || `lairner:df/smoke` | Smoke | Kenney grenade-a, recolored green |
| `lairner:df/glock` | G18 | own || `lairner:df/he` | HE | Kenney grenade-b |
| `lairner:df/glock` | G18 | own || `lairner:df/smoke_puff` | (item display) smoke cloud piece, 16 units wide, centered | Kenney smoke, gray |
| `lairner:df/glock` | G18 | own |
| `lairner:df/glock` | G18 | own |Guns and the knife set `hand_animation_on_swap: false`, so changing the
| `lairner:df/glock` | G18 | own |stack (ammo in components) doesn't replay the equip bob.
| `lairner:df/glock` | G18 | own |
| `lairner:df/glock` | G18 | own |Models: barrel along -Z, top +Y, centered on (8, 8, 8). One shared palette
| `lairner:df/glock` | G18 | own |texture (`lairner:item/df/palette`, 8x8 px per color so mipmaps stay clean).
| `lairner:df/glock` | G18 | own |Previews of every model in GUI, first person, third person and on the ground
| `lairner:df/glock` | G18 | own |are in `previews/` (rendered by `tools/preview.py` with the client's own
| `lairner:df/glock` | G18 | own |transform chain; real in-game look may differ slightly).
| `lairner:df/glock` | G18 | own |
| `lairner:df/glock` | G18 | own |### Sounds (`assets/lairner/sounds.json`)
| `lairner:df/glock` | G18 | own |
| `lairner:df/glock` | G18 | own || Event | Range (blocks) |
| `lairner:df/glock` | G18 | own ||---|---|
| `lairner:df/glock` | G18 | own || `lairner:df.glock.shot`, `df.mac10.shot`, `df.mp9.shot` | 56 |
| `lairner:df/glock` | G18 | own || `lairner:df.ak.shot`, `df.deagle.shot` | 72 |
| `lairner:df/glock` | G18 | own || `lairner:df.usp.shot`, `df.m4s.shot` (silenced) | 22 / 24 |
| `lairner:df/glock` | G18 | own || `lairner:df.reload.pistol` (2.2 s), `df.reload.smg` (2.7 s), `df.reload.rifle` (2.5 s) | 12 |
| `lairner:df/glock` | G18 | own || `lairner:df.dryfire` | 10 |
| `lairner:df/glock` | G18 | own || `lairner:df.hit`, `df.headshot` (for the shooter) | 8 |
| `lairner:df/glock` | G18 | own || `lairner:df.headshot.kill` (headshot kill), `df.headshot.hit` (headshot, no kill); world sounds at the victim, mono | 80 / 80 |
| `lairner:df/glock` | G18 | own || `lairner:df.knife.swing`, `df.knife.hit` | 12 / 16 |
| `lairner:df/glock` | G18 | own || `lairner:df.bomb.beep` | 24 |
| `lairner:df/glock` | G18 | own || `lairner:df.bomb.key` (one keypad press while planting), `df.bomb.plant` (armed) | 12 / 32 |
| `lairner:df/glock` | G18 | own || `lairner:df.bomb.defuse` (defuse starts), `df.bomb.defused` | 16 / 32 |
| `lairner:df/glock` | G18 | own || `lairner:df.bomb.explode` | 160 |
| `lairner:df/glock` | G18 | own || `lairner:df.flash.ring` (for the flashed player), `df.flash.explode` | 8 / 64 |
| `lairner:df/glock` | G18 | own || `lairner:df.grenade.bounce` | 20 |
| `lairner:df/glock` | G18 | own || `lairner:df.he.explode` | 96 |
| `lairner:df/glock` | G18 | own || `lairner:df.smoke.pop` (pop + 3.5 s hiss) | 32 |
| `lairner:df/glock` | G18 | own |
| `lairner:df/glock` | G18 | own |Shots have 2-3 variants picked at random. Range is the
| `lairner:df/glock` | G18 | own |`attenuation_distance`: the client fades linearly to silence at
| `lairner:df/glock` | G18 | own |`attenuation_distance * max(volume, 1)`. Play them with volume 1 (lower for
| `lairner:df/glock` | G18 | own |quieter) and send them per player (`Player#playSound(Location, ...)`):
| `lairner:df/glock` | G18 | own |`World#playSound` only sends to players within `16 * max(volume, 1)` blocks.
| `lairner:df/glock` | G18 | own |
| `lairner:df/glock` | G18 | own |### Font `lairner:df` and HUD
| `lairner:df/glock` | G18 | own |
| `lairner:df/glock` | G18 | own || Char | What | Use |
| `lairner:df/glock` | G18 | own ||---|---|---|
| `lairner:df/glock` | G18 | own || `` | crosshair | title |
| `lairner:df/glock` | G18 | own || `` | hit marker | title |
| `lairner:df/glock` | G18 | own || `` | headshot marker | title |
| `lairner:df/glock` | G18 | own || `` | full-screen white flash | title |
| `lairner:df/glock` | G18 | own || `` `` `` `` | bomb, kit, armor, helmet icons | action bar (normal line height) |
| `lairner:df/glock` | G18 | own || ``-`` | space -1, -2, -4 ... -128 | layout |
| `lairner:df/glock` | G18 | own || ``-`` | space +1, +2, +4 ... +128 | layout |
| `lairner:df/glock` | G18 | own |
| `lairner:df/glock` | G18 | own |Title glyphs are centered on the screen: the title is drawn at 4x scale
| `lairner:df/glock` | G18 | own |from the screen center with text y = -10, so a glyph of height H is
| `lairner:df/glock` | G18 | own |centered with ascent H/2 - 3; images have an even width and an invisible
| `lairner:df/glock` | G18 | own |(alpha 1) pixel in the last column so the measured width centers them
| `lairner:df/glock` | G18 | own |exactly. Send them as the title with `"font": "lairner:df"` and
| `lairner:df/glock` | G18 | own |`"shadow_color": 0` (titles draw a shadow otherwise). Fade with the
| `lairner:df/glock` | G18 | own |title times.
| `lairner:df/glock` | G18 | own |
| `lairner:df/glock` | G18 | own |**Flash:** `` is a 32x16 white image drawn 1024 text units high and
| `lairner:df/glock` | G18 | own |2048 wide; at title scale that is 8192 GUI pixels wide and 4096 high, more than the
| `lairner:df/glock` | G18 | own |screen at any GUI scale up to 8K at GUI scale 1, so it covers the whole
| `lairner:df/glock` | G18 | own |screen. The title fade-out fades it. Alternative that is exact at any
| `lairner:df/glock` | G18 | own |window size: an `equippable` head item with
| `lairner:df/glock` | G18 | own |`camera_overlay: "lairner:df/flash_<10..100>"` (ten opacity steps are in
| `lairner:df/glock` | G18 | own |`textures/df/`), stepped down each tick.
| `lairner:df/glock` | G18 | own |
| `lairner:df/glock` | G18 | own |**Vanilla overrides** (only while this pack is loaded): the crosshair
| `lairner:df/glock` | G18 | own |sprite is a CS-style static crosshair (four lines, gap), and the food bar
| `lairner:df/glock` | G18 | own |sprites are transparent (sprint is blocked by keeping food at 6).
| `lairner:df/glock` | G18 | own |
| `lairner:df/glock` | G18 | own |## Layout
| `lairner:df/glock` | G18 | own |
| `lairner:df/glock` | G18 | own |```
| `lairner:df/glock` | G18 | own |pack/                 the pack as zipped (pack.mcmeta, pack.png, assets/)
| `lairner:df/glock` | G18 | own |dist/                 lairner-pack.zip (+ .sha1), committed for the raw URL
| `lairner:df/glock` | G18 | own |source/kenney/        the Kenney meshes and colormap the models come from
| `lairner:df/glock` | G18 | own |previews/             renders of every model
| `lairner:df/glock` | G18 | own |tools/
| `lairner:df/glock` | G18 | own |  build.py            regenerate models + textures, validate, zip, print SHA-1
| `lairner:df/glock` | G18 | own |  models.py           OBJ -> cuboid models, own models, palette, item definitions
| `lairner:df/glock` | G18 | own |  voxelize.py         voxelizer and box merger
| `lairner:df/glock` | G18 | own |  textures.py         font glyphs, HUD icons, flash overlays, hidden food bar, pack.png
| `lairner:df/glock` | G18 | own |  sounds.py           sound recipes (needs the source libraries, see below)
| `lairner:df/glock` | G18 | own |  render.py, preview.py  software previews
| `lairner:df/glock` | G18 | own |  pngio.py            PNG read/write (stdlib)
| `lairner:df/glock` | G18 | own |```
| `lairner:df/glock` | G18 | own |
| `lairner:df/glock` | G18 | own |## Rebuild
| `lairner:df/glock` | G18 | own |
| `lairner:df/glock` | G18 | own |Python 3 (stdlib only) and ffmpeg with libvorbis.
| `lairner:df/glock` | G18 | own |
| `lairner:df/glock` | G18 | own |```
| `lairner:df/glock` | G18 | own |python3 tools/build.py          # models + textures + checks + dist zip
| `lairner:df/glock` | G18 | own |python3 tools/preview.py        # previews/*.png
| `lairner:df/glock` | G18 | own |```
| `lairner:df/glock` | G18 | own |
| `lairner:df/glock` | G18 | own |Sounds are committed as OGG. To rebuild them, download The Free Firearm
| `lairner:df/glock` | G18 | own |Sound Library ("Prepared SFX Library.7z") and the four Kenney audio packs
| `lairner:df/glock` | G18 | own |(RPG Audio, Impact Sounds, Interface Sounds, Sci-fi Sounds), extract each
| `lairner:df/glock` | G18 | own |Kenney pack into `<dir>/<rpg-audio|impact-sounds|interface-sounds|sci-fi-sounds>/`,
| `lairner:df/glock` | G18 | own |then:
| `lairner:df/glock` | G18 | own |
| `lairner:df/glock` | G18 | own |```
| `lairner:df/glock` | G18 | own |python3 tools/sounds.py --ffsl "<path>/Prepared SFX Library" --kenney <dir>
| `lairner:df/glock` | G18 | own |python3 tools/build.py
| `lairner:df/glock` | G18 | own |```
| `lairner:df/glock` | G18 | own |
| `lairner:df/glock` | G18 | own |The zip is reproducible (sorted entries, fixed timestamps): the same
| `lairner:df/glock` | G18 | own |inputs give the same SHA-1. After a change, commit `dist/` too; the server
| `lairner:df/glock` | G18 | own |config needs the new SHA-1.
| `lairner:df/glock` | G18 | own |
| `lairner:df/glock` | G18 | own |Credits and licenses: [LICENSE.md](LICENSE.md).
