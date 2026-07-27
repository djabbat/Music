#!/usr/bin/env python3
"""
THEMATIC MATRIX — Mozart-style systematic theme development.
6 themes × 6 transformations = 36 cells.
Each cell can be combined with others following the matrix.
"""
import mido as md, os, random
from ze_music import *

# ═══════════════════════════════════════════
# THE THEMATIC MATRIX (like Mozart's patterns)
# ═══════════════════════════════════════════
# 6 themes from Gurian folk songs
# 6 transformations: Original, Inversion, Retrograde, Augmentation, Diminution, Ornamented
# Matrix cell [theme][transform] = new theme variant

GURIAN = [0,2,3,6,7,8,10]

melodies_raw = {}
for fn in ['Chakrulo','Gandagana','Khasanbegura','Guruli_Naduri','gurian','Guruli_Khasanbegura']:
    n = load_midi(f'data/midi/georgian/{fn}.mid')
    top = sorted([x for x in n if x.pitch >= 65], key=lambda x: x.start)
    if top: melodies_raw[fn] = top

THEMES = {
    'Gilgamesh': melodies_raw['Chakrulo'],
    'Enkidu':    melodies_raw['Gandagana'],
    'Ishtar':    melodies_raw['Khasanbegura'],
    'Humbaba':   melodies_raw['Guruli_Khasanbegura'],
    'Shamhat':   melodies_raw['Guruli_Naduri'],
    'Utnapishtim': melodies_raw['gurian'],
}

def clv(v): return max(1, min(127, int(v)))
def chrd(deg, tonic, scale):
    s=scale;idx=(deg-1)%len(s)
    r=(tonic//12)*12+s[idx]
    while r<tonic-12:r+=12
    t=(r//12)*12+s[(idx+2)%len(s)]
    if t<r:t+=12
    f=(r//12)*12+s[(idx+4)%len(s)]
    if f<t:f+=12
    return r,t,f

# ═══════════════════════════════════════════
# THEMATIC MATRIX TRANSFORMATIONS
# ═══════════════════════════════════════════
def transform(notes, variant, tonic_ref=62):
    """Apply one of 6 transformations to a theme."""
    if not notes: return notes
    
    if variant == 'O':  # Original
        return [(n.pitch, n.duration, n.velocity) for n in notes]
    
    elif variant == 'I':  # Inversion around tonic
        result = []
        for n in notes:
            inv = tonic_ref - (n.pitch - tonic_ref)
            result.append((max(36, min(108, inv)), n.duration, n.velocity))
        return result
    
    elif variant == 'R':  # Retrograde
        rev = list(reversed(notes))
        return [(n.pitch, n.duration, n.velocity) for n in rev]
    
    elif variant == 'A':  # Augmentation (×2 slower)
        return [(n.pitch, n.duration*2, n.velocity-5) for n in notes]
    
    elif variant == 'D':  # Diminution (×2 faster)
        return [(n.pitch, n.duration//2, n.velocity+5) for n in notes]
    
    elif variant == 'Orn':  # Ornamented
        result = []
        for i, n in enumerate(notes):
            result.append((n.pitch, n.duration, n.velocity))
            if i % 2 == 0:
                grace = n.pitch + random.choice([1,2,-1,-2])
                result.append((max(36, min(108, grace)), n.duration//4, n.velocity-10))
        return result
    
    return [(n.pitch, n.duration, n.velocity) for n in notes]

# ═══════════════════════════════════════════
# MOZART MATRIX — composition plan
# ═══════════════════════════════════════════
# Each row = one variation pass through the matrix
# Format: (theme_name, transform, section_name, dynamic, progression)

MATRIX = [
    # EXPOSITION — state each theme
    ("Gilgamesh",   "O",   "Exposition: Gilgamesh",        "mf", [1,4,5,1]),
    ("Enkidu",      "O",   "Exposition: Enkidu",           "mp", [6,4,5,1]),
    ("Ishtar",      "O",   "Exposition: Ishtar",           "f",  [1,5,6,4]),
    
    # DEVELOPMENT 1 — invert themes
    ("Gilgamesh",   "I",   "Development: Gilgamesh inv.",  "mf", [1,5,6,4]),
    ("Enkidu",      "R",   "Development: Enkidu retro.",   "mp", [6,4,5,1]),
    ("Ishtar",      "Orn", "Development: Ishtar orn.",     "f",  [1,5,6,4]),
    ("Humbaba",     "O",   "Development: Humbaba enters",  "ff", [6,4,5,1]),
    
    # DEVELOPMENT 2 — combine themes
    ("Gilgamesh",   "A",   "Dev2: Gilgamesh augmented",    "f",  [1,4,5,1]),
    ("Enkidu",      "D",   "Dev2: Enkidu diminished",      "p",  [6,4,5,1]),
    ("Shamhat",     "O",   "Dev2: Shamhat appears",        "mp", [1,5,6,4]),
    ("Gilgamesh",   "Orn", "Dev2: Gilgamesh ornamented",   "mf", [1,4,5,1]),
    
    # CLIMAX — all themes together
    ("Ishtar",      "A",   "Climax: Ishtar augmented",     "ff", [1,4,5,1]),
    ("Gilgamesh",   "D",   "Climax: Gilgamesh fast",       "ff", [1,5,6,4]),
    ("Humbaba",     "I",   "Climax: Humbaba inverted",     "ff", [6,4,5,1]),
    ("Utnapishtim", "O",   "Climax: Utnapishtim speaks",   "f",  [1,4,1,5]),
    
    # RESOLUTION — themes return transformed
    ("Gilgamesh",   "O",   "Resolution: Gilgamesh returns", "mf", [1,4,5,1]),
    ("Enkidu",      "I",   "Resolution: Enkidu in heaven",  "p",  [1,4,1,5]),
    ("Ishtar",      "R",   "Resolution: Ishtar recedes",    "mp", [1,5,6,4]),
    
    # CODA
    ("Gilgamesh",   "A",   "Coda: The King at the Walls",   "pp", [1,4,5,1]),
]

print("╔══════════════════════════════════════════════╗")
print("║  MOZART MATRIX — Thematic Development       ║")
print("║  6 themes × 6 transforms = 36 cells         ║")
print("╚══════════════════════════════════════════════╝\n")

# Build the matrix as a table
print("      ", end="")
for t in ['O','I','R','A','D','Orn']:
    print(f"  {t:>6}", end="")
print("\n      " + "─"*42)
for theme_name in ['Gilgamesh','Enkidu','Ishtar','Humbaba','Shamhat','Utnapishtim']:
    print(f"  {theme_name:<12}", end="")
    for variant in ['O','I','R','A','D','Orn']:
        # Check if this cell is used in the matrix
        used = any(row[0]==theme_name and row[1]==variant for row in MATRIX)
        print(f"  {'✓' if used else '·':>6}", end="")
    print()

print(f"\nCells used: {len(MATRIX)} / 36\n")

# ═══════════════════════════════════════════
# COMPOSE FROM MATRIX
# ═══════════════════════════════════════════
mid_out = md.MidiFile(ticks_per_beat=480)
out_data = {ch: [] for ch in range(14)}
last_v = {'bass':36,'cello':48,'viola':55,'vln2':60,'flute':72}

global_tick = 0

for theme_name, variant, section_name, dyn, prog in MATRIX:
    theme_notes = THEMES[theme_name]
    transformed = transform(theme_notes, variant)
    
    DYN_MAP = {'pp':0.4,'p':0.55,'mp':0.7,'mf':0.85,'f':1.0,'ff':1.15}
    dm = DYN_MAP[dyn]
    
    print(f"  {section_name:<45} [{theme_name}:{variant}] {dyn}")
    
    for i, (pitch, dur, vel) in enumerate(transformed):
        dur_ticks = max(60, int(dur * 200))  # ~200 ticks per beat
        tick = global_tick
        global_tick += dur_ticks
        
        deg = prog[i % len(prog)]
        r, t3, f5 = chrd(deg, 62, GURIAN)
        bv = clv(vel * dm)
        
        # Voice leading
        for target, key, ch, vel_mod, dur_mod in [
            (max(28,r-24), 'bass', 4, -20, 2),
            (max(36,r-12), 'cello', 3, -15, 1),
            (t3, 'viola', 2, -10, 1),
            (f5, 'vln2', 1, -5, 1),
        ]:
            step = 1 if target > last_v[key] else -1
            last_v[key] += step * min(abs(target - last_v[key]), 3)
            if abs(last_v[key] - target) <= 3: last_v[key] = target
            out_data[ch].append((tick, 'on', last_v[key], clv(bv+vel_mod)))
            out_data[ch].append((tick+dur_ticks*dur_mod, 'off', last_v[key], 0))
        
        # Melody
        out_data[0].append((tick, 'on', pitch, clv(bv+8)))
        out_data[0].append((tick+dur_ticks, 'off', pitch, 0))
        
        # Flute
        fl = pitch + 12
        if fl <= 108:
            step = 1 if fl > last_v['flute'] else -1
            last_v['flute'] += step * min(abs(fl - last_v['flute']), 4)
            if abs(last_v['flute'] - fl) <= 4: last_v['flute'] = fl
            out_data[5].append((tick, 'on', last_v['flute'], clv(bv-5)))
            out_data[5].append((tick+dur_ticks, 'off', last_v['flute'], 0))
        
        # Oboe suspensions
        if i % 4 == 3 and i > 0:
            _,pt,_ = chrd(prog[(i-1)%len(prog)], 62, GURIAN)
            out_data[6].append((tick, 'on', pt, clv(bv-12)))
            out_data[6].append((tick+dur_ticks//2, 'off', pt, 0))
        
        # Horns
        if i % 8 == 0:
            out_data[7].append((tick, 'on', max(36,r-5), clv(bv-15)))
            out_data[7].append((tick+dur_ticks*8, 'off', max(36,r-5), 0))
        
        # Timpani
        if i % 4 == 0:
            out_data[8].append((tick, 'on', 38, clv(bv+10)))
            out_data[8].append((tick+dur_ticks//4, 'off', 38, 0))
        
        # Harp
        if i % 8 == 0:
            for j, cn in enumerate([r+12, f5, t3, r]):
                if cn <= 108:
                    out_data[9].append((tick+j*80, 'on', cn, clv(bv-25)))
                    out_data[9].append((tick+j*80+dur_ticks//3, 'off', cn, 0))
        
        # Trumpets on climax
        if dyn == 'ff' and i % 8 == 0:
            out_data[13].append((tick, 'on', r, clv(bv+15)))
            out_data[13].append((tick+dur_ticks//2, 'off', r, 0))
        
        # Krimanchuli
        if random.random() < 0.3:
            kp = pitch + 12
            if kp <= 108:
                out_data[10].append((tick, 'on', kp, clv(bv+8)))
                out_data[10].append((tick+dur_ticks, 'off', kp, 0))

# Write MIDI
NAMES = ["Strings","Violins II","Violas","Celli","Basses","Flute","Oboe","Horns","Timpani","Harp","Krimanchuli","Celesta","Counterpoint","Trumpets"]
PROGS = [48,40,41,42,43,73,68,60,47,46,69,8,40,61]

for ch in range(14):
    data = out_data[ch]
    if not data: continue
    data.sort(key=lambda x: (x[0], 0 if x[1]=='off' else 1))
    tk = md.MidiTrack(); mid_out.tracks.append(tk)
    tk.append(md.MetaMessage('track_name', name=NAMES[ch]))
    tk.append(md.Message('program_change', program=PROGS[ch], channel=ch, time=0))
    lt = 0
    for tick, typ, note, vel in data:
        d = max(0, tick - lt); lt = tick
        if typ == 'on':
            tk.append(md.Message('note_on', note=note, velocity=vel, time=d, channel=ch))
        else:
            tk.append(md.Message('note_off', note=note, velocity=0, time=d, channel=ch))

out = 'Samnu_Azuzi/midi/Samnu_Azuzi_Matrix.mid'
mid_out.save(out)
secs = global_tick / 480 * 60 / 72
print(f"\n{'═'*60}")
print(f"  MATRIX COMPLETE")
print(f"  {len(MATRIX)} variations × 6 themes")
print(f"  Duration: {int(secs//60)}:{int(secs%60):02d}")
print(f"  {out}")
print(f"{'═'*60}")

wav = out.replace('.mid', '.wav')
print("Rendering...")
os.system(f'timidity -c /tmp/timidity.cfg "{out}" -Ow -o "{wav}" -s 44100 -A120 2>/dev/null')
sz = os.path.getsize(wav)//1048576 if os.path.exists(wav) else 0
print(f"WAV: {sz} MB ✓")
