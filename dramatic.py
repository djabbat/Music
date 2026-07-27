#!/usr/bin/env python3
"""Melodic development + drama + engagement — theme transformation, climax, contrast."""
import mido as md, os, random

GURIAN = [0,2,3,6,7,8,10]
MAJOR = [0,2,4,5,7,9,11]

def clv(v): return max(1, min(127, int(v)))

def functional_chord(degree, tonic, scale):
    s = scale; idx = (degree-1)%len(s)
    root = (tonic//12)*12 + s[idx]
    while root < tonic-12: root += 12
    third = (root//12)*12 + s[(idx+2)%len(s)]
    if third < root: third += 12
    fifth = (root//12)*12 + s[(idx+4)%len(s)]
    if fifth < third: fifth += 12
    return root, third, fifth

# Melodic transformations
def transform_melody(notes, variant):
    """Apply classical melodic development technique."""
    result = []
    for i, n in enumerate(notes):
        if variant == 'original':
            result.append(n)
        elif variant == 'inversion':
            # Invert around tonic
            tonic = notes[0] if notes else 60
            inverted = tonic - (n - tonic)
            result.append(inverted)
        elif variant == 'retrograde':
            result = list(reversed(notes))
            break
        elif variant == 'augmentation':
            result.append(n * 2 if i % 2 == 0 else n)
        elif variant == 'diminution':
            result.append(n // 2 if i % 2 == 0 else n)
        elif variant == 'sequence_up':
            result.append(n + 2)  # step up
        elif variant == 'sequence_down':
            result.append(n - 2)
        elif variant == 'ornamented':
            # Add neighbor tones
            result.append(n)
            if i % 3 == 0:
                result.append(n + random.choice([1, 2, -1, -2]))
        elif variant == 'fragmented':
            if i < len(notes)//2:
                result.append(n)
        elif variant == 'climactic':
            # Higher, louder, slower
            result.append(n + 5)
    return result

def build_dramatic_events(base_events, scale, tonic):
    """Build a dramatic score from melody events with development, climax, contrast."""
    out_data = {ch: [] for ch in range(15)}
    
    PROGRESSIONS = [[1,4,5,1],[1,6,4,5],[1,5,6,4],[6,4,5,1],[1,4,1,5]]
    VARIANTS = ['original','sequence_up','inversion','ornamented','sequence_down',
                'climactic','fragmented','original','augmentation','retrograde']
    
    total = len(base_events)
    # Dramatic structure: exposition → development → climax → resolution
    sections = [
        ('exposition',   0.0,  0.25, 'pp',   'original',     [1,4,5,1]),
        ('transition',   0.25, 0.40, 'mp',   'sequence_up',  [1,5,6,4]),
        ('development',  0.40, 0.60, 'mf',   'inversion',    [6,4,5,1]),
        ('climax_build', 0.60, 0.75, 'f',    'ornamented',   [1,5,6,4]),
        ('climax',       0.75, 0.85, 'ff',   'climactic',    [1,4,5,1]),
        ('resolution',   0.85, 0.95, 'mf',   'original',     [1,4,1,5]),
        ('coda',         0.95, 1.0,  'pp',   'fragmented',   [1,4,5,1]),
    ]
    
    last = {'bass':36,'cello':48,'viola':55,'vln2':60,'flute':72,'counter':65}
    grand_pause_every = total // 8  # dramatic silences
    
    for i, (tick, pitch, vel) in enumerate(base_events):
        dur = base_events[i+1][0] - tick if i+1 < len(base_events) else 480
        dur = max(60, min(dur, 1920))
        
        # Find current section
        frac = i / total
        section = sections[0]
        for s in sections:
            if frac >= s[1] and frac < s[2]:
                section = s
                break
        
        s_name, s_start, s_end, s_dyn, s_variant, s_prog = section
        
        # Dynamic mapping
        DYN_MAP = {'pp': 0.4, 'p': 0.55, 'mp': 0.7, 'mf': 0.85, 'f': 1.0, 'ff': 1.15}
        dyn_mult = DYN_MAP[s_dyn]
        
        # Crescendo within climax build
        if s_name == 'climax_build':
            local_frac = (frac - s_start) / (s_end - s_start)
            dyn_mult = 0.7 + 0.45 * local_frac  # mp → ff
        
        # Grand pause — dramatic silence
        if i % grand_pause_every == grand_pause_every - 1 and s_name in ('climax_build', 'climax'):
            dur = dur * 3  # extended pause before hit
            dyn_mult = 1.3  # extra loud after pause
        
        # Functional chord
        deg = s_prog[i % len(s_prog)]
        r, t3, f5 = functional_chord(deg, tonic, scale)
        
        # Melodic development — transform pitch based on section variant
        if s_variant == 'inversion':
            pitch = tonic - (pitch - tonic)
        elif s_variant == 'sequence_up':
            pitch += 2
        elif s_variant == 'sequence_down':
            pitch -= 2
        elif s_variant == 'climactic':
            pitch += 5
        elif s_variant == 'ornamented' and i % 3 == 0:
            pitch += random.choice([1, 2, -1, -2])
        elif s_variant == 'augmentation' and i % 2 == 0:
            dur *= 2
        elif s_variant == 'fragmented' and i > 0:
            if i % 3 != 0: continue  # sparse
        
        pitch = max(36, min(108, pitch))
        bv = clv(vel * dyn_mult)
        
        # Rhythm per section
        if s_name in ('exposition', 'resolution'):
            rhythm_dur = dur
        elif s_name in ('transition', 'development'):
            rhythm_dur = dur // 2 if i % 2 == 0 else dur
        elif s_name == 'climax_build':
            rhythm_dur = dur // 2  # faster
        elif s_name == 'climax':
            rhythm_dur = dur * 2  # massive, slow
        else:
            rhythm_dur = dur // 4 if i % 4 == 0 else dur  # sparse coda
        
        rhythm_dur = max(30, min(rhythm_dur, 1920))
        
        # ═══ VOICES ═══
        # Bass — functional root, dramatic
        bass_note = max(28, r-24)
        step = 1 if bass_note > last['bass'] else -1
        last['bass'] += step * min(abs(bass_note - last['bass']), 2)
        if abs(last['bass'] - bass_note) <= 2: last['bass'] = bass_note
        
        out_data[4].append((tick, 'on', last['bass'], clv(bv-20)))
        out_data[4].append((tick+rhythm_dur*2, 'off', last['bass'], 0))
        
        # Cello
        cello = max(36, r-12)
        step = 1 if cello > last['cello'] else -1
        last['cello'] += step * min(abs(cello - last['cello']), 3)
        if abs(last['cello'] - cello) <= 3: last['cello'] = cello
        out_data[3].append((tick, 'on', last['cello'], clv(bv-15)))
        out_data[3].append((tick+rhythm_dur, 'off', last['cello'], 0))
        
        # Viola
        step = 1 if t3 > last['viola'] else -1
        last['viola'] += step * min(abs(t3 - last['viola']), 3)
        if abs(last['viola'] - t3) <= 3: last['viola'] = t3
        out_data[2].append((tick, 'on', last['viola'], clv(bv-10)))
        out_data[2].append((tick+rhythm_dur, 'off', last['viola'], 0))
        
        # Violin II
        step = 1 if f5 > last['vln2'] else -1
        last['vln2'] += step * min(abs(f5 - last['vln2']), 3)
        if abs(last['vln2'] - f5) <= 3: last['vln2'] = f5
        out_data[1].append((tick, 'on', last['vln2'], clv(bv-5)))
        out_data[1].append((tick+rhythm_dur, 'off', last['vln2'], 0))
        
        # Violin I — melody
        out_data[0].append((tick, 'on', pitch, clv(bv+8)))
        out_data[0].append((tick+rhythm_dur, 'off', pitch, 0))
        
        # Flute — melody up
        fl = pitch + 12
        if fl <= 108:
            step = 1 if fl > last['flute'] else -1
            last['flute'] += step * min(abs(fl - last['flute']), 4)
            if abs(last['flute'] - fl) <= 4: last['flute'] = fl
            out_data[5].append((tick, 'on', last['flute'], clv(bv-5)))
            out_data[5].append((tick+rhythm_dur, 'off', last['flute'], 0))
        
        # Oboe — suspensions
        if i % 4 == 3 and i > 0:
            _, prev_t, _ = functional_chord(s_prog[(i-1)%len(s_prog)], tonic, scale)
            out_data[6].append((tick, 'on', prev_t, clv(bv-12)))
            out_data[6].append((tick+rhythm_dur//2, 'off', prev_t, 0))
            out_data[6].append((tick+rhythm_dur//2, 'on', t3, clv(bv-14)))
            out_data[6].append((tick+rhythm_dur, 'off', t3, 0))
        
        # Horns — sustained
        if i % 8 == 0:
            out_data[7].append((tick, 'on', max(36, r-5), clv(bv-15)))
            out_data[7].append((tick+rhythm_dur*8, 'off', max(36, r-5), 0))
        
        # Trumpets — fanfare on climax
        if s_name == 'climax' and i % 4 == 0:
            out_data[13].append((tick, 'on', r, clv(bv+15)))
            out_data[13].append((tick+rhythm_dur//2, 'off', r, 0))
            out_data[13].append((tick+rhythm_dur//2, 'on', f5, clv(bv+12)))
            out_data[13].append((tick+rhythm_dur, 'off', f5, 0))
        
        # Timpani — dramatic rolls on climax
        if s_name == 'climax':
            for j in range(4):
                out_data[8].append((tick + j*60, 'on', 38, clv(bv+20)))
                out_data[8].append((tick + j*60 + 50, 'off', 38, 0))
        elif s_name == 'climax_build' and i % 2 == 0:
            out_data[8].append((tick, 'on', 38, clv(bv+10 + i*2//total*20)))
            out_data[8].append((tick+rhythm_dur//4, 'off', 38, 0))
        elif i % 4 == 0:
            out_data[8].append((tick, 'on', 38, clv(bv+10)))
            out_data[8].append((tick+rhythm_dur//4, 'off', 38, 0))
        
        # Harp
        if i % 8 == 0:
            for j, cn in enumerate([r+12, f5, t3, r]):
                if cn <= 108:
                    out_data[9].append((tick + j*80, 'on', cn, clv(bv-25)))
                    out_data[9].append((tick + j*80 + rhythm_dur//3, 'off', cn, 0))
        
        # Counterpoint line — more active in development
        if s_name == 'development' and i % 3 == 0:
            cntr = pitch - 7
            step = 1 if cntr > last['counter'] else -1
            last['counter'] += step * min(abs(cntr - last['counter']), 5)
            if abs(last['counter'] - cntr) <= 5: last['counter'] = cntr
            out_data[12].append((tick + rhythm_dur, 'on', last['counter'], clv(bv-12)))
            out_data[12].append((tick + rhythm_dur*3, 'off', last['counter'], 0))
        
        # Krimanchuli — more present in climax
        if random.random() < (0.5 if s_name == 'climax' else 0.2):
            kp = pitch + 12
            if kp <= 108:
                out_data[10].append((tick, 'on', kp, clv(bv+10)))
                out_data[10].append((tick+rhythm_dur, 'off', kp, 0))
        
        # Celesta — delicate in exposition
        if s_name in ('exposition', 'coda') and i % 6 == 0:
            out_data[11].append((tick, 'on', min(108, r+12), clv(bv-30)))
            out_data[11].append((tick+rhythm_dur//3, 'off', min(108, r+12), 0))
        
        # ═══ DRAMATIC TUTTI on climax hits ═══
        if s_name == 'climax' and i % 16 == 0:
            # Full orchestra hit
            for ch in [0,1,2,3,4,5,13]:
                out_data[ch].append((tick, 'on', r if ch!=13 else f5, clv(127)))
                out_data[ch].append((tick+rhythm_dur, 'off', r if ch!=13 else f5, 0))
    
    return out_data

# ═══ COMPOSE ═══
inp = 'Samnu_Azuzi/midi/Samnu_Azuzi_Full_Opera_Harmonized.mid'
mid_in = md.MidiFile(inp); tpb = mid_in.ticks_per_beat
events = []
abs_t = 0
for track in mid_in.tracks:
    abs_t = 0
    for msg in track:
        abs_t += msg.time
        if msg.type == 'note_on' and msg.velocity > 0:
            events.append((abs_t, msg.note, msg.velocity))
events.sort()

print(f"Building dramatic score from {len(events)} notes...")
out_data = build_dramatic_events(events, GURIAN, 62)

mid_out = md.MidiFile(ticks_per_beat=tpb)
NAMES = ["Strings","Violins II","Violas","Celli","Basses","Flute","Oboe","Horns","Timpani","Harp","Krimanchuli","Celesta","Counterpoint","Trumpets","Tutti"]
PROGS = [48,40,41,42,43,73,68,60,47,46,69,8,40,61,48]

for ch in range(15):
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

out = 'Samnu_Azuzi/midi/Samnu_Azuzi_Dramatic.mid'
mid_out.save(out)
print(f"MIDI: {out}")
print(f"15 tracks — exposition→development→climax→resolution→coda")
print(f"Melodic variants: original, inversion, sequence, ornamented, climactic, fragmented")

wav = out.replace('.mid', '.wav')
print("Rendering...")
os.system(f'timidity -c /tmp/timidity.cfg "{out}" -Ow -o "{wav}" -s 44100 -A120 2>/dev/null')
sz = os.path.getsize(wav)//1048576 if os.path.exists(wav) else 0
print(f"WAV: {sz} MB ✓")
