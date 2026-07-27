#!/usr/bin/env python3
"""
ZE-MIM DEFINITIVE — непрерывные, протяжные, разнообразные мелодии.
Грузинский бас-бурдон. Смены ладов. Динамические волны. Золотое сечение.
"""
import mido as md, os, random, math, sys
from ze_music import *

# ═══════════════════════════════════
# CONFIG
# ═══════════════════════════════════
SCALES = {
    'gurian': [0,2,3,6,7,8,10], 'svan': [0,2,4,7,9],
    'major': [0,2,4,5,7,9,11], 'minor': [0,2,3,5,7,8,10],
    'dorian': [0,2,3,5,7,9,10], 'lydian': [0,2,4,6,7,9,11],
}

# Load themes
melodies = {}
for fn in ['Chakrulo','Gandagana','Khasanbegura','Guruli_Naduri','gurian','Guruli_Khasanbegura']:
    n = load_midi(f'data/midi/georgian/{fn}.mid')
    top = sorted([x for x in n if x.pitch >= 65], key=lambda x: x.start)
    if top: melodies[fn] = [(x.pitch, x.duration*0.5, x.velocity) for x in top]

THEMES = {
    'Gilgamesh': melodies['Chakrulo'], 'Enkidu': melodies['Gandagana'],
    'Ishtar': melodies['Khasanbegura'], 'Humbaba': melodies['Guruli_Khasanbegura'],
    'Shamhat': melodies['Guruli_Naduri'], 'Utnapishtim': melodies['gurian'],
}

def clv(v): return max(1, min(127, int(v)))

# ═══════════════════════════════════
# DEFINITIVE COMPOSER
# ═══════════════════════════════════
class DefinitiveComposer:
    def __init__(self, tempo=55):
        self.tempo = tempo; self.tpb = 480; self.tick = 0
        self.out = {ch: [] for ch in range(5)}
        self.last = {}
    
    def scale_note(self, pitch, scale):
        pc = pitch % 12
        if pc in scale: return pitch
        near = min(scale, key=lambda s: abs(s - pc))
        return (pitch // 12) * 12 + near
    
    def vl(self, target, key, step=2):
        if key not in self.last: self.last[key] = target; return target
        lv = self.last[key]; d = target - lv
        s = 1 if d > 0 else -1
        r = lv + s * min(abs(d), step)
        if abs(r - target) <= step: r = target
        self.last[key] = max(24, min(108, r))
        return self.last[key]
    
    def note(self, ch, pitch, vel, tick, dur):
        pitch = max(24, min(108, pitch))
        self.out[ch].append((tick, 'on', pitch, clv(vel)))
        self.out[ch].append((tick + dur, 'off', pitch, 0))
    
    def section(self, theme, scale_name, dyn_arc, reps=6, stretch=5):
        """Compose one continuous section with stretched notes."""
        scale = SCALES[scale_name]
        
        # Parse dynamic arc
        stages = dyn_arc.split('→')
        DM = {'pp': 0.2, 'p': 0.4, 'mp': 0.55, 'mf': 0.7, 'f': 0.85, 'ff': 1.0}
        
        melody = list(theme)
        total_notes = len(melody) * reps
        
        for rep in range(reps):
            for i, (pitch, dur_beats, vel) in enumerate(melody[:64]):
                global_i = rep * 64 + i
                frac = global_i / max(1, total_notes - 1)
                
                # Dynamic interpolation
                sf = frac * (len(stages) - 1)
                lo, hi = int(sf), min(int(sf) + 1, len(stages) - 1)
                tp = sf - lo
                dm = DM[stages[lo]] + tp * (DM[stages[hi]] - DM[stages[lo]])
                
                # Micro-breathing (phrase = 128 notes)
                pos = global_i % 128
                micro = 1.0 - 0.04 * abs(pos - 64) / 64
                
                # Scale adaptation
                p = self.scale_note(pitch, scale)
                
                # STRETCH — 4-7x longer notes
                stretch_factor = stretch + 2 * (1.0 - abs(frac - 0.5) * 2)
                dur_ticks = max(240, int(dur_beats * self.tpb * stretch_factor))
                dur_ticks = min(dur_ticks, 9600)
                
                v = clv(vel * dm * micro)
                tick = self.tick
                
                # === MELODY (continuous, unbroken) ===
                self.note(0, p, v + 5, tick, dur_ticks)
                
                # === BASS DRONE (Georgian bani) ===
                bass_root = 38 if (global_i // 64) % 2 == 0 else 43
                bass = self.vl(bass_root, 'bass')
                if global_i % 4 == 0:
                    self.note(2, bass, clv(v * 0.35), tick, dur_ticks * 3)
                
                # === HARMONY (soft, sustained) ===
                harm_p = p - random.choice([3, 4, 5])
                harm = self.vl(harm_p, 'harm', 3)
                if global_i % 2 == 0:
                    self.note(1, harm, clv(v * 0.45), tick, dur_ticks * 2)
                
                # === KRIMANCHULI (floating above) ===
                if dm > 0.55 and global_i % 8 == 4:
                    kp = p + 12
                    if kp <= 108:
                        self.note(3, kp, clv(v * 0.7), tick, dur_ticks)
                
                # === CELESTA/HARP accent ===
                if global_i % 12 == 0:
                    self.note(4, min(108, p + 12), clv(v * 0.3), tick, dur_ticks // 2)
                
                self.tick += dur_ticks
            
            # Vary melody on repeat
            if reps > 1:
                melody = [(p + random.choice([0, 0, 0, 1, -1]), d, v) for p, d, v in melody[:56]]
    
    def compose_opera(self, movements):
        """Compose full opera from movement definitions."""
        for name, theme_name, scale_name, dyn_arc, reps, stretch in movements:
            t0 = self.tick
            theme = THEMES[theme_name]
            self.section(theme, scale_name, dyn_arc, reps, stretch)
            secs = (self.tick - t0) / self.tpb * 60 / self.tempo
            print(f"  {name:<30} [{scale_name:<8}] {dyn_arc:<15} {int(secs//60)}:{int(secs%60):02d}")
    
    def save(self, fp):
        mo = md.MidiFile(ticks_per_beat=self.tpb)
        N = ["Melody", "Harmony", "Bass-Bani", "Krimanchuli", "Celesta"]
        P = [48, 41, 43, 69, 8]
        
        for ch in range(5):
            data = self.out[ch]
            if not data: continue
            data.sort(key=lambda x: (x[0], 0 if x[1] == 'off' else 1))
            tk = md.MidiTrack(); mo.tracks.append(tk)
            tk.append(md.MetaMessage('set_tempo', tempo=int(60000000 / self.tempo), time=0))
            tk.append(md.MetaMessage('track_name', name=N[ch]))
            tk.append(md.Message('program_change', program=P[ch], channel=ch, time=0))
            lt = 0
            for tick, typ, note, vel in data:
                d = max(0, tick - lt); lt = tick
                if typ == 'on':
                    tk.append(md.Message('note_on', note=note, velocity=vel, time=d, channel=ch))
                else:
                    tk.append(md.Message('note_off', note=note, velocity=0, time=d, channel=ch))
        mo.save(fp)
        return self.tick / self.tpb * 60 / self.tempo

# ═══════════════════════════════════════
# COMPOSE
# ═══════════════════════════════════════
print("╔══════════════════════════════════════╗")
print("║  DEFINITIVE — непрерывные мелодии   ║")
print("╚══════════════════════════════════════╝\n")

C = DefinitiveComposer(tempo=55)

MOVEMENTS = [
    ("Overture-Dawn",        "Utnapishtim", "gurian", "pp→p→mp", 8, 5),
    ("Gilgamesh-King",       "Gilgamesh",   "gurian", "mp→mf→f", 10, 5),
    ("Enkidu-Wild",          "Enkidu",      "svan",   "p→mp→mf", 8, 6),
    ("Shamhat-Water",        "Shamhat",     "major",  "mp→mf", 7, 5),
    ("Gilgamesh-Campaign",   "Gilgamesh",   "major",  "mf→f→ff", 10, 5),
    ("Humbaba-Guardian",     "Humbaba",     "minor",  "f→ff", 8, 6),
    ("Battle-Cedar",         "Gilgamesh",   "dorian", "ff→f", 10, 4),
    ("Ishtar-Descends",      "Ishtar",      "minor",  "f→ff", 9, 5),
    ("Ishtar-Fury",          "Ishtar",      "dorian", "ff", 8, 4),
    ("Enkidu-Illness",       "Enkidu",      "svan",   "f→mf→mp", 7, 7),
    ("Enkidu-Farewell",      "Enkidu",      "minor",  "mp→p→pp", 8, 8),
    ("Gilgamesh-Lament",     "Gilgamesh",   "gurian", "p→pp", 9, 7),
    ("Wilderness",           "Gilgamesh",   "lydian", "pp→p→mp", 8, 6),
    ("Utnapishtim-Wisdom",   "Utnapishtim", "gurian", "mp", 8, 8),
    ("Return-Uruk",          "Gilgamesh",   "major",  "mp→mf→f", 10, 5),
    ("Walls-Peace",          "Gilgamesh",   "gurian", "f→mf→p→pp", 9, 7),
]

C.compose_opera(MOVEMENTS)

fp = 'Samnu_Azuzi/midi/Samnu_Azuzi_Definitive.mid'
dur = C.save(fp)
mi, si = int(dur // 60), int(dur % 60)
print(f"\n  TOTAL: {mi}:{si:02d}")
print(f"  MIDI: {fp}")

# Render
wav = fp.replace('.mid', '.wav')
print("  Rendering...")
ret = os.system(f'timidity -c /tmp/timidity.cfg "{fp}" -Ow -o "{wav}" -s 44100 -A200 2>/dev/null')
sz = os.path.getsize(wav) // 1048576 if os.path.exists(wav) else 0
if sz > 0:
    os.system(f'cp "{wav}" ~/Desktop/Samnu_Azuzi_Definitive.wav')
    with open(wav, 'rb') as f:
        f.seek(40); ds = int.from_bytes(f.read(4), 'little')
        f.seek(24); sr = int.from_bytes(f.read(4), 'little')
        f.seek(22); ch = int.from_bytes(f.read(2), 'little')
        secs = ds / (ch * 2 * sr)
    print(f"  WAV: {sz} MB  {int(secs//60)}:{int(secs%60):02d} → Desktop")
else:
    print(f"  Use DAW to render: {fp}")
