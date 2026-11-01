"""Spawn music and the silenced biome music (2026-11-01).

  python3 tools/music.py [path/to/music.json]      (default /opt/minecraft/config/defusal/music.json)

1. assets/lairner/sounds.json: one event per map and side, lairner:df.music.<map>_<t|ct>, which plays one of
   the client's own music discs (minecraft:records/<name>, not shipped in this pack: every client has them).
   Discs, not music/game: the discs are mono, so the client attenuates them with distance (attenuation_distance
   20 blocks, linear, fades to silence at 20); the stereo music/game tracks have no distance falloff in
   Minecraft. The game plays them in the 'records' category (Jukebox/Note Blocks slider) at a low volume.
2. assets/minecraft/sounds.json: the biome background music events of 26.3 replaced by nothing, so the client's
   own random game music never plays over the spawn music (the pack is only active on the defusal server).
   The list is every music event named by a worldgen biome or dimension type of the 26.3 client jar.

Both are rewritten from scratch each time (other events of lairner sounds.json stay).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LA = os.path.join(ROOT, 'pack', 'assets', 'lairner', 'sounds.json')
MC = os.path.join(ROOT, 'pack', 'assets', 'minecraft', 'sounds.json')
ATTENUATION = 20

SILENCED = [
    'music.creative', 'music.game', 'music.under_water',
    'music.nether.basalt_deltas', 'music.nether.crimson_forest', 'music.nether.nether_wastes',
    'music.nether.soul_sand_valley', 'music.nether.warped_forest',
    'music.overworld.badlands', 'music.overworld.bamboo_jungle', 'music.overworld.cherry_grove',
    'music.overworld.deep_dark', 'music.overworld.desert', 'music.overworld.dripstone_caves',
    'music.overworld.flower_forest', 'music.overworld.forest', 'music.overworld.frozen_peaks',
    'music.overworld.grove', 'music.overworld.jagged_peaks', 'music.overworld.jungle',
    'music.overworld.lush_caves', 'music.overworld.meadow', 'music.overworld.old_growth_taiga',
    'music.overworld.snowy_slopes', 'music.overworld.sparse_jungle', 'music.overworld.stony_peaks',
    'music.overworld.sulfur_caves', 'music.overworld.swamp',
]


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else '/opt/minecraft/config/defusal/music.json'
    maps = json.load(open(src))['maps']
    ev = json.load(open(LA))
    for k in [k for k in ev if k.startswith('df.music.')]:
        del ev[k]
    for m in sorted(maps):
        for side in ('T', 'CT'):
            ev['df.music.%s_%s' % (m, side.lower())] = {
                'sounds': [{'name': 'minecraft:records/%s' % maps[m][side], 'stream': True,
                            'attenuation_distance': ATTENUATION}]}
    with open(LA, 'w') as f:
        json.dump(dict(sorted(ev.items())), f, indent=2)
        f.write('\n')
    os.makedirs(os.path.dirname(MC), exist_ok=True)
    with open(MC, 'w') as f:
        json.dump({e: {'replace': True, 'sounds': []} for e in SILENCED}, f, indent=2)
        f.write('\n')
    print('%d music events, %d silenced vanilla music events' % (2 * len(maps), len(SILENCED)))


if __name__ == '__main__':
    main()
