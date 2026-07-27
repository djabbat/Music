
#!/usr/bin/env python3
"""Threshold Stand — Opera Generator."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ze_music import *

STATES = {
    "CALM":    (0.00, 0.12, 0.20),
    "BUILD":   (0.18, 0.16, 0.45),
    "PEAK":    (0.35, 0.12, 0.75),
    "RESOLVE": (-0.10, 0.15, 0.35),
    "DRONE":   (0.02, 0.10, 0.25),
    "DRAMATIC":(-0.25, 0.14, 0.85),
    "COMPLEX": (0.05, 0.22, 0.50),
    "GROOVE":  (0.30, 0.10, 0.55),
}

class OperaGenerator:
    """Ze Opera — Threshold Stand generator."""
    def __init__(self, seed=42):
        import random
        random.seed(seed)
        self.scale = [0,2,4,5,7,9,11]
        self.ps = []
        for o in range(4):
            for s in self.scale:
                p = 36+s+o*12
                if 36<=p<=96: self.ps.append(p)
        self.cp = 60; self.all_n = []
    
    def section(self, state, n_events, style="orchestral"):
        v, tau, chi = STATES[state]
        notes = []; t = 0.0; zs = ZeStream(); ci = len(self.ps)//2
        import random
        
        for i in range(n_events):
            cv = zs.v; err = v-cv
            pt = max(0.05, min(0.95, 0.5+0.4*err))
            ev = ZeEvent.T if random.random()<pt else ZeEvent.S
            zs.events.append(ev)
            
            st_ranges = {"aria":[1,2,3,4,5], "chorus":[1,2,2,3], "recit":[1,1,2,2,1,1,3,5], "orchestral":[1,2,3,4]}
            steps = st_ranges.get(style, [1,2,2,3])
            step = random.choice(steps) if ev==ZeEvent.T else -random.choice(steps)
            
            ci = max(0, min(len(self.ps)-1, ci+step))
            pitch = self.ps[ci]
            dur = 1.0 if style in ("aria","chorus") else (0.5 if style=="recit" else 0.75)
            vel = 78 + int(chi*35) + random.randint(-8,12)
            notes.append(Note(pitch=pitch, start=t, duration=dur, velocity=max(20,min(127,vel))))
            
            if style in ("orchestral","chorus") and random.random()<0.5:
                hi = max(0, ci-random.choice([2,3,4]))
                notes.append(Note(pitch=self.ps[hi], start=t, duration=dur, velocity=vel-12))
            if style == "orchestral" and random.random()<0.3:
                bi = max(0, ci-7)
                notes.append(Note(pitch=self.ps[bi], start=t, duration=dur, velocity=vel-18))
            t += dur*0.25
        return notes
    
    def compose(self):
        ct = 0.0
        
        # OVERTURE
        for state in ["CALM","BUILD","COMPLEX","PEAK","DRAMATIC","RESOLVE","PEAK","CALM"]:
            notes = self.section(state, 32, "orchestral")
            for n in notes: n.start += ct
            ct = notes[-1].start+notes[-1].duration if notes else ct
            self.all_n.extend(notes)
        
        # ACT I
        for name, state, n, style in [
            ("DRONE",40,"orchestral"),("BUILD",48,"aria"),("PEAK",56,"chorus"),
            ("COMPLEX",36,"recit"),("DRAMATIC",48,"orchestral"),("RESOLVE",40,"chorus")]:
            notes = self.section(state, n, style)
            for n2 in notes: n2.start += ct
            ct = notes[-1].start+notes[-1].duration if notes else ct
            self.all_n.extend(notes)
        
        # ACT II
        for name, state, n, style in [
            ("CALM",32,"orchestral"),("BUILD",56,"aria"),("GROOVE",48,"orchestral"),
            ("COMPLEX",56,"aria"),("PEAK",64,"chorus"),("DRONE",40,"orchestral"),
            ("RESOLVE",48,"chorus")]:
            notes = self.section(state, n, style)
            for n2 in notes: n2.start += ct
            ct = notes[-1].start+notes[-1].duration if notes else ct
            self.all_n.extend(notes)
        
        # ACT III
        for name, state, n, style in [
            ("DRAMATIC",56,"orchestral"),("PEAK",64,"aria"),("COMPLEX",72,"chorus"),
            ("GROOVE",56,"orchestral"),("DRONE",48,"recit"),("BUILD",56,"aria"),
            ("PEAK",80,"chorus"),("RESOLVE",52,"chorus")]:
            notes = self.section(state, n, style)
            for n2 in notes: n2.start += ct
            ct = notes[-1].start+notes[-1].duration if notes else ct
            self.all_n.extend(notes)
        
        return self.all_n
    
    def save(self, fp, tempo=90):
        import mido as md
        mid = md.MidiFile(ticks_per_beat=480)
        tk = md.MidiTrack(); mid.tracks.append(tk)
        tk.append(md.MetaMessage('set_tempo', tempo=md.bpm2tempo(tempo)))
        tk.append(md.MetaMessage('track_name', name='Ze Opera - Threshold Stand'))
        tpb = mid.ticks_per_beat; lt = 0
        for n in sorted(self.all_n, key=lambda x: x.start):
            st = int(n.start*tpb*tempo/60); dt = max(1, int(n.duration*tpb*tempo/60))
            d = max(0, st-lt)
            tk.append(md.Message('note_on', note=n.pitch, velocity=n.velocity, time=d, channel=0))
            tk.append(md.Message('note_off', note=n.pitch, velocity=0, time=dt, channel=0))
            lt = st+dt
        mid.save(fp)

if __name__ == "__main__":
    print("Composing Threshold Stand...")
    opera = OperaGenerator(seed=42)
    opera.compose()
    opera.save("Threshold_Stand.mid")
    print(f"Done: {len(opera.all_n)} notes")
