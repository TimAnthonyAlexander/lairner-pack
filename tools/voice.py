"""Build the df voice lines into pack/assets/lairner/sounds/df/voice/ and their sounds.json entries.

Two voices (Tim, 2026-11-01):
- the announcer (bomb planted/defused, round winners): old-school robotic TTS, deep, low quality. eSpeak NG
  (GPL-3.0) through the `espeakng_loader` wheel (bundles libespeak-ng; nothing installed system-wide), pitched
  low, then lo-fi: 11 kHz, telephone band (150-3200 Hz), a light bit crush.
- everything the players say (grenade callouts, round start lines): ElevenLabs Eleven v3 (model `eleven_v3`,
  Creator plan: commercial use allowed), voices per side: CT British (SAS lines) and American, T accented
  (Russian, Balkan, Greek) and Australian (the "Bloody Darryl" lines). The API output is cached in
  source/eleven/<hash>.mp3 (the hash of model, voice, text and settings), so a rebuild costs no characters.

Usage:
  python3 -m venv /tmp/v && /tmp/v/bin/pip install espeakng_loader
  /tmp/v/bin/python tools/voice.py --eleven-key <file with the API key>
All files are mono OGG, silence trimmed, peak -1 dB.
"""
import argparse
import ctypes
import hashlib
import json
import os
import subprocess
import tempfile
import urllib.error
import urllib.request
import wave

import espeakng_loader as el

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LA = os.path.join(ROOT, 'pack', 'assets', 'lairner')
OUT = os.path.join(LA, 'sounds', 'df', 'voice')
CACHE = os.path.join(ROOT, 'source', 'eleven')

# eSpeak announcer: (voice, words per minute, pitch 0-99, pitch range 0-99)
ANNOUNCER = ('en-us+m3', 135, 12, 12)
LOFI = ('aresample=11025,highpass=f=150,lowpass=f=3200,'
        'acrusher=level_in=1:level_out=1:bits=9:mode=log:aa=1:mix=0.35,aresample=44100')

MODEL = 'eleven_v3'
V = {  # ElevenLabs voices (premade and library voices of the account)
    'george': 'JBFqnCBsd6RMkjVDRZzb',    # British, warm
    'daniel': 'onwK4e9ZLuTAKqWW03F9',    # British, steady
    'graham': '0UADyUjkZk8ADanJ1yEw',    # British, calm
    'adam': 'pNInz6obpgDQGcFmaJgB',      # American, dominant
    'harry': 'SOYHLrjzK2X1ezoPC6cr',     # American, fierce
    'brian': 'nPczCjzI2devNBz1zQrb',     # American, deep
    'connery': 'e6gztcS9NPqChYKvXN6c',   # American, serious
    'callum': 'N2lVS1w4EtoT3dr4eOWO',    # American, husky
    'maxim': 'IGRoDkfYV2Frq7Ly0PRu',     # Russian-accented English
    'roman': 'v0eRobr4pSbFT9FKocdw',     # Russian
    'slobodan': 'adxhr4Ei7ASJ3Cz7fxwX',  # Balkan
    'atlas': 'ejJ1ETWS2ohLMMeCu1H3',     # Greek
    'charlie': 'IKne3meq5aSn9XLyUdCD',   # Australian
    'liam': 'TX3LPaxmHKxFdv7VOQHJ',      # American, energetic
    'chris': 'iP95p4xoKVk53GoZ742B',     # American, down-to-earth
}
# 2026-11-01 (Tim: "a Slavic man in monotone or a polite Englishman instead of American war phrases with
# exclamation"): American soldiers shouting; British only for the SAS lines, Australian for the "bloody" ones
CT_VOICES = ['adam', 'connery', 'brian', 'chris', 'harry']
T_VOICES = ['harry', 'callum', 'liam', 'chris', 'adam']
STABILITY = 0.0   # Eleven v3 "Creative": the most expressive
# delivery tags, cycled per line (callouts always shout)
GO_TAGS = ['[shouting]', '[excited] [shouting]', '[aggressive] [shouting]', '[battle cry]', '[pumped up] [shouting]']

# grenade callouts: the thrower's side picks the set (df.voice.<kind>_<side>), the client one of the lines
CALLOUTS = {
    'he': ['Fire in the hole!', 'Grenade out!', 'Frag out!', 'Nade out!', 'H.E. going in!', 'Throwing a grenade!'],
    'flash': ['Flashbang out!', 'Flash out!', 'Flashing!', 'Flash going in!', 'Throwing a flash!',
              'Flashbang, look away!'],
    'smoke': ['Smoke out!', 'Throwing smoke!', 'Smoke going in!', "Smoke's out!", 'Smoking!', 'Smoke, smoke!'],
}

# round start lines per side (the CS2 agents' round start lines and the classics), (text, voice or None = next
# of the side's voices); one event each (df.voice.goct<n>, df.voice.got<n>), Skript picks one per side
GO_CT = [
    ('Bingo, bango, bongo; bish, bash, bosh.', 'george'), ("Let's make this right as rain.", 'daniel'),
    ('Are we rushing in? Or are we going sneaky-beaky like?', 'graham'),
    ("Remove any doubts in your head. It's us, or them.", 'george'),
    ('Remember! This is bandit country. Shoot everything that moves.', 'daniel'),
    ("Remember! This isn't the killing house anymore! This is real life.", 'graham'),
    ("There's no stopping us!", None), ("Let's get our heads in the game!", None),
    ("Be careful, let's all make it home tonight.", None), ("Come on, let's get this started.", None),
    ('Does anyone have a plan?', None), ('Valor and discipline, mon ami.', None),
    ('Fortune favors the bored.', None), ('Justice comes for them.', None),
    ('Today is not the day we die.', None), ('After we win, drinks are on me.', None),
    ("Let's make this quick.", None), ("Let's do this by the book, people.", None),
    ("These guys don't have a chance in hell.", None), ("Let's get in there, and get out.", None),
    ('Alright, keep it together, we got this.', None),
    ('If we keep this up, we could make it back in time for waffles.', None),
    ('Anyone else here for the pickle party?', None), ("Let's wrap it up.", None),
    ("This is it, let's go!", None), ('Buckle up, bad guys!', None),
    ('Just another day in the office for us!', None),
    ('Go, go, go!', None), ('Lock and load!', None), ('Move out!', None), ("Let's move out!", None),
    ('Stick together, team.', None),
]
GO_T = [
    ('This is where we get our revenge.', None), ('You will cry like babies before you die.', None),
    ('We will dance on your graves!', None), ('You are stupid to think you can win.', None),
    ('This is our land.', None), ('Fear us.', None), ('Move it!', None),
    ('Move, my brothers!', None), ('Let us be safe, and swift.', None),
    ('We will make them regret this day.', None), ("Let's go, my friends.", None),
    ('We will make them cry.', None), ('We will drive them from our lands.', None),
    ("Let's get this party started.", None), ('Good day to die, people.', None),
    ("Let's go!", None), ("Let's get in and out.", None),
    ("Look, it's simple. All we gotta do is go in there, plant the bomb, get the cash, and get out. "
     "Not so bloody hard, is it?", 'charlie'),
    ('Okay, here we bloody go!', 'charlie'), ("Let's send 'em to the sick bay, shall we?", 'charlie'),
    ('Have a go, you mongrel dogs!', 'charlie'), ("Okay, I'm feeling a bit good about this one.", 'charlie'),
    ("Who's ready to start trying?", None), ("Let's go ruin someone's day.", None),
    ("We do the winning, they do the dying.", None), ('We kneel for no one!', None),
    ('Let us send them home!', None), ('We will take everything from them.', None),
    ('They want a body count. So be it.', None),
    ('Go, go, go!', None), ('Lock and load!', None), ('Move out!', None),
]

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


def espeak(text, voice, wav_path):
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


def eleven(text, voice, key, stability):
    """The line as MP3 from the cache or the API (Eleven v3)."""
    body = {'text': text, 'model_id': MODEL, 'voice_settings': {'stability': stability}}
    h = hashlib.sha1(json.dumps([voice, body], sort_keys=True).encode()).hexdigest()[:16]
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, h + '.mp3')
    if not os.path.exists(path):
        req = urllib.request.Request(
            'https://api.elevenlabs.io/v1/text-to-speech/%s?output_format=mp3_44100_128' % V[voice],
            data=json.dumps(body).encode(), headers={'xi-api-key': key, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
        except urllib.error.HTTPError as e:
            raise SystemExit('ElevenLabs %d for %s (%s): %s' % (e.code, voice, text, e.read().decode()[:300]))
        with open(path, 'wb') as f:
            f.write(data)
        print('  generated %s (%s): %s' % (h, voice, text))
    return path


def ff(args):
    subprocess.run(['ffmpeg', '-v', 'error', '-y'] + args, check=True)


def peak_db(path):
    r = subprocess.run(['ffmpeg', '-v', 'info', '-i', path, '-af', 'volumedetect', '-f', 'null', '-'],
                       capture_output=True, text=True, check=True)
    for line in r.stderr.splitlines():
        if 'max_volume:' in line:
            return float(line.split('max_volume:')[1].split('dB')[0])
    return 0.0


TRIM = ('silenceremove=start_periods=1:start_threshold=-50dB,areverse,'
        'silenceremove=start_periods=1:start_threshold=-50dB,areverse,')


def finish(src, dst, chain):
    with tempfile.TemporaryDirectory() as td:
        lo = os.path.join(td, 'lo.wav')
        ff(['-i', src, '-af', TRIM + chain, '-ac', '1', '-ar', '44100', lo])
        gain = -1.0 - peak_db(lo)
        ff(['-i', lo, '-af', 'volume=%.2fdB' % gain, '-ac', '1', '-c:a', 'libvorbis', '-q:a', '4', dst])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--eleven-key', required=True, help='file with the ElevenLabs API key')
    a = ap.parse_args()
    key = open(a.eleven_key).read().strip()
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        os.remove(os.path.join(OUT, f))
    path = os.path.join(LA, 'sounds.json')
    with open(path) as f:
        data = json.load(f)
    for k in [k for k in data if k.startswith('df.voice.')]:
        del data[k]

    def entry(ev, names, att, sub):
        data[ev] = {'sounds': [{'name': 'lairner:df/voice/' + n, 'attenuation_distance': att} for n in names],
                    'subtitle': sub}

    # the announcer
    for ev, line in (('planted', 'The bomb has been planted.'), ('defused', 'The bomb has been defused.'),
                     ('ctwin', 'Counter-Terrorists win.'), ('twin', 'Terrorists win.')):
        with tempfile.TemporaryDirectory() as td:
            raw = os.path.join(td, 'raw.wav')
            espeak(line, ANNOUNCER, raw)
            finish(raw, os.path.join(OUT, ev + '.ogg'), LOFI)
        entry('df.voice.' + ev, [ev], 16, line.rstrip('.'))

    # callouts per grenade and side: shouted
    for kind, lines in CALLOUTS.items():
        for side, voices in (('ct', CT_VOICES), ('t', T_VOICES)):
            names = []
            for i, line in enumerate(lines):
                mp3 = eleven('[shouting] ' + line, voices[i % len(voices)], key, STABILITY)
                n = '%s_%s_%d' % (kind, side, i + 1)
                finish(mp3, os.path.join(OUT, n + '.ogg'), 'highpass=f=70')
                names.append(n)
            entry('df.voice.%s_%s' % (kind, side), names, 28, lines[0].rstrip('!'))

    # round start lines
    counts = {}
    for side, lines, voices in (('ct', GO_CT, CT_VOICES), ('t', GO_T, T_VOICES)):
        nxt = 0
        for i, (line, voice) in enumerate(lines):
            if voice is None:
                voice = voices[nxt % len(voices)]
                nxt += 1
            # war phrases end with an exclamation mark, not a full stop (questions stay questions)
            said = line[:-1] + '!' if line.endswith('.') else line
            mp3 = eleven(GO_TAGS[i % len(GO_TAGS)] + ' ' + said, voice, key, STABILITY)
            n = 'go%s%d' % (side, i + 1)
            finish(mp3, os.path.join(OUT, n + '.ogg'), 'highpass=f=70')
            entry('df.voice.' + n, [n], 16, line.rstrip('!.'))
        counts[side] = len(lines)

    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
        f.write('\n')
    print('voice events: %d; round start lines: CT %d, T %d (Skript dfGoLive must match)' % (
        len([k for k in data if k.startswith('df.voice.')]), counts['ct'], counts['t']))


if __name__ == '__main__':
    main()
