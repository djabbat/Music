#!/usr/bin/env python3
"""Samnu Azuzi — 90+ minute complete opera."""
from ze_music import *
import random, os, mido as md, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

melodies = {}
for fn in ['Chakrulo','Gandagana','Khasanbegura','Guruli_Naduri','gurian','Guruli_Khasanbegura']:
    fp = f'data/midi/georgian/{fn}.mid'
    n = load_midi(fp)
    top = sorted([x for x in n if x.pitch >= 65], key=lambda x: x.start)
    if top: melodies[fn] = top

THEMES = {
    'Gilgamesh': melodies['Chakrulo'], 'Enkidu': melodies['Gandagana'],
    'Ishtar': melodies['Khasanbegura'], 'Humbaba': melodies['Guruli_Khasanbegura'],
    'Shamhat': melodies['Guruli_Naduri'], 'Utnapishtim': melodies['gurian'],
}

tempo = 72
mid = md.MidiFile(ticks_per_beat=480)
ORCH = [(0,40),(1,40),(2,41),(3,42),(4,73),(5,60),(6,61),(7,47),(8,46),(9,55),(10,54),(11,42),(12,68)]
tracks = {}
lt = {}
for ch, prog in ORCH:
    tk = md.MidiTrack(); mid.tracks.append(tk)
    tk.append(md.MetaMessage('set_tempo', tempo=md.bpm2tempo(tempo)))
    tk.append(md.MetaMessage('track_name', name=f'Ch{ch}'))
    tk.append(md.Message('program_change', program=prog, channel=ch, time=0))
    tracks[ch] = tk; lt[ch] = 0
tpb = mid.ticks_per_beat
ct = 0.0

def msg(ch, p, v, st, dt):
    d = max(0, st - lt[ch]); lt[ch] = st + dt
    tracks[ch].append(md.Message('note_on', note=p, velocity=v, time=d, channel=ch))
    tracks[ch].append(md.Message('note_off', note=p, velocity=0, time=dt, channel=ch))

def orch(p0, v0, st, dt, state):
    msg(0, p0, min(127, v0+5), st, dt)
    if random.random() < 0.6: msg(1, max(36, p0-4), v0-8, st, dt*2)
    if random.random() < 0.5: msg(2, max(36, p0-7), v0-12, st, dt*3)
    if random.random() < 0.4: msg(3, max(24, p0-14), v0-18, st, dt*4)
    if random.random() < 0.5 and p0+12 <= 108: msg(4, p0+12, v0-5, st, dt)
    if random.random() < 0.25: msg(5, max(36, p0-5), v0-10, st, dt*5)
    if state in ('PEAK','DRAMATIC') and random.random() < 0.35:
        msg(6, p0, min(127, v0+15), st, dt//2)
    if random.random() < 0.3: msg(7, 38, min(127, v0+15), st, dt//4)
    if random.random() < 0.2: msg(8, min(108, p0+12), v0-15, st, dt*2)
    msg(9, p0, v0+8, st, dt); msg(10, max(40, p0-4), v0-5, st, dt)
    if random.random() < 0.15: msg(11, max(28, p0-24), v0-20, st, dt*12)
    if random.random() < 0.4:
        kp = p0+12 if random.random() < 0.5 else p0+random.choice([5,7])
        if kp <= 108: msg(12, kp, min(127, v0+10), st, dt)

def theme(tm, start_t, speed, state, reps=1):
    global ct; t = start_t; notes = list(tm)
    for rep in range(reps):
        for i, note in enumerate(notes):
            st = int(t * tpb * tempo / 60)
            dt = max(1, int(note.duration * tpb * tempo / 60 * speed))
            orch(note.pitch, note.velocity, st, dt, state)
            t += note.duration * speed
        if reps > 1:
            notes = [Note(pitch=n.pitch+random.choice([0,0,0,2,-2]),
                         start=n.start, duration=n.duration,
                         velocity=n.velocity) for n in tm[:50]]
    ct = t; return t

def drone_sec(n_beats, start_t):
    global ct; t = start_t
    for i in range(n_beats):
        st = int(t * tpb * tempo / 60); bt = max(1, int(3.5 * tpb * tempo / 60))
        bp = [36,43,48,36,43,50,38,43][i%8]
        msg(11, bp, 50-int(i*0.5), st, bt); msg(3, bp, 35-int(i*0.3), st, bt)
        if i % 4 == 0: msg(7, 38, 55, st, bt//8)
        if i % 6 == 0: msg(12, bp+24, 58, st, bt//2)
        t += 3.8
    ct = t; return t

def battle_sec(n_hits, start_t):
    global ct; t = start_t
    for i in range(n_hits):
        st = int(t * tpb * tempo / 60); dt = max(1, int(0.35 * tpb * tempo / 60))
        pp = [60,62,64,65,67,69,71,72,60,63,65,67][i%12]
        msg(0, pp, 95, st, dt); msg(6, pp, 105, st, dt//2)
        msg(7, 38+random.choice([0,5,7]), 100, st, dt//4)
        if i % 3 == 0: msg(12, min(108, pp+12), 88, st, dt)
        t += 0.55
    ct = t; return t

def lament(tm, start_t):
    global ct; t = start_t; notes = list(tm[:80])
    for rep in range(3):
        for i, note in enumerate(notes):
            st = int(t * tpb * tempo / 60)
            dt = max(1, int(note.duration * tpb * tempo / 60 * 1.5))
            p0, v0 = note.pitch, note.velocity-20
            msg(0, p0, v0, st, dt); msg(3, max(24, p0-24), v0-25, st, dt*2)
            msg(9, p0-12, v0, st, dt)
            if i % 8 == 0: msg(7, 38, 40, st, dt//4)
            t += note.duration * 1.5
    ct = t; return t

# ═══════════════════════════════════════════
# COMPOSE
# ═══════════════════════════════════════════
print("COMPOSING 90+ MINUTE OPERA...")

# OVERTURE (~8 min internal)
ct = drone_sec(30, ct)
ct = theme(THEMES['Gilgamesh'], ct, 1.0, 'BUILD', reps=2)
ct = theme(THEMES['Ishtar'], ct, 0.8, 'DRAMATIC', reps=2)
ct = battle_sec(40, ct)
ct = theme(THEMES['Enkidu'], ct, 0.7, 'RESOLVE', reps=2)
ct = drone_sec(20, ct)
print(f'  OVERTURE: {ct:.0f}s')

# ACT I (~15 min internal)
ct = drone_sec(25, ct)
ct = theme(THEMES['Gilgamesh'], ct, 0.9, 'PEAK', reps=3)
ct = drone_sec(15, ct)
ct = theme(THEMES['Enkidu'], ct, 0.6, 'DRONE', reps=2)
ct = theme(THEMES['Shamhat'], ct, 0.7, 'BUILD', reps=2)
ct = theme(THEMES['Gilgamesh'], ct, 1.0, 'PEAK', reps=2)
ct = battle_sec(30, ct)
ct = theme(THEMES['Gilgamesh'], ct, 0.6, 'RESOLVE', reps=2)
print(f'  ACT I: {ct:.0f}s')

# ACT II (~16 min internal)
ct = drone_sec(20, ct)
ct = theme(THEMES['Gilgamesh'], ct, 0.8, 'BUILD', reps=3)
ct = drone_sec(15, ct)
ct = theme(THEMES['Humbaba'], ct, 0.5, 'DRONE', reps=3)
ct = battle_sec(60, ct)
ct = theme(THEMES['Gilgamesh'], ct, 1.1, 'PEAK', reps=2)
ct = theme(THEMES['Ishtar'], ct, 0.9, 'DRAMATIC', reps=3)
print(f'  ACT II: {ct:.0f}s')

# ACT III (~18 min internal)
ct = theme(THEMES['Ishtar'], ct, 0.7, 'DRAMATIC', reps=3)
ct = battle_sec(50, ct)
ct = drone_sec(20, ct)
ct = lament(THEMES['Enkidu'], ct)
ct = drone_sec(25, ct)
ct = lament(THEMES['Gilgamesh'], ct)
ct = drone_sec(30, ct)
print(f'  ACT III: {ct:.0f}s')

# ACT IV (~18 min internal)
ct = drone_sec(35, ct)
ct = theme(THEMES['Gilgamesh'], ct, 0.5, 'DRONE', reps=3)
ct = drone_sec(20, ct)
ct = theme(THEMES['Utnapishtim'], ct, 0.4, 'CALM', reps=4)
ct = drone_sec(25, ct)
ct = theme(THEMES['Utnapishtim'], ct, 0.3, 'COMPLEX', reps=3)
ct = drone_sec(20, ct)
print(f'  ACT IV: {ct:.0f}s')

# ACT V (~15 min internal)
ct = theme(THEMES['Gilgamesh'], ct, 0.8, 'BUILD', reps=2)
ct = drone_sec(15, ct)
ct = theme(THEMES['Enkidu'], ct, 0.4, 'DRAMATIC', reps=2)
ct = drone_sec(15, ct)
ct = lament(THEMES['Gilgamesh'], ct)
ct = theme(THEMES['Gilgamesh'], ct, 0.9, 'PEAK', reps=3)
ct = drone_sec(25, ct)
ct = theme(THEMES['Gilgamesh'], ct, 0.4, 'RESOLVE', reps=2)
ct = drone_sec(35, ct)
print(f'  ACT V: {ct:.0f}s')

internal_min = int(ct // 60)
internal_sec = int(ct % 60)
est_play = int(ct * 1.55)  # timidity stretches ~1.55x

fp = 'Samnu_Azuzi/midi/Samnu_Azuzi_Full_Opera.mid'
mid.save(fp)
print(f'\nCOMPOSITION DONE')
print(f'  Internal: {internal_min}:{internal_sec:02d}')
print(f'  Est.play: ~{est_play//60}:{est_play%60:02d}')
print(f'  MIDI: {fp}')

print('\nRENDERING AUDIO...')
os.system(f'timidity -c /tmp/timidity.cfg "{fp}" -Ow -o /tmp/samnu_full.wav -s 44100 -A120')
sz = os.path.getsize('/tmp/samnu_full.wav') // 1048576 if os.path.exists('/tmp/samnu_full.wav') else 0
os.system('cp /tmp/samnu_full.wav Samnu_Azuzi/midi/Samnu_Azuzi_Full_Opera.wav')
print(f'WAV: {sz} MB')
print('READY')
