#!/usr/bin/env python3
"""Samnu Azuzi — with harmonic & rhythmic post-processing."""
from ze_music import *
import random, os, mido as md

melodies = {}
for fn in ['Chakrulo','Gandagana','Khasanbegura','Guruli_Naduri','gurian','Guruli_Khasanbegura']:
    n = load_midi(f'data/midi/georgian/{fn}.mid')
    top = sorted([x for x in n if x.pitch >= 65], key=lambda x: x.start)
    if top: melodies[fn] = top

THEMES = {
    'Gilgamesh': melodies['Chakrulo'], 'Enkidu': melodies['Gandagana'],
    'Ishtar': melodies['Khasanbegura'], 'Humbaba': melodies['Guruli_Khasanbegura'],
    'Shamhat': melodies['Guruli_Naduri'], 'Utnapishtim': melodies['gurian'],
}

# Gurian scale degrees → possible chords (triads built on each degree)
GURIAN_SCALE = [0, 2, 3, 6, 7, 8, 10]  # C D Eb F# G Ab Bb

def gurian_chord(root_midi, degree):
    """Build a chord on scale degree. Returns [root, third, fifth] MIDI pitches."""
    scale = GURIAN_SCALE
    root_class = root_midi % 12
    # Find position in scale
    try:
        idx = scale.index(root_class)
    except ValueError:
        idx = min(range(len(scale)), key=lambda i: abs(scale[i]-root_class))
    third_idx = (idx + 2) % len(scale)
    fifth_idx = (idx + 4) % len(scale)
    octave = root_midi // 12
    root_p = octave*12 + scale[idx]
    third_p = octave*12 + scale[third_idx]
    fifth_p = octave*12 + scale[fifth_idx]
    # Keep in range
    if third_p < root_p: third_p += 12
    if fifth_p < third_p: fifth_p += 12
    return [root_p, third_p, fifth_p]

# Rhythm patterns for different sections
RHYTHMS = {
    'DRONE':    [1.0, 0, 0, 0, 1.0, 0, 0, 0],  # slow pulse
    'BUILD':    [0.5, 0.5, 0, 0.5, 0.5, 0.5, 0, 0.5],
    'PEAK':     [0.25, 0.25, 0.25, 0.25, 0.5, 0.25, 0.25, 0.5],
    'DRAMATIC': [0.25, 0.5, 0.25, 0.25, 0.25, 0.5, 0.25, 0.25],
    'RESOLVE':  [1.0, 0, 0.5, 0, 1.0, 0, 0.5, 0],
    'CALM':     [1.5, 0, 0, 0, 1.0, 0, 0, 0],
    'COMPLEX':  [0.25, 0.5, 0.25, 0.25, 0.5, 0.25, 0.25, 0.5],
}

tempo = 72
mid = md.MidiFile(ticks_per_beat=480)

# 15 tracks with proper names
TRACKS = [
    (0, 48, "Strings Ensemble"),
    (1, 40, "Violins I"),
    (2, 41, "Violas"),
    (3, 42, "Celli"),
    (4, 43, "Basses"),
    (5, 73, "Flutes"),
    (6, 68, "Oboes"),
    (7, 60, "French Horns"),
    (8, 61, "Trumpets"),
    (9, 47, "Timpani"),
    (10, 46, "Harp"),
    (11, 54, "VOICE - Mtkmeli"),
    (12, 53, "VOICE - Modzakhili"),
    (13, 52, "VOICE - Bani"),
    (14, 69, "KRIMANCHULI"),
]

tracks = {}; lt = {}
for ch, prog, name in TRACKS:
    tk = md.MidiTrack(); mid.tracks.append(tk)
    tk.append(md.MetaMessage('set_tempo', tempo=md.bpm2tempo(tempo)))
    tk.append(md.MetaMessage('track_name', name=name))
    tk.append(md.Message('program_change', program=prog, channel=ch, time=0))
    tracks[ch] = tk; lt[ch] = 0
tpb = mid.ticks_per_beat; ct = 0.0

def msg(ch, p, v, st, dt):
    if not (21 <= p <= 108): return
    d = max(0, st - lt[ch]); lt[ch] = st + dt
    tracks[ch].append(md.Message('note_on', note=p, velocity=v, time=d, channel=ch))
    tracks[ch].append(md.Message('note_off', note=p, velocity=0, time=dt, channel=ch))

def harmonize_and_play(p0, v0, st, dt, state, phrase_pos):
    """Post-processing: build full chord, apply voice leading, rhythm articulation."""
    
    # 1. Build Gurian chord from melody note as root
    chord = gurian_chord(p0, 0)
    root, third, fifth = chord
    
    # 2. Voice leading — smooth movement
    # Bass (octave below root)
    msg(4, max(28, root-24), v0-25, st, dt*2)
    # Cello (root in low register)
    msg(3, max(36, root-12), v0-20, st, dt)
    # Viola (third or fifth depending on position)
    msg(2, third, v0-15, st, dt)
    # Violin II (fifth)
    msg(1, fifth, v0-10, st, dt)
    # Violin I / Strings — melody
    msg(0, p0, v0+5, st, dt)
    
    # 3. Woodwinds — melodic doubling with passing tones
    if phrase_pos % 4 != 0:
        msg(5, p0+12 if p0+12 <= 108 else p0, v0-8, st, dt)  # flute octave up
    if phrase_pos % 3 == 0:
        msg(6, third, v0-10, st, dt*1.5)  # oboe on chord third
    
    # 4. Brass — harmonic pillars (every 4th beat)
    if phrase_pos % 4 == 0:
        msg(7, root-5 if root-5 >= 36 else root, v0-12, st, dt*3)  # horn
    if phrase_pos % 8 == 0 and state in ('PEAK','DRAMATIC'):
        msg(8, p0, min(127, v0+18), st, dt//2)  # trumpet fanfare
    
    # 5. Timpani — Gurian rhythmic pulse
    rhy = RHYTHMS.get(state, RHYTHMS['BUILD'])
    beat_in_bar = phrase_pos % 8
    if rhy[beat_in_bar] > 0:
        msg(9, 38 if beat_in_bar % 2 == 0 else 43, v0+15, st, int(rhy[beat_in_bar] * tpb * tempo / 60))
    
    # 6. Harp — arpeggiated chord on phrase starts
    if phrase_pos % 8 == 0:
        for delay, chord_note in enumerate([root, third, fifth, root+12]):
            arp_st = st + delay * int(0.08 * tpb * tempo / 60)
            msg(10, min(108, chord_note), v0-20, arp_st, dt//4)
    
    # 7. Vocal trio — Gurian polyphony with harmonic enrichment
    msg(11, p0, v0+8, st, dt)      # Mtkmeli — melody
    msg(12, third, v0-3, st, dt)   # Modzakhili — chord third (not just parallel!)
    if phrase_pos % 12 == 0:
        msg(13, max(30, root-24), v0-22, st, dt*8)  # Bani — bass drone with harmonic root
    
    # 8. Krimanchuli — yodel with harmonic awareness
    km = phrase_pos % 8
    if km in (0, 3, 5):
        kp = p0 + 12  # falsetto on chord root octave
    elif km == 7:
        kp = fifth  # resolution on chord fifth
    else:
        kp = random.choice([root, third, fifth]) + 12  # leap within chord
    if kp <= 108:
        msg(14, kp, min(127, v0+12), st, dt)
        # Grace note — chord tone
        if random.random() < 0.4:
            grace = random.choice([root, third, fifth]) + 12
            if grace <= 108:
                msg(14, grace, v0+5, st, dt//4)


def theme(tm, start_t, speed, state, reps=1):
    global ct; t = start_t; notes = list(tm)
    phrase = 0
    for rep in range(reps):
        for i, note in enumerate(notes):
            st = int(t * tpb * tempo / 60)
            dt = max(1, int(note.duration * tpb * tempo / 60 * speed))
            harmonize_and_play(note.pitch, note.velocity, st, dt, state, phrase)
            t += note.duration * speed; phrase += 1
        notes = [Note(pitch=n.pitch+random.choice([0,0,0,2,-2]),
                     start=n.start, duration=n.duration, velocity=n.velocity) for n in tm[:50]]
    ct = t; return t

def drone_sec(n_beats, start_t, state='DRONE'):
    global ct; t = start_t
    for i in range(n_beats):
        st = int(t * tpb * tempo / 60); bt = max(1, int(3.5 * tpb * tempo / 60))
        bp = GURIAN_SCALE[i % len(GURIAN_SCALE)] + 36  # bass in Gurian scale
        chord = gurian_chord(bp, 0)
        msg(4, bp, 55, st, bt); msg(3, chord[1], 40, st, bt)
        msg(2, chord[2], 40, st, bt*2)
        if i % 4 == 0: msg(9, 38, 60, st, bt//8)
        if i % 6 == 0: msg(14, min(108, bp+24), 60, st, bt//2)
        if i % 3 == 0: msg(10, min(108, chord[2]+12), 45, st, bt//2)
        t += 3.8
    ct = t; return t

def battle_sec(n_hits, start_t):
    global ct; t = start_t
    for i in range(n_hits):
        st = int(t * tpb * tempo / 60); dt = max(1, int(0.35 * tpb * tempo / 60))
        pp = GURIAN_SCALE[i % 7] + 60
        chord = gurian_chord(pp, 0)
        for j, cp in enumerate(chord):
            msg(j, cp, 90+j*5, st, dt)
        msg(8, pp, 110, st, dt//2); msg(9, 38+random.choice([0,5,7]), 105, st, dt//4)
        if i % 3 == 0: msg(14, min(108, pp+12), 90, st, dt)
        t += 0.55
    ct = t; return t

def lament(tm, start_t):
    global ct; t = start_t; notes = list(tm[:80])
    phrase = 0
    for rep in range(3):
        for i, note in enumerate(notes):
            st = int(t * tpb * tempo / 60)
            dt = max(1, int(note.duration * tpb * tempo / 60 * 1.5))
            p0, v0 = note.pitch, note.velocity-25
            chord = gurian_chord(p0, 0)
            msg(0, p0, v0, st, dt); msg(4, max(28, chord[0]-24), v0-30, st, dt*2)
            msg(3, chord[0]-12, v0-25, st, dt); msg(11, p0-12, v0, st, dt)
            if i % 8 == 0: msg(9, 38, 35, st, dt//4)
            if i % 12 == 0:
                for dly, cn in enumerate(chord):
                    msg(10, min(108, cn), v0-30, st+dly*int(0.1*tpb*tempo/60), dt//4)
            t += note.duration * 1.5; phrase += 1
    ct = t; return t

# ═══ COMPOSE ═══
print("HARMONIZED OPERA — Gurian chords + rhythm patterns")
ct = drone_sec(30, ct)
ct = theme(THEMES['Gilgamesh'], ct, 1.0, 'BUILD', reps=2)
ct = theme(THEMES['Ishtar'], ct, 0.8, 'DRAMATIC', reps=2)
ct = battle_sec(40, ct)
ct = theme(THEMES['Enkidu'], ct, 0.7, 'RESOLVE', reps=2)
ct = drone_sec(20, ct)
print(f'OVERTURE: {ct:.0f}s')

ct = drone_sec(25, ct); ct = theme(THEMES['Gilgamesh'], ct, 0.9, 'PEAK', reps=3)
ct = drone_sec(15, ct); ct = theme(THEMES['Enkidu'], ct, 0.6, 'DRONE', reps=2)
ct = theme(THEMES['Shamhat'], ct, 0.7, 'BUILD', reps=2)
ct = theme(THEMES['Gilgamesh'], ct, 1.0, 'PEAK', reps=2)
ct = battle_sec(30, ct); ct = theme(THEMES['Gilgamesh'], ct, 0.6, 'RESOLVE', reps=2)
print(f'ACT I: {ct:.0f}s')

ct = drone_sec(20, ct); ct = theme(THEMES['Gilgamesh'], ct, 0.8, 'BUILD', reps=3)
ct = drone_sec(15, ct); ct = theme(THEMES['Humbaba'], ct, 0.5, 'DRONE', reps=3)
ct = battle_sec(60, ct); ct = theme(THEMES['Gilgamesh'], ct, 1.1, 'PEAK', reps=2)
ct = theme(THEMES['Ishtar'], ct, 0.9, 'DRAMATIC', reps=3)
print(f'ACT II: {ct:.0f}s')

ct = theme(THEMES['Ishtar'], ct, 0.7, 'DRAMATIC', reps=3)
ct = battle_sec(50, ct); ct = drone_sec(20, ct)
ct = lament(THEMES['Enkidu'], ct); ct = drone_sec(25, ct)
ct = lament(THEMES['Gilgamesh'], ct); ct = drone_sec(30, ct)
print(f'ACT III: {ct:.0f}s')

ct = drone_sec(35, ct); ct = theme(THEMES['Gilgamesh'], ct, 0.5, 'DRONE', reps=3)
ct = drone_sec(20, ct); ct = theme(THEMES['Utnapishtim'], ct, 0.4, 'CALM', reps=4)
ct = drone_sec(25, ct); ct = theme(THEMES['Utnapishtim'], ct, 0.3, 'COMPLEX', reps=3)
ct = drone_sec(20, ct)
print(f'ACT IV: {ct:.0f}s')

ct = theme(THEMES['Gilgamesh'], ct, 0.8, 'BUILD', reps=2)
ct = drone_sec(15, ct); ct = theme(THEMES['Enkidu'], ct, 0.4, 'DRAMATIC', reps=2)
ct = drone_sec(15, ct); ct = lament(THEMES['Gilgamesh'], ct)
ct = theme(THEMES['Gilgamesh'], ct, 0.9, 'PEAK', reps=3)
ct = drone_sec(25, ct); ct = theme(THEMES['Gilgamesh'], ct, 0.4, 'RESOLVE', reps=2)
ct = drone_sec(35, ct)
print(f'ACT V: {ct:.0f}s')

fp = 'Samnu_Azuzi/midi/Samnu_Azuzi_Harmonized.mid'; mid.save(fp)
print(f'\nCOMPOSED: {fp}')
print(f'Internal: {int(ct//60)}:{int(ct%60):02d}')
print(f'\nRENDERING...')
os.system(f'timidity -c /tmp/timidity.cfg "{fp}" -Ow -o /tmp/samnu_harm.wav -s 44100 -A120 2>/dev/null')
os.system('cp /tmp/samnu_harm.wav Samnu_Azuzi/midi/Samnu_Azuzi_Harmonized.wav')
sz = os.path.getsize('/tmp/samnu_harm.wav')//1048576 if os.path.exists('/tmp/samnu_harm.wav') else 0
print(f'DONE: {sz} MB')
