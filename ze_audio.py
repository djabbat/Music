#!/usr/bin/env python3
"""
Ze Audio — Audio-to-Ze extraction pipeline.
Извлекает Ze-параметры из аудиофайлов (WAV/MP3) через базовый pitch tracking.
Использует librosa для анализа и сопоставляет с Ze-каналами.

Зависимости: pip install librosa numpy scipy
"""

import os, sys, math
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False

# Import Ze core
try:
    from ze_music import Note, ZeMusicAnalysis, ZeScore, compute_ze_score, ZeStream, ZeEvent
except ImportError:
    print("ERROR: ze_music.py not found.")


@dataclass
class AudioZeResult:
    """Результат Ze-анализа аудиофайла."""
    filepath: str
    duration_sec: float
    sample_rate: int
    # Extracted notes
    notes: List  # List[Note]
    n_notes: int
    # Ze analysis
    v: float
    tau: float
    chi: float
    zeta: float
    autocorr_4: float
    ze_score: float
    # Audio features (for baseline comparison)
    tempo_bpm: float
    rms_energy: float
    spectral_centroid: float
    spectral_bandwidth: float
    zero_crossing_rate: float
    mfcc_mean: List[float]
    
    def to_dict(self) -> dict:
        return {
            "file": os.path.basename(self.filepath),
            "duration": round(self.duration_sec, 2),
            "n_notes": self.n_notes,
            "v": round(self.v, 4),
            "tau": round(self.tau, 4),
            "chi": round(self.chi, 4),
            "zeta": round(self.zeta, 4),
            "C(4)": round(self.autocorr_4, 4),
            "ze_score": round(self.ze_score, 1),
            "tempo_bpm": round(self.tempo_bpm, 1),
            "rms_energy": round(self.rms_energy, 4),
            "spectral_centroid": round(self.spectral_centroid, 1),
            "spectral_bandwidth": round(self.spectral_bandwidth, 1),
            "zcr": round(self.zero_crossing_rate, 4),
        }


def extract_pitch_contour(audio_path: str, hop_length: int = 512, fmin: float = 65.0, fmax: float = 2093.0) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Извлекает pitch contour из аудио через librosa.pyin (вероятностный YIN).
    
    Returns:
        times: массив времени (сек)
        pitches_hz: массив частот (Hz, NaN = unvoiced)
        sr: sample rate
    """
    if not HAS_LIBROSA:
        raise ImportError("librosa required: pip install librosa")
    
    y, sr = librosa.load(audio_path, sr=None, mono=True)
    
    # PYIN pitch tracking (state-of-the-art for monophonic)
    f0, voiced_flag, voiced_probs = librosa.pyin(
        y, fmin=fmin, fmax=fmax, sr=sr,
        hop_length=hop_length, fill_na=np.nan
    )
    
    times = librosa.frames_to_time(np.arange(len(f0)), sr=sr, hop_length=hop_length)
    
    return times, f0, sr


def hz_to_midi(hz: float) -> int:
    """Конвертирует Hz в MIDI номер ноты."""
    if np.isnan(hz) or hz <= 0:
        return -1
    return int(round(12 * math.log2(hz / 440.0) + 69))


def extract_rms_energy(audio_path: str) -> Tuple[float, float]:
    """Извлекает RMS энергию и её вариацию."""
    if not HAS_LIBROSA: return 0.0, 0.0
    y, sr = librosa.load(audio_path, sr=None, mono=True)
    rms = librosa.feature.rms(y=y)[0]
    return float(np.mean(rms)), float(np.std(rms))


def extract_tempo(audio_path: str) -> float:
    """Извлекает темп (BPM)."""
    if not HAS_LIBROSA: return 120.0
    y, sr = librosa.load(audio_path, sr=None, mono=True)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
    return float(tempo)


def extract_spectral_features(audio_path: str) -> dict:
    """Извлекает спектральные признаки (baseline comparison)."""
    if not HAS_LIBROSA:
        return {"centroid": 0, "bandwidth": 0, "zcr": 0, "mfcc": []}
    
    y, sr = librosa.load(audio_path, sr=None, mono=True)
    
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
    zcr = librosa.feature.zero_crossing_rate(y)[0]
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    
    return {
        "centroid": float(np.mean(centroid)),
        "bandwidth": float(np.mean(bandwidth)),
        "zcr": float(np.mean(zcr)),
        "mfcc": [float(np.mean(mfcc[i])) for i in range(13)],
    }


def audio_to_notes(audio_path: str, hop_length: int = 512, min_note_dur: float = 0.05) -> List:
    """
    Конвертирует аудио в список Note через pitch tracking.
    
    Алгоритм:
    1. PYIN pitch tracking → частоты
    2. Конвертация Hz → MIDI
    3. Детекция нот: группировка последовательных одинаковых MIDI
    4. Оценка velocity через RMS
    """
    if not HAS_LIBROSA or not HAS_NUMPY:
        print("WARNING: librosa/numpy required for audio extraction.")
        return []
    
    times, pitches_hz, sr = extract_pitch_contour(audio_path, hop_length=hop_length)
    
    # Get RMS for velocity estimation
    y, _ = librosa.load(audio_path, sr=sr, mono=True)
    rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
    
    # Hz → MIDI
    midi_pitches = np.array([hz_to_midi(p) for p in pitches_hz])
    
    # Detect notes: merge consecutive identical MIDI pitches
    notes = []
    current_pitch = -1
    current_start = 0.0
    note_samples = 0
    
    for i in range(len(midi_pitches)):
        p = midi_pitches[i]
        t = times[i]
        
        if p < 0:  # unvoiced
            if current_pitch >= 0:
                # End current note
                dur = t - current_start
                if dur >= min_note_dur:
                    vel = int(min(127, max(20, rms[min(i, len(rms)-1)] * 2000)))
                    notes.append(Note(pitch=current_pitch, start=current_start, duration=dur, velocity=vel))
                current_pitch = -1
        elif p != current_pitch:
            if current_pitch >= 0:
                dur = t - current_start
                if dur >= min_note_dur:
                    vel = int(min(127, max(20, rms[min(i, len(rms)-1)] * 2000)))
                    notes.append(Note(pitch=current_pitch, start=current_start, duration=dur, velocity=vel))
            current_pitch = p
            current_start = t
    
    # Last note
    if current_pitch >= 0:
        dur = times[-1] - current_start
        if dur >= min_note_dur:
            notes.append(Note(pitch=current_pitch, start=current_start, duration=dur, velocity=80))
    
    return notes


def analyze_audio(audio_path: str) -> Optional[AudioZeResult]:
    """
    Полный Ze-анализ аудиофайла: pitch → MIDI notes → Ze параметры.
    """
    if not os.path.exists(audio_path):
        print(f"File not found: {audio_path}")
        return None
    
    # Extract features
    notes = audio_to_notes(audio_path)
    
    if len(notes) < 4:
        print(f"WARNING: Only {len(notes)} notes extracted from {audio_path}")
        return None
    
    # Ze analysis
    analysis = ZeMusicAnalysis(name=os.path.basename(audio_path))
    analysis.analyze(notes)
    zs = compute_ze_score(notes)
    
    # Audio features
    try:
        tempo = extract_tempo(audio_path)
        rms_mean, rms_std = extract_rms_energy(audio_path)
        spec = extract_spectral_features(audio_path)
    except:
        tempo = 120.0; rms_mean = 0.0; rms_std = 0.0
        spec = {"centroid": 0, "bandwidth": 0, "zcr": 0, "mfcc": []}
    
    # Duration
    y, sr = librosa.load(audio_path, sr=None, mono=True)
    duration = len(y) / sr
    
    return AudioZeResult(
        filepath=audio_path,
        duration_sec=duration,
        sample_rate=sr,
        notes=notes,
        n_notes=len(notes),
        v=analysis.combined_stream.v,
        tau=analysis.combined_stream.tau,
        chi=analysis.combined_stream.chi,
        zeta=min(analysis.combined_stream.zeta, 20.0),
        autocorr_4=analysis.combined_stream.autocorrelation(4) if analysis.combined_stream.N > 4 else 0.0,
        ze_score=zs.score,
        tempo_bpm=tempo,
        rms_energy=rms_mean,
        spectral_centroid=spec["centroid"],
        spectral_bandwidth=spec["bandwidth"],
        zero_crossing_rate=spec["zcr"],
        mfcc_mean=spec.get("mfcc", []),
    )


# ═══════════════════════════════════════════════════════
# AUDIO → ZE BATCH
# ═══════════════════════════════════════════════════════

def batch_audio_to_ze(directory: str, pattern: str = "*.wav") -> List[AudioZeResult]:
    """Пакетный анализ аудиофайлов."""
    results = []
    files = list(Path(directory).rglob(pattern))
    
    if not files:
        print(f"No files matching '{pattern}' in {directory}")
        return results
    
    print(f"Found {len(files)} audio files.")
    
    for i, fp in enumerate(files):
        try:
            print(f"  [{i+1}/{len(files)}] {fp.name}...", end=" ")
            r = analyze_audio(str(fp))
            if r:
                results.append(r)
                print(f"v={r.v:+.3f} τ={r.tau:.3f} Score={r.ze_score:.0f}")
            else:
                print("SKIP (too few notes)")
        except Exception as e:
            print(f"ERROR: {e}")
    
    return results


# ═══════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Ze Audio CLI")
        print("  analyze <audio_file>     — analyze single audio file")
        print("  batch <directory>        — batch analyze all WAV files")
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "analyze" and len(sys.argv) > 2:
        path = sys.argv[2]
        r = analyze_audio(path)
        if r:
            d = r.to_dict()
            for k, v in d.items():
                print(f"  {k:<20} {v}")
    
    elif cmd == "batch" and len(sys.argv) > 2:
        results = batch_audio_to_ze(sys.argv[2])
        print(f"\nDone: {len(results)} files analysed.")
