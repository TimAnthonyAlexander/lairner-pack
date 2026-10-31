"""Build the df sounds (mono OGG) and assets/lairner/sounds.json.

Sources are not in the repo (too big). Download them and pass the folders:

  The Free Firearm Sound Library (CC0)
    https://opengameart.org/content/the-free-firearm-sound-library
    -> "Prepared SFX Library.7z", extract; pass the "Prepared SFX Library" folder
  Kenney audio packs (CC0): rpg-audio, impact-sounds, interface-sounds,
    sci-fi-sounds from https://kenney.nl/assets ; extract each zip into
    <kenney>/<pack-name>/ (so <kenney>/rpg-audio/Audio/metalLatch.ogg exists)

Usage: python3 tools/sounds.py --ffsl "<Prepared SFX Library>" --kenney <dir>

Everything else (beeps, ring, hiss) is synthesized here with ffmpeg.
Each recipe states the source file and start time (onsets were found by
an envelope scan of the library recordings).
"""
import argparse
import json
import os
import re
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LA = os.path.join(ROOT, 'pack', 'assets', 'lairner')
OUT = os.path.join(LA, 'sounds', 'df')
RATE = 44100
QUALITY = '3'

# note: ffmpeg's sine source has amplitude 1/8 (-18 dB); synth gains account for that
SILENCED = 'highpass=f=220,lowpass=f=2300,equalizer=f=900:t=q:w=1:g=4'


def ff(args):
    subprocess.run(['ffmpeg', '-v', 'error', '-y'] + args, check=True)


def peak_db(path):
    r = subprocess.run(['ffmpeg', '-v', 'info', '-i', path, '-af', 'volumedetect', '-f', 'null', '-'],
                       capture_output=True, text=True, check=True)
    m = re.search(r'max_volume: (-?[\d.]+) dB', r.stderr)
    return float(m.group(1))


class Builder:
    def __init__(self, ffsl, kenney):
        self.ffsl = ffsl
        self.kenney = kenney
        self.tmp = tempfile.mkdtemp(prefix='lairner-snd-', dir=os.environ.get('TMPDIR'))

    def src(self, ref):
        lib, rel = ref.split(':', 1)
        if lib == 'ffsl':
            return os.path.join(self.ffsl, rel)
        return os.path.join(self.kenney, lib, 'Audio', rel)

    def render(self, name, parts, length, peak=-1.0, post=''):
        """parts: [(ref | 'lavfi:<graph>', start, dur, delay, filters, gain_db)]"""
        args = []
        chains = []
        for i, (ref, start, dur, delay, filt, gain) in enumerate(parts):
            if ref.startswith('lavfi:'):
                args += ['-f', 'lavfi', '-i', ref[6:]]
                pre = ''
            else:
                args += ['-i', self.src(ref)]
                pre = 'atrim=start=%s:duration=%s,asetpts=PTS-STARTPTS,' % (start, dur)
            f = pre + 'aformat=sample_fmts=fltp:sample_rates=%d:channel_layouts=mono' % RATE
            if filt:
                f += ',' + filt
            f += ',volume=%sdB' % gain
            if delay:
                f += ',adelay=%d' % int(delay * 1000)
            chains.append('[%d:a]%s[p%d]' % (i, f, i))
        mix = ''.join('[p%d]' % i for i in range(len(parts)))
        graph = ';'.join(chains) + ';%samix=inputs=%d:normalize=0:duration=longest,atrim=duration=%s' % (
            mix, len(parts), length)
        graph += ',afade=t=in:d=0.003,afade=t=out:st=%s:d=%s' % (max(0, length - min(0.25, length * 0.3)),
                                                                    min(0.25, length * 0.3))
        if post:
            graph += ',' + post
        graph += '[out]'
        wav = os.path.join(self.tmp, name.replace('/', '_') + '.wav')
        ff(args + ['-filter_complex', graph, '-map', '[out]', '-ac', '1', '-ar', str(RATE), wav])
        gain = peak - peak_db(wav)
        dst = os.path.join(OUT, name + '.ogg')
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        ff(['-i', wav, '-af', 'volume=%.2fdB' % gain, '-ac', '1', '-c:a', 'libvorbis', '-q:a', QUALITY,
            '-map_metadata', '-1', dst])
        return 'lairner:df/' + name


def clip(ref, start, dur, filt='', gain=0, delay=0):
    return (ref, start, dur, delay, filt, gain)


def synth(graph, delay=0, filt='', gain=0):
    return ('lavfi:' + graph, 0, 0, delay, filt, gain)


# event -> (sounds, attenuation_distance, subtitle)
def recipes(b):
    ev = {}
    lead = 0.012

    def shots(name, ref, onsets, dur, filt='', peak=-1.0):
        return [b.render('%s_%d' % (name, i + 1), [clip(ref, t - lead, dur, filt)], dur, peak)
                for i, t in enumerate(onsets)]

    ev['df.glock.shot'] = (shots('glock/shot', 'ffsl:Walther PPQ/X_39P.wav', [1.40, 6.44, 10.66], 0.55), 56)
    ev['df.usp.shot'] = (shots('usp/shot', 'ffsl:Ruger Mark III/R_30P.wav', [0.45, 3.87], 0.32,
                               SILENCED, peak=-7.0), 22)
    ev['df.deagle.shot'] = (shots('deagle/shot', 'ffsl:1911/A_42P.wav', [0.94, 5.00], 0.8,
                                  'asetrate=%d,aresample=%d' % (RATE * 0.88, RATE)), 72)
    ev['df.mac10.shot'] = (shots('mac10/shot', 'ffsl:Carl Gustav M45/G_31P.wav', [0.31, 3.50, 6.72], 0.45), 56)
    ev['df.mp9.shot'] = (shots('mp9/shot', 'ffsl:PPSh/P_30P.wav', [0.96, 4.38, 8.24], 0.45,
                               'asetrate=%d,aresample=%d' % (RATE * 1.06, RATE)), 56)
    ev['df.ak.shot'] = (shots('ak/shot', 'ffsl:AK-47/C_28P.wav', [0.61, 3.25, 6.02], 0.7), 72)
    ev['df.m4s.shot'] = (shots('m4s/shot', 'ffsl:AR-15/D_32P.wav', [0.70, 5.64], 0.34,
                               SILENCED, peak=-6.0), 24)

    rpg, imp, ui, sci = 'rpg-audio:', 'impact-sounds:', 'interface-sounds:', 'sci-fi-sounds:'
    ev['df.reload.pistol'] = ([b.render('reload/pistol', [
        clip(rpg + 'metalLatch.ogg', 0, 0.3, delay=0.15),
        clip(imp + 'impactMetal_light_001.ogg', 0, 0.3, 'highpass=f=400', -6, delay=1.15),
        clip(rpg + 'metalClick.ogg', 0, 0.45, delay=1.75)], 2.2, -4.0)], 12)
    ev['df.reload.smg'] = ([b.render('reload/smg', [
        clip(rpg + 'metalLatch.ogg', 0, 0.3, delay=0.2),
        clip(rpg + 'beltHandle1.ogg', 0, 0.3, gain=-4, delay=0.7),
        clip(imp + 'impactMetal_light_002.ogg', 0, 0.3, 'highpass=f=400', -6, delay=1.6),
        clip(rpg + 'metalClick.ogg', 0, 0.45, delay=2.25)], 2.7, -4.0)], 12)
    ev['df.reload.rifle'] = ([b.render('reload/rifle', [
        clip(rpg + 'metalLatch.ogg', 0, 0.3, delay=0.25),
        clip(rpg + 'beltHandle2.ogg', 0, 0.45, gain=-4, delay=0.8),
        clip(imp + 'impactMetal_light_003.ogg', 0, 0.3, 'highpass=f=300', -4, delay=1.45),
        clip(rpg + 'metalClick.ogg', 0, 0.45, delay=2.0)], 2.5, -4.0)], 12)
    ev['df.dryfire'] = ([b.render('dryfire', [clip(rpg + 'metalClick.ogg', 0, 0.2, 'highpass=f=800')], 0.2, -6.0)], 10)

    ev['df.hit'] = ([b.render('hit', [
        clip(ui + 'tick_002.ogg', 0, 0.05),
        synth('sine=frequency=2400:duration=0.04', filt='afade=t=out:d=0.04', gain=4)], 0.08, -4.0)], 8)
    ev['df.headshot'] = ([b.render('headshot', [
        clip(imp + 'impactMetal_light_000.ogg', 0, 0.35, 'highpass=f=1200'),
        synth('sine=frequency=3200:duration=0.25', filt='afade=t=out:d=0.25', gain=4)], 0.35, -2.0)], 8)

    ev['df.headshot.kill'] = ([tim_headshot_kill()], 80)
    ev['df.headshot.hit'] = ([tim_headshot_hit()], 80)

    ev['df.knife.swing'] = ([b.render('knife/swing_%d' % (i + 1), [clip(rpg + f, 0, 0.45)], 0.45, -5.0)
                             for i, f in enumerate(('knifeSlice.ogg', 'knifeSlice2.ogg'))], 12)
    ev['df.knife.hit'] = ([b.render('knife/hit', [
        clip(imp + 'impactPunch_medium_000.ogg', 0, 0.4),
        clip(rpg + 'knifeSlice2.ogg', 0, 0.3, 'highpass=f=1500', -8)], 0.4, -2.0)], 16)

    beep = 'sine=frequency=%d:duration=%s'
    ev['df.bomb.beep'] = ([b.render('bomb/beep', [synth(beep % (2100, 0.11), filt='afade=t=out:st=0.08:d=0.03')],
                                    0.12, -3.0)], 24)
    ev['df.bomb.key'] = ([b.render('bomb/key', [synth(beep % (1350, 0.06), filt='afade=t=out:st=0.04:d=0.02', gain=12),
                                                clip(ui + 'click_002.ogg', 0, 0.06, gain=-6)], 0.07, -6.0)], 12)
    ev['df.bomb.plant'] = ([b.render('bomb/plant', [
        clip(rpg + 'metalLatch.ogg', 0, 0.3),
        synth(beep % (1600, 0.1), delay=0.3, filt='afade=t=out:st=0.07:d=0.03', gain=12),
        synth(beep % (2100, 0.16), delay=0.45, filt='afade=t=out:st=0.1:d=0.06', gain=12)], 0.7, -3.0)], 32)
    ev['df.bomb.defuse'] = ([b.render('bomb/defuse', [
        clip(rpg + 'metalLatch.ogg', 0, 0.3),
        clip(rpg + 'metalClick.ogg', 0, 0.3, gain=-3, delay=0.35),
        clip(rpg + 'beltHandle1.ogg', 0, 0.3, gain=-6, delay=0.7)], 1.1, -4.0)], 16)
    ev['df.bomb.defused'] = ([b.render('bomb/defused', [
        synth(beep % (2100, 0.1), filt='afade=t=out:st=0.07:d=0.03'),
        synth(beep % (1600, 0.1), delay=0.13, filt='afade=t=out:st=0.07:d=0.03'),
        synth(beep % (1100, 0.25), delay=0.26, filt='afade=t=out:st=0.1:d=0.15')], 0.6, -3.0)], 32)
    ev['df.bomb.explode'] = ([b.render('bomb/explode', [
        clip(sci + 'lowFrequency_explosion_000.ogg', 0, 2.0),
        clip(sci + 'explosionCrunch_000.ogg', 0, 0.8, gain=-2),
        synth('anoisesrc=color=brown:duration=3.2:amplitude=0.6', filt='lowpass=f=500,afade=t=out:st=0.2:d=3.0',
              gain=-6)], 3.2, -0.5)], 160)

    ev['df.flash.ring'] = ([b.render('flash/ring', [
        synth('sine=frequency=3900:duration=4', filt='afade=t=out:st=0.3:d=3.7:curve=exp', gain=12),
        synth('sine=frequency=4150:duration=4', filt='afade=t=out:st=0.3:d=3.7:curve=exp', gain=9),
        synth('anoisesrc=color=pink:duration=1.2:amplitude=0.3', filt='highpass=f=2000,afade=t=out:d=1.2',
              gain=-14)], 4.0, -8.0)], 8)
    ev['df.flash.explode'] = ([b.render('flash/explode', [
        clip(sci + 'explosionCrunch_002.ogg', 0, 0.8, 'highpass=f=500'),
        clip(imp + 'impactGlass_light_000.ogg', 0, 0.3, gain=-8)], 0.8, -1.0)], 64)
    ev['df.grenade.bounce'] = ([b.render('grenade/bounce_%d' % (i + 1), [
        clip(imp + 'impactTin_medium_00%d.ogg' % i, 0, 0.16)], 0.16, -4.0) for i in range(3)], 20)
    ev['df.he.explode'] = ([b.render('he/explode', [
        clip(sci + 'explosionCrunch_000.ogg', 0, 0.8),
        clip(sci + 'lowFrequency_explosion_001.ogg', 0, 1.0, gain=-1),
        synth('anoisesrc=color=brown:duration=1.8:amplitude=0.5', filt='lowpass=f=700,afade=t=out:st=0.1:d=1.7',
              gain=-8)], 1.8, -0.5)], 96)
    ev['df.smoke.pop'] = ([b.render('smoke/pop', [
        clip(imp + 'impactSoft_heavy_000.ogg', 0, 0.4),
        synth('anoisesrc=color=pink:duration=3.5:amplitude=0.5',
              filt='highpass=f=900,lowpass=f=5000,afade=t=in:d=0.15,afade=t=out:st=0.8:d=2.7', gain=-6)],
        3.5, -3.0)], 32)
    return ev


def tim_headshot_kill():
    """df.headshot.kill: Tim's own sound (source/tim/headshot.m4a, provided by Tim, 2.55 s stereo AAC).
    The sound runs 0.45-1.59 s; trimmed to 0.43-1.62 s, mono (a stereo file would play non-positional at full
    volume for everyone), 5 ms fades against clicks, Ogg Vorbis."""
    dst = os.path.join(OUT, 'headshot_kill.ogg')
    ff(['-i', os.path.join(ROOT, 'source', 'tim', 'headshot.m4a'),
        '-af', 'atrim=start=0.43:end=1.62,asetpts=PTS-STARTPTS,afade=t=in:d=0.005,afade=t=out:st=1.184:d=0.005',
        '-ac', '1', '-ar', str(RATE), '-c:a', 'libvorbis', '-q:a', QUALITY, dst])
    return 'lairner:df/headshot_kill'


def tim_headshot_hit():
    """df.headshot.hit: Tim's own sound (source/tim/headshot_dmg.m4a, provided by Tim, 1.07 s stereo AAC),
    a headshot that doesn't kill. The sound runs 0.058-0.435 s (silencedetect -45 dB); trimmed to 0.05-0.45 s,
    mono, 5 ms fades, Ogg Vorbis."""
    dst = os.path.join(OUT, 'headshot_hit.ogg')
    ff(['-i', os.path.join(ROOT, 'source', 'tim', 'headshot_dmg.m4a'),
        '-af', 'atrim=start=0.05:end=0.45,asetpts=PTS-STARTPTS,afade=t=in:d=0.005,afade=t=out:st=0.395:d=0.005',
        '-ac', '1', '-ar', str(RATE), '-c:a', 'libvorbis', '-q:a', QUALITY, dst])
    return 'lairner:df/headshot_hit'


SUBTITLES = {
    'df.glock.shot': 'Gunshot', 'df.usp.shot': 'Silenced shot', 'df.deagle.shot': 'Gunshot',
    'df.mac10.shot': 'Gunshot', 'df.mp9.shot': 'Gunshot', 'df.ak.shot': 'Gunshot', 'df.m4s.shot': 'Silenced shot',
    'df.reload.pistol': 'Reloading', 'df.reload.smg': 'Reloading', 'df.reload.rifle': 'Reloading',
    'df.knife.swing': 'Knife swings', 'df.knife.hit': 'Knife hits', 'df.bomb.beep': 'Bomb beeps',
    'df.bomb.plant': 'Bomb planted', 'df.bomb.defuse': 'Defusing', 'df.bomb.defused': 'Bomb defused',
    'df.bomb.explode': 'Bomb explodes', 'df.flash.explode': 'Flashbang pops', 'df.grenade.bounce': 'Grenade bounces',
    'df.he.explode': 'Grenade explodes', 'df.smoke.pop': 'Smoke hisses', 'df.headshot.kill': 'Headshot kill',
    'df.headshot.hit': 'Headshot',
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ffsl', required=True)
    ap.add_argument('--kenney', required=True)
    a = ap.parse_args()
    b = Builder(a.ffsl, a.kenney)
    events = recipes(b)
    out = {}
    for name in sorted(events):
        files, att = events[name]
        entry = {'sounds': [{'name': f, 'attenuation_distance': att} for f in files]}
        if name in SUBTITLES:
            entry['subtitle'] = SUBTITLES[name]
        out[name] = entry
    with open(os.path.join(LA, 'sounds.json'), 'w') as f:
        json.dump(out, f, indent=2)
        f.write('\n')
    total = sum(os.path.getsize(os.path.join(dp, fn)) for dp, _, fns in os.walk(OUT) for fn in fns)
    print('%d events, %d files, %.0f KB' % (len(out), sum(len(v[0]) for v in events.values()), total / 1024))


if __name__ == '__main__':
    main()
