#!/usr/bin/env python3
"""Enchanting post-processor for both operas — legato, dynamics, ethereal orchestration."""
import mido as md, os, random

def clv(v): return max(1, min(127, int(v)))

def chord_for(pitch, scale, tonic):
    s = scale; pc = (pitch - tonic) % 12
    try: idx = s.index(pc)
    except: idx = min(range(len(s)), key=lambda i: abs(s[i]-pc))
    o = pitch // 12
    r = (tonic//12)*12 + s[idx]
    while r < pitch - 12: r += 12
    while r > pitch: r -= 12
    t = (r//12)*12 + s[(idx+2)%len(s)]
    if t < r: t += 12
    f = (r//12)*12 + s[(idx+4)%len(s)]
    if f < t: f += 12
    return r, t, f

def enchanting(inp, out, scale, tonic, tempo=72):
    """Transform any MIDI into flowing, enchanting orchestral music."""
    mid_in = md.MidiFile(inp); tpb = mid_in.ticks_per_beat
    
    # Collect all melody notes
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
    last_v = {'bass': 36, 'cello': 48, 'viola': 55, 'vln2': 60, 'flute': 72, 'oboe': 65}
    
    total = len(events)
    
    for i, (tick, pitch, vel) in enumerate(events):
        dur = events[i+1][0] - tick if i+1 < len(events) else 480
        dur = max(60, min(dur, 1920))
        
        # Dynamic wave: pp→f→pp over the whole piece, with local waves
        global_frac = i / total
        # Global dynamic arc: soft start, build to climax at 60%, fade to end
        if global_frac < 0.6:
            global_dyn = 0.35 + 0.65 * (global_frac / 0.6)  # pp → f
        else:
            global_dyn = 1.0 - 0.65 * ((global_frac - 0.6) / 0.4)  # f → pp
        
        # Local wave: every 64 events
        local_frac = (i % 64) / 64
        local_wave = 1.0 - 0.2 * abs(local_frac - 0.5) / 0.5
        
        dm = global_dyn * local_wave
        bv = clv(vel * dm)
        
        # Chord
        r, t3, f5 = chord_for(pitch, scale, tonic)
        
        # Legato overlap
        overlap = int(dur * 0.25)
        
        # ═══ VOICES — all legato, all overlapping ═══
        
        # Violins I — melody, singing
        out_data[0].append((tick, 'on', pitch, clv(bv+5)))
        out_data[0].append((tick+dur+overlap, 'off', pitch, 0))
        
        # Violins II — gentle harmony
        target = f5
        step = 1 if target > last_v['vln2'] else -1 if target < last_v['vln2'] else 0
        last_v['vln2'] += step * min(abs(target - last_v['vln2']), 2)
        if abs(last_v['vln2'] - target) <= 2: last_v['vln2'] = target
        out_data[1].append((tick, 'on', last_v['vln2'], clv(bv-3)))
        out_data[1].append((tick+dur+overlap, 'off', last_v['vln2'], 0))
        
        # Violas — warm middle
        target = t3
        step = 1 if target > last_v['viola'] else -1 if target < last_v['viola'] else 0
        last_v['viola'] += step * min(abs(target - last_v['viola']), 2)
        if abs(last_v['viola'] - target) <= 2: last_v['viola'] = target
        out_data[2].append((tick, 'on', last_v['viola'], clv(bv-6)))
        out_data[2].append((tick+dur+overlap, 'off', last_v['viola'], 0))
        
        # Celli — foundation
        target = max(36, r-12)
        step = 1 if target > last_v['cello'] else -1 if target < last_v['cello'] else 0
        last_v['cello'] += step * min(abs(target - last_v['cello']), 3)
        if abs(last_v['cello'] - target) <= 3: last_v['cello'] = target
        out_data[3].append((tick, 'on', last_v['cello'], clv(bv-12)))
        out_data[3].append((tick+dur*2, 'off', last_v['cello'], 0))
        
        # Basses — soft pulse
        target = max(28, r-24)
        step = 1 if target > last_v['bass'] else -1 if target < last_v['bass'] else 0
        last_v['bass'] += step * min(abs(target - last_v['bass']), 2)
        if abs(last_v['bass'] - target) <= 2: last_v['bass'] = target
        if i % 2 == 0:
            out_data[4].append((tick, 'on', last_v['bass'], clv(bv-20)))
            out_data[4].append((tick+dur*3, 'off', last_v['bass'], 0))
        
        # Flute — floating above
        fl_target = pitch + 12
        if fl_target <= 108:
            step = 1 if fl_target > last_v['flute'] else -1
            last_v['flute'] += step * min(abs(fl_target - last_v['flute']), 3)
            if abs(last_v['flute'] - fl_target) <= 3: last_v['flute'] = fl_target
            # Flute enters slightly after strings
            out_data[5].append((tick + dur//3, 'on', last_v['flute'], clv(bv-8)))
            out_data[5].append((tick+dur+overlap, 'off', last_v['flute'], 0))
        
        # Oboe — soft suspensions
        if i % 6 == 3 and i > 3:
            prev_r, prev_t, _ = chord_for(events[i-3][1], scale, tonic)
            out_data[6].append((tick, 'on', prev_t, clv(bv-14)))
            out_data[6].append((tick+dur, 'off', prev_t, 0))
        
        # Horns — very distant
        if i % 16 == 0:
            out_data[7].append((tick, 'on', max(36, r-5), clv(bv-18)))
            out_data[7].append((tick+dur*8, 'off', max(36, r-5), 0))
        
        # Harp — celestial
        if i % 6 == 0:
            for j, cn in enumerate([r+12 if r+12<=108 else 108, f5, t3, r]):
                if cn <= 108:
                    out_data[9].append((tick + j*100, 'on', cn, clv(bv-25)))
                    out_data[9].append((tick + j*100 + dur//2, 'off', cn, 0))
        
        # Celesta — sparkles
        if i % 4 == 0:
            out_data[11].append((tick, 'on', min(108, r+12), clv(bv-30)))
            out_data[11].append((tick+dur//2, 'off', min(108, r+12), 0))
        
        # Soft krimanchuli — only at peaks
        if dm > 0.85 and i % 8 == 4:
            kp = pitch + 12
            if kp <= 108:
                out_data[10].append((tick, 'on', kp, clv(bv+3)))
                out_data[10].append((tick+dur+overlap, 'off', kp, 0))
        
        # Trumpets — only at climax
        if 0.55 < global_frac < 0.65 and i % 8 == 0:
            out_data[13].append((tick, 'on', r, clv(bv+8)))
            out_data[13].append((tick+dur, 'off', r, 0))
    
    NAMES = ["Violins I","Violins II","Violas","Celli","Basses","Flute","Oboe","Horns","Timpani","Harp","Krimanchuli","Celesta","Counterpoint","Trumpets"]
    PROGS = [48,40,41,42,43,73,68,60,47,46,69,8,40,61]
    
    tempo_event_added = False
    for ch in range(14):
        data = out_data[ch]
        if not data: continue
        data.sort(key=lambda x: (x[0], 0 if x[1]=='off' else 1))
        tk = md.MidiTrack(); mid_out.tracks.append(tk)
        if not tempo_event_added:
            tk.append(md.MetaMessage('set_tempo', tempo=833333, time=0))  # 72 BPM = 833333 µs/beat
            tempo_event_added = True
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

# Process BOTH operas
print("✨ ENCHANTING BOTH OPERAS\n")

for label, inp, scale, tonic in [
    ("Samnu Azuzi", "Samnu_Azuzi/midi/Samnu_Azuzi_Full_Opera_Harmonized.mid", [0,2,3,6,7,8,10], 62),
    ("Threshold Stand", "Threshold_Stand/Threshold_Stand_Harmonized.mid", [0,2,4,5,7,9,11], 60),
]:
    if not os.path.exists(inp):
        # Try alternative
        alt = inp.replace('_Symphonic','').replace('_Full_Opera','_Harmonized')
        if os.path.exists(alt): inp = alt
    
    out = inp.replace('.mid', '_Enchanted.mid')
    print(f"{label}...")
    n = enchanting(inp, out, scale, tonic)
    print(f"  {n} notes → 14 tracks, legato, dynamic waves")
    
    wav = out.replace('.mid', '.wav')
    os.system(f'timidity -c /tmp/timidity.cfg "{out}" -Ow -o "{wav}" -s 44100 -A120 2>/dev/null')
    sz = os.path.getsize(wav)//1048576 if os.path.exists(wav) else 0
    print(f"  WAV: {sz} MB ✓\n")

print("BOTH OPERAS ENCHANTED")
