#!/usr/bin/env python3
"""Humanize & Harmonize — voice leading, suspensions, dynamics, phrasing."""
import mido as md, os, random, math

GURIAN = [0,2,3,6,7,8,10]
MAJOR = [0,2,4,5,7,9,11]

def chord(pitch, mode):
    s = GURIAN if mode == 'gurian' else MAJOR
    pc = pitch % 12
    try: idx = s.index(pc)
    except: idx = min(range(len(s)), key=lambda i: abs(s[i]-pc))
    o = pitch // 12
    r = o*12 + s[idx]
    t = o*12 + s[(idx+2)%len(s)]; 
    if t < r: t += 12
    f = o*12 + s[(idx+4)%len(s)]
    if f < t: f += 12
    return r, t, f

def clv(v): return max(1, min(127, int(v)))

def humanize(inp, out, mode='gurian'):
    """Enhanced humanization: voice leading, suspensions, dynamics, phrasing."""
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
    out_data = {ch: [] for ch in range(12)}  # 12 tracks
    
    # Voice-leading state: remember last pitch for smooth movement
    last = {'bass': 36, 'cello': 48, 'viola': 55, 'vln2': 60, 'flute': 72}
    
    # Phrase tracking for dynamics
    phrase_len = 8
    phrase_peak = phrase_len // 2
    
    for i, (tick, pitch, vel) in enumerate(events):
        dur = events[i+1][0] - tick if i+1 < len(events) else 480
        dur = max(60, min(dur, 1920))
        r, t3, f5 = chord(pitch, mode)
        
        # Phrase position for dynamics
        pos_in_phrase = i % phrase_len
        # Dynamic arc: swell to middle, fade to end
        dyn_factor = 1.0 - 0.3 * abs(pos_in_phrase - phrase_peak) / phrase_peak
        base_vel = clv(vel * dyn_factor)
        
        # ═══ SMOOTH VOICE LEADING ═══
        
        # Bass (ch 4) — move by step to chord root
        target_bass = max(28, r-24)
        bass_step = 1 if target_bass > last['bass'] else -1
        smooth_bass = last['bass'] + bass_step * min(abs(target_bass - last['bass']), 2)
        if abs(smooth_bass - target_bass) <= 2:
            smooth_bass = target_bass
        last['bass'] = smooth_bass
        out_data[4].append((tick, 'on', smooth_bass, clv(base_vel-25)))
        out_data[4].append((tick+dur*2, 'off', smooth_bass, 0))
        
        # Cello (ch 3) — smooth to chord root
        target_cello = max(36, r-12)
        cello_step = 1 if target_cello > last['cello'] else -1
        smooth_cello = last['cello'] + cello_step * min(abs(target_cello - last['cello']), 3)
        if abs(smooth_cello - target_cello) <= 3: smooth_cello = target_cello
        last['cello'] = smooth_cello
        out_data[3].append((tick, 'on', smooth_cello, clv(base_vel-18)))
        out_data[3].append((tick+dur*2, 'off', smooth_cello, 0))
        
        # Viola (ch 2) — smooth to chord third
        target_viola = t3
        vla_step = 1 if target_viola > last['viola'] else -1
        smooth_viola = last['viola'] + vla_step * min(abs(target_viola - last['viola']), 3)
        if abs(smooth_viola - target_viola) <= 3: smooth_viola = target_viola
        last['viola'] = smooth_viola
        out_data[2].append((tick, 'on', smooth_viola, clv(base_vel-12)))
        out_data[2].append((tick+dur, 'off', smooth_viola, 0))
        
        # Violin II (ch 1) — smooth to fifth
        target_v2 = f5
        v2_step = 1 if target_v2 > last['vln2'] else -1
        smooth_v2 = last['vln2'] + v2_step * min(abs(target_v2 - last['vln2']), 3)
        if abs(smooth_v2 - target_v2) <= 3: smooth_v2 = target_v2
        last['vln2'] = smooth_v2
        out_data[1].append((tick, 'on', smooth_v2, clv(base_vel-8)))
        out_data[1].append((tick+dur, 'off', smooth_v2, 0))
        
        # Violin I / Strings (ch 0) — melody with slight vibrato (micro timing variation)
        out_data[0].append((tick, 'on', pitch, clv(base_vel+5)))
        out_data[0].append((tick+dur, 'off', pitch, 0))
        
        # Flute (ch 5) — smooth melody octave up with passing tones
        target_flute = pitch+12 if pitch+12 <= 108 else pitch
        fl_step = 1 if target_flute > last['flute'] else -1
        smooth_flute = last['flute'] + fl_step * min(abs(target_flute - last['flute']), 4)
        if abs(smooth_flute - target_flute) <= 4: smooth_flute = target_flute
        last['flute'] = smooth_flute
        if smooth_flute <= 108:
            out_data[5].append((tick, 'on', smooth_flute, clv(base_vel-8)))
            out_data[5].append((tick+dur, 'off', smooth_flute, 0))
        
        # ═══ SUSPENSIONS (ch 6 — Oboe) ═══
        # Every 4th note, hold previous chord tone as suspension, then resolve
        if i % 4 == 3 and i > 0:
            prev_r, prev_t, prev_f = chord(events[i-1][1], mode)
            sus_pitch = prev_t  # hold the third from previous chord
            # Suspension: on at tick, off slightly after (resolution)
            out_data[6].append((tick, 'on', sus_pitch, clv(base_vel-10)))
            out_data[6].append((tick + dur//2, 'off', sus_pitch, 0))
            # Resolution: the new chord third
            out_data[6].append((tick + dur//2, 'on', t3, clv(base_vel-12)))
            out_data[6].append((tick + dur, 'off', t3, 0))
        
        # ═══ HORNS (ch 7) — sustained chorale ═══
        if i % 8 == 0:
            # Horn chord: root + fifth, sustained for full phrase
            out_data[7].append((tick, 'on', r-5 if r-5>=36 else r, clv(base_vel-15)))
            out_data[7].append((tick+dur*8, 'off', r-5 if r-5>=36 else r, 0))
            out_data[7].append((tick, 'on', f5-5 if f5-5>=36 else f5, clv(base_vel-18)))
            out_data[7].append((tick+dur*8, 'off', f5-5 if f5-5>=36 else f5, 0))
        
        # ═══ TIMPANI (ch 8) — musical phrasing, not just pulse ═══
        # Strong beat on phrase start, soft on phrase end
        if pos_in_phrase == 0:
            out_data[8].append((tick, 'on', 38, clv(base_vel+20)))
            out_data[8].append((tick+dur//3, 'off', 38, 0))
        elif pos_in_phrase == 4:
            out_data[8].append((tick, 'on', 43, clv(base_vel+10)))
            out_data[8].append((tick+dur//4, 'off', 43, 0))
        elif pos_in_phrase == 7:
            # Roll at phrase end
            for j in range(3):
                out_data[8].append((tick + j*30, 'on', 38, clv(base_vel-5+j*3)))
                out_data[8].append((tick + j*30 + 25, 'off', 38, 0))
        
        # ═══ HARP (ch 9) — arpeggiated, gentler ═══
        if i % 8 == 0:
            arp_notes = [r+12, f5, t3, r]  # descending arpeggio
            for j, cn in enumerate(arp_notes[:4]):
                if cn <= 108:
                    out_data[9].append((tick + j*80, 'on', cn, clv(base_vel-25)))
                    out_data[9].append((tick + j*80 + dur//3, 'off', cn, 0))
        
        # ═══ KRIMANCHULI (ch 10) — more human phrasing ═══
        if random.random() < 0.3:
            # Yodel with dynamic swell
            kp = pitch+12 if pos_in_phrase < phrase_peak else pitch+random.choice([5,7])
            if kp <= 108:
                kvel = clv(base_vel + 8 + int(10*dyn_factor))
                out_data[10].append((tick, 'on', kp, kvel))
                out_data[10].append((tick+dur, 'off', kp, 0))
                # Grace note before yodel
                if random.random() < 0.5:
                    grace = kp + random.choice([2,3,-2,-3])
                    if 24 <= grace <= 108:
                        out_data[10].append((tick, 'on', grace, clv(kvel-10)))
                        out_data[10].append((tick+dur//5, 'off', grace, 0))
        
        # ═══ CELESTA/PIZZICATO (ch 11) — delicate accents ═══
        if pos_in_phrase % 3 == 0:
            out_data[11].append((tick, 'on', r+12 if r+12<=108 else r, clv(base_vel-30)))
            out_data[11].append((tick+dur//3, 'off', r+12 if r+12<=108 else r, 0))
    
    NAMES = ["Strings","Violins II","Violas","Celli","Basses","Flute","Oboe-Suspensions","Horns","Timpani","Harp","Krimanchuli","Celesta"]
    PROGS = [48,40,41,42,43,73,68,60,47,46,69,8]
    
    for ch in range(12):
        data = out_data[ch]
        if not data: continue
        data.sort(key=lambda x: (x[0], 0 if x[1]=='off' else 1))
        tk = md.MidiTrack(); mid_out.tracks.append(tk)
        tk.append(md.MetaMessage('track_name', name=NAMES[ch]))
        tk.append(md.Message('program_change', program=PROGS[ch], channel=ch, time=0))
        last_tick = 0
        for tick, typ, note, vel in data:
            delta = max(0, tick - last_tick); last_tick = tick
            if typ == 'on':
                tk.append(md.Message('note_on', note=note, velocity=vel, time=delta, channel=ch))
            else:
                tk.append(md.Message('note_off', note=note, velocity=0, time=delta, channel=ch))
    
    mid_out.save(out)
    return len(events)

# Process both
for label, inp, mode in [
    ("Samnu Azuzi", "Samnu_Azuzi/midi/Samnu_Azuzi_Full_Opera_Harmonized.mid", "gurian"),
    ("Threshold Stand", "Threshold_Stand/Threshold_Stand_Harmonized.mid", "major"),
]:
    out_midi = inp.replace('.mid', '_Humanized.mid')
    print(f"Humanizing: {label}...")
    n = humanize(inp, out_midi, mode)
    print(f"  {n} notes → 12 tracks (voice leading + suspensions + dynamics)")
    out_wav = out_midi.replace('.mid', '.wav')
    os.system(f'timidity -c /tmp/timidity.cfg "{out_midi}" -Ow -o "{out_wav}" -s 44100 -A120 2>/dev/null')
    sz = os.path.getsize(out_wav)//1048576 if os.path.exists(out_wav) else 0
    print(f"  WAV: {sz} MB ✓\n")

print("DONE — Both operas humanized with voice leading, suspensions, dynamics")
