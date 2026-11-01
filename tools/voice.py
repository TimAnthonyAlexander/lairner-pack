"""Build the df voice lines (old-school robotic TTS) into pack/assets/lairner/sounds/df/voice/ and their
sounds.json entries.

Engine: eSpeak NG (GPL-3.0) through the `espeakng_loader` wheel (bundles libespeak-ng and its data; nothing
installed system-wide):  python3 -m venv /tmp/v && /tmp/v/bin/pip install espeakng_loader
Usage: /tmp/v/bin/python tools/voice.py

Style (Tim, 2026-11-01): old-school, low quality, deep male voice, not modern TTS. eSpeak's formant voice,
pitched low, then made lo-fi: 11 kHz, telephone band (150-3200 Hz), a light bit crush, peak -1 dB, mono OGG.
"""
import ctypes
import json
import os
import subprocess
import tempfile
import wave

import espeakng_loader as el

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LA = os.path.join(ROOT, 'pack', 'assets', 'lairner')
OUT = os.path.join(LA, 'sounds', 'df', 'voice')

# voice settings: (espeak voice, words per minute, pitch 0-99, pitch range 0-99)
ANNOUNCER = ('en-us+m3', 135, 12, 12)
CALLERS = [('en-us+m1', 175, 22, 40), ('en-us+m3', 170, 16, 35), ('en-us+m7', 180, 26, 45)]

# event -> (lines, who speaks, attenuation distance, subtitle)
EVENTS = {
    'df.voice.planted': (['The bomb has been planted.'], 'announcer', 16, 'The bomb has been planted'),
    'df.voice.defused': (['The bomb has been defused.'], 'announcer', 16, 'The bomb has been defused'),
    'df.voice.ctwin': (['Counter-Terrorists win.'], 'announcer', 16, 'Counter-Terrorists win'),
    'df.voice.twin': (['Terrorists win.'], 'announcer', 16, 'Terrorists win'),
    'df.voice.he': (['Fire in the hole!', 'Grenade out!', 'Frag out!', 'H E going in!'], 'caller', 28, 'Fire in the hole!'),
    'df.voice.flash': (['Flashbang out!', 'Flash out!', 'Flashing!', 'Flash going in!'], 'caller', 28, 'Flashbang out!'),
    'df.voice.smoke': (['Smoke out!', 'Throwing smoke!', 'Smoke going in!', "Smoke's out!"], 'caller', 28, 'Smoke out!'),
}

LOFI = ('aresample=11025,highpass=f=150,lowpass=f=3200,'
        'acrusher=level_in=1:level_out=1:bits=9:mode=log:aa=1:mix=0.35,aresample=44100')

_lib = None
_rate = 22050
_samples = []


def _init():
    global _lib, _rate, _cb
    if _lib:
        return
    _lib = ctypes.CDLL(el.get_library_path())
    _rate = _lib.espeak_Initialize(2, 0, el.get_data_path().encode(), 0)   # AUDIO_OUTPUT_SYNCHRONOUS
    cbtype = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(ctypes.c_short), ctypes.c_int, ctypes.c_void_p)

    def cb(wav, n, events):
        if wav and n > 0:
            _samples.append(ctypes.string_at(wav, n * 2))
        return 0
    _cb = cbtype(cb)
    _lib.espeak_SetSynthCallback(_cb)


def speak(text, voice, wav_path):
    _init()
    name, rate, pitch, prange = voice
    _samples.clear()
    _lib.espeak_SetVoiceByName(name.encode())
    _lib.espeak_SetParameter(1, rate, 0)
    _lib.espeak_SetParameter(3, pitch, 0)
    _lib.espeak_SetParameter(4, prange, 0)
    t = text.encode()
    _lib.espeak_Synth(t, len(t) + 1, 0, 0, 0, 0x01, None, None)
    _lib.espeak_Synchronize()
    with wave.open(wav_path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(_rate)
        w.writeframes(b''.join(_samples))


def ff(args):
    subprocess.run(['ffmpeg', '-v', 'error', '-y'] + args, check=True)


def peak_db(path):
    r = subprocess.run(['ffmpeg', '-v', 'info', '-i', path, '-af', 'volumedetect', '-f', 'null', '-'],
                       capture_output=True, text=True, check=True)
    for line in r.stderr.splitlines():
        if 'max_volume:' in line:
            return float(line.split('max_volume:')[1].split('dB')[0])
    return 0.0


def main():
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        os.remove(os.path.join(OUT, f))
    path = os.path.join(LA, 'sounds.json')
    with open(path) as f:
        data = json.load(f)
    for ev, (lines, who, att, sub) in EVENTS.items():
        names = []
        for i, line in enumerate(lines):
            voice = ANNOUNCER if who == 'announcer' else CALLERS[i % len(CALLERS)]
            base = ev[len('df.voice.'):] + ('_%d' % (i + 1) if len(lines) > 1 else '')
            dst = os.path.join(OUT, base + '.ogg')
            with tempfile.TemporaryDirectory() as td:
                raw, lo = os.path.join(td, 'raw.wav'), os.path.join(td, 'lo.wav')
                speak(line, voice, raw)
                # trim the synthesizer's leading/trailing silence, then the lo-fi chain
                ff(['-i', raw, '-af', 'silenceremove=start_periods=1:start_threshold=-50dB,areverse,'
                    'silenceremove=start_periods=1:start_threshold=-50dB,areverse,' + LOFI, '-ac', '1', lo])
                gain = -1.0 - peak_db(lo)
                ff(['-i', lo, '-af', 'volume=%.2fdB' % gain, '-ac', '1', '-c:a', 'libvorbis', '-q:a', '3', dst])
            names.append('lairner:df/voice/' + base)
        data[ev] = {'sounds': [{'name': n, 'attenuation_distance': att} for n in names], 'subtitle': sub}
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
        f.write('\n')
    print('voice lines: ' + ', '.join('%s %d' % (e, len(v[0])) for e, v in EVENTS.items()))


if __name__ == '__main__':
    main()
