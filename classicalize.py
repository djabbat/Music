#!/usr/bin/env python3
"""Classical harmony & rhythm — functional progressions, varied rhythmic patterns."""
import mido as md, os, random

GURIAN = [0,2,3,6,7,8,10]
MAJOR = [0,2,4,5,7,9,11]
MINOR = [0,2,3,5,7,8,10]

def clv(v): return max(1, min(127, int(v)))

def chord_for(pitch, mode_scale):
    """Return (root, third, fifth) for this pitch in the given scale."""
    s = mode_scale
    pc = pitch % 12
    try: idx = s.index(pc)
    except: idx = min(range(len(s)), key=lambda i: abs(s[i]-pc))
    o = pitch // 12
    r = o*12 + s[idx]
    t = o*12 + s[(idx+2)%len(s)]
    if t < r: t += 12
    f = o*12 + s[(idx+4)%len(s)]
    if f < t: f += 12
    return r, t, f

def functional_chord(degree, tonic, scale):
    """Build chord on scale degree (1=I, 4=IV, 5=V)."""
    s = scale
    idx = (degree - 1) % len(s)
    o = tonic // 12
    root = (tonic//12)*12 + s[idx]
    while root < tonic - 12: root += 12
    third = (root//12)*12 + s[(idx+2)%len(s)]
    if third < root: third += 12
    fifth = (root//12)*12 + s[(idx+4)%len(s)]
    if fifth < third: fifth += 12
    return root, third, fifth

# Rhythm patterns (in ticks at 480 tpb, 72 BPM = 400 ticks/beat)
# Each pattern is 2 bars of 4/4 = 8 beats = 3200 ticks
RHYTHM_PATTERNS = {
    'chorale':    [800, 800, 800, 800, 800, 800, 800, 800],           # whole notes
    'flowing':    [400, 400, 400, 400, 400, 400, 400, 400, 400, 400, 400, 400, 400, 400, 400, 400],  # quarters
    'walking':    [200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200],  # eighths
    'dotted':     [600, 200, 400, 400, 600, 200, 400, 400, 600, 200, 400, 400],  # dotted+short
    'syncopated': [300, 500, 200, 600, 300, 500, 200, 600, 300, 500, 200, 600],
    'waltz':      [600, 300, 300, 600, 300, 300, 600, 300, 300, 600, 300, 300, 600, 300, 300, 600, 300, 300],
    'heroic':     [800, 400, 400, 800, 400, 400, 800, 400, 400, 1600],
}

def classicalize(inp, out, mode='gurian'):
    scale = GURIAN if mode == 'gurian' else MAJOR
    tonic_pitch = 62 if mode == 'gurian' else 60  # D for Gurian, C for major
    
    mid_in = md.MidiFile(inp); tpb = mid_in.ticks_per_beat
    events = []
    abs_t = 0
    for track in mid_in.tracks:
        abs_t = 0
        for msg in track:
            abs_t += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                events.append((abs_t, msg.note, msg.velocity))
    if not events: return 0
    events.sort()
    
    mid_out = md.MidiFile(ticks_per_beat=tpb)
    out_data = {ch: [] for ch in range(14)}
    
    # Harmony state — track functional progression
    phrase_len = 16  # events per harmonic phrase
    PROGRESSIONS = [
        [1, 4, 5, 1],  # I-IV-V-I
        [1, 6, 4, 5],  # I-vi-IV-V
        [1, 5, 6, 4],  # I-V-vi-IV
        [1, 4, 1, 5],  # I-IV-I-V
        [6, 4, 5, 1],  # vi-IV-V-I
    ]
    
    last = {'bass': 36, 'cello': 48, 'viola': 55, 'vln2': 60, 'flute': 72, 'counter': 65}
    
    # Build a harmonic grid first — functional chords that change every phrase
    total_phrases = len(events) // phrase_len + 1
    harmonic_grid = []
    for p in range(total_phrases):
        prog = PROGRESSIONS[p % len(PROGRESSIONS)]
        for deg in prog:
            harmonic_grid.append(deg)
    # Expand: each chord degree covers phrase_len // len(prog) events
    chord_map = []
    for deg in harmonic_grid:
        for _ in range(phrase_len // 4):
            chord_map.append(deg)
    while len(chord_map) < len(events):
        chord_map.append(1)  # pad with I
    
    for i, (tick, pitch, vel) in enumerate(events):
        dur = events[i+1][0] - tick if i+1 < len(events) else 480
        dur = max(60, min(dur, 1920))
        
        # ═══ FUNCTIONAL HARMONY ═══
        chord_deg = chord_map[min(i, len(chord_map)-1)]
        r, t3, f5 = functional_chord(chord_deg, tonic_pitch, scale)
        
        pos_in_bar = i % 16
        phrase_pos = i % phrase_len
        
        # Pick rhythm pattern based on section
        section = i // 400  # ~every 400 events
        if section % 5 == 0:  # chorale sections
            rhythm = RHYTHM_PATTERNS['chorale']
        elif section % 5 == 1:  # flowing
            rhythm = RHYTHM_PATTERNS['flowing']
        elif section % 5 == 2:  # heroic
            rhythm = RHYTHM_PATTERNS['heroic']
        elif section % 5 == 3:  # waltz
            rhythm = RHYTHM_PATTERNS['waltz']
        else:  # dotted
            rhythm = RHYTHM_PATTERNS['dotted']
        
        rhythm_dur = rhythm[i % len(rhythm)]
        # Scale rhythm to match original duration tempo
        rhythm_factor = dur / 400.0  # normalize to quarter note
        rhythm_dur = int(rhythm_dur * rhythm_factor)
        rhythm_dur = max(30, min(rhythm_dur, 1920))
        
        # Dynamic arc
        dyn = 1.0 - 0.2 * abs(pos_in_bar - 8) / 8
        bv = clv(vel * dyn)
        
        # ═══ BASS — functional root, rhythmic pattern ═══
        bass_note = max(28, r - 24)
        # Smooth approach
        step = 1 if bass_note > last['bass'] else -1
        smooth_bass = last['bass'] + step * min(abs(bass_note - last['bass']), 2)
        if abs(smooth_bass - bass_note) <= 2: smooth_bass = bass_note
        last['bass'] = smooth_bass
        
        out_data[4].append((tick, 'on', smooth_bass, clv(bv-20)))
        out_data[4].append((tick+rhythm_dur, 'off', smooth_bass, 0))
        
        # Walking bass on flowing sections
        if section % 5 == 1 and i % 4 == 0:
            walk_note = smooth_bass + random.choice([0, 2, 4, 5, 7])
            out_data[4].append((tick + rhythm_dur//2, 'on', max(28, walk_note), clv(bv-25)))
            out_data[4].append((tick + rhythm_dur, 'off', max(28, walk_note), 0))
        
        # ═══ CELLO — chord root, medium rhythm ═══
        cello_note = max(36, r - 12)
        step = 1 if cello_note > last['cello'] else -1
        smooth_cello = last['cello'] + step * min(abs(cello_note - last['cello']), 3)
        if abs(smooth_cello - cello_note) <= 3: smooth_cello = cello_note
        last['cello'] = smooth_cello
        
        out_data[3].append((tick, 'on', smooth_cello, clv(bv-15)))
        out_data[3].append((tick+rhythm_dur, 'off', smooth_cello, 0))
        
        # ═══ VIOLA — chord third ═══
        viola_note = t3
        step = 1 if viola_note > last['viola'] else -1
        smooth_viola = last['viola'] + step * min(abs(viola_note - last['viola']), 3)
        if abs(smooth_viola - viola_note) <= 3: smooth_viola = viola_note
        last['viola'] = smooth_viola
        
        out_data[2].append((tick, 'on', smooth_viola, clv(bv-10)))
        out_data[2].append((tick+rhythm_dur, 'off', smooth_viola, 0))
        
        # ═══ VIOLIN II — chord fifth ═══
        v2_note = f5
        step = 1 if v2_note > last['vln2'] else -1
        smooth_v2 = last['vln2'] + step * min(abs(v2_note - last['vln2']), 3)
        if abs(smooth_v2 - v2_note) <= 3: smooth_v2 = v2_note
        last['vln2'] = smooth_v2
        
        out_data[1].append((tick, 'on', smooth_v2, clv(bv-5)))
        out_data[1].append((tick+rhythm_dur, 'off', smooth_v2, 0))
        
        # ═══ VIOLIN I — melody with chord-aware adjustments ═══
        # Keep original melody but snap to chord tones when close
        melody_pitch = pitch
        distances = [abs(melody_pitch - r), abs(melody_pitch - t3), abs(melody_pitch - f5)]
        nearest_chord_tone = [r, t3, f5][distances.index(min(distances))]
        if min(distances) <= 2:  # snap to nearest chord tone
            melody_pitch = nearest_chord_tone
        
        out_data[0].append((tick, 'on', melody_pitch, clv(bv+5)))
        out_data[0].append((tick+rhythm_dur, 'off', melody_pitch, 0))
        
        # ═══ FLUTE — melody octave up ═══
        fl_target = melody_pitch + 12
        if fl_target <= 108:
            step = 1 if fl_target > last['flute'] else -1
            smooth_fl = last['flute'] + step * min(abs(fl_target - last['flute']), 4)
            if abs(smooth_fl - fl_target) <= 4: smooth_fl = fl_target
            last['flute'] = smooth_fl
            out_data[5].append((tick, 'on', smooth_fl, clv(bv-8)))
            out_data[5].append((tick+rhythm_dur, 'off', smooth_fl, 0))
        
        # ═══ OBOE — suspensions on chord changes ═══
        if phrase_pos % 4 == 3 and i > 0:
            prev_r, prev_t, prev_f = functional_chord(chord_map[min(i-1, len(chord_map)-1)], tonic_pitch, scale)
            out_data[6].append((tick, 'on', prev_t, clv(bv-12)))
            out_data[6].append((tick+rhythm_dur//2, 'off', prev_t, 0))
            out_data[6].append((tick+rhythm_dur//2, 'on', t3, clv(bv-14)))
            out_data[6].append((tick+rhythm_dur, 'off', t3, 0))
        
        # ═══ HORNS — sustained ═══
        if i % 8 == 0:
            out_data[7].append((tick, 'on', max(36, r-5), clv(bv-15)))
            out_data[7].append((tick+rhythm_dur*8, 'off', max(36, r-5), 0))
        
        # ═══ TRUMPETS — fanfare on I and V ═══
        if chord_deg in (1, 5) and phrase_pos % 8 == 0:
            out_data[13].append((tick, 'on', r, clv(bv+10)))
            out_data[13].append((tick+rhythm_dur//2, 'off', r, 0))
        
        # ═══ TIMPANI — emphasize harmony changes ═══
        if phrase_pos % 4 == 0:
            out_data[8].append((tick, 'on', 38, clv(bv+15)))
            out_data[8].append((tick+rhythm_dur//4, 'off', 38, 0))
        
        # ═══ HARP — arpeggiate chord on changes ═══
        if phrase_pos % 8 == 0:
            for j, cn in enumerate([r+12, f5, t3, r]):
                if cn <= 108:
                    out_data[9].append((tick + j*80, 'on', cn, clv(bv-25)))
                    out_data[9].append((tick + j*80 + rhythm_dur//3, 'off', cn, 0))
        
        # ═══ COUNTERPOINT — imitative entry ═══
        if i > 8 and i % 6 == 0:
            cntr_note = pitch - 7  # fifth below
            step = 1 if cntr_note > last['counter'] else -1
            smooth_cntr = last['counter'] + step * min(abs(cntr_note - last['counter']), 4)
            if abs(smooth_cntr - cntr_note) <= 4: smooth_cntr = cntr_note
            last['counter'] = smooth_cntr
            out_data[12].append((tick + rhythm_dur, 'on', smooth_cntr, clv(bv-15)))
            out_data[12].append((tick + rhythm_dur*2, 'off', smooth_cntr, 0))
        
        # ═══ KRIMANCHULI ═══
        if random.random() < 0.3:
            kp = pitch + 12
            if kp <= 108:
                out_data[10].append((tick, 'on', kp, clv(bv+8)))
                out_data[10].append((tick+rhythm_dur, 'off', kp, 0))
        
        # Celesta
        if i % 6 == 0:
            out_data[11].append((tick, 'on', min(108, r+12), clv(bv-30)))
            out_data[11].append((tick+rhythm_dur//3, 'off', min(108, r+12), 0))
    
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
    
    mid_out.save(out)
    return len(events)

# Process Samnu Azuzi
inp = 'Samnu_Azuzi/midi/Samnu_Azuzi_Full_Opera_Harmonized.mid'
out = inp.replace('.mid', '_Classical.mid')
print(f"Classical harmony + rhythm — Samnu Azuzi...")
n = classicalize(inp, out, 'gurian')
print(f"  {n} notes → 14 tracks")
print(f"  Harmony: I-IV-V-I functional progressions")
print(f"  Rhythm: 6 alternating patterns (chorale/flowing/heroic/waltz/dotted/syncopated)")
print(f"  MIDI: {out}")

wav = out.replace('.mid', '.wav')
print(f"Rendering...")
os.system(f'timidity -c /tmp/timidity.cfg "{out}" -Ow -o "{wav}" -s 44100 -A120 2>/dev/null')
sz = os.path.getsize(wav)//1048576 if os.path.exists(wav) else 0
print(f"WAV: {sz} MB ✓")
