# Ze Music — Mathematical Music Composition and Analysis

A formal framework for composing and analyzing music through information theory, group theory, and dynamical systems. Built on the Ze Vectors Theory (Tqemaladze, 2026).

## What This Is

Ze-MIM (Ze Musical Impact Model) parametrizes music as a binary stream of Tension (T) and Stretch (S) events across four independent channels: pitch, rhythm, dynamics, and harmony. From this stream, five scalar parameters are derived — v (velocity), τ (complexity), χ (variability), ζ (impedance), and C(k) (autocorrelation). These map onto well-established constructs in the neuroscience of music perception.

The framework supports two directions:
- **Analysis:** MIDI → Ze parameters → hit potential score
- **Synthesis:** Ze parameters → MIDI → audio

## Included Operas

### Threshold Stand (28 minutes, 3 acts)
A concept opera composed entirely through the Ze state machine. Eight compositional states drive the narrative across three acts, synthesizing Georgian polyphony, Bach counterpoint, Mozart form, Orff ostinato, and rock idioms.

### Samnu Azuzi — The Gilgamesh Triad (14 minutes)
Three arias for the central figures of the Epic of Gilgamesh: the king (baritone), Enkidu (tenor), and Ishtar (soprano). Uses reconstructed ancient Mesopotamian modes through Georgian folk scales — Gurian, Svan, and a custom chromatic mode for Ishtar's fury. Full symphonic orchestration with solo voice.

## Project Structure

```
Music/
├── CONCEPT.md              Scientific framework (v5.0)
├── THEORY.md               Mathematical foundations
├── PARAMETERS.md           Ze parameters and composer profiles
├── REFERENCES.md           Verified sources (15 refs, PMID/DOI)
│
├── ze_music.py             Core engine — analysis, generation, scoring
├── ze_research.py          Batch analysis, cross-validation, statistics
├── ze_audio.py             Audio-to-Ze extraction pipeline (librosa)
├── ze_statistics.py        Power analysis, baseline comparison
├── ze_visualise.py         Scientific visualization (5 plot types)
│
├── Threshold_Stand/        Opera: concept, score, MIDI, WAV
├── Samnu_Azuzi/            Gilgamesh triad: arias, MIDI, WAV
│
├── data/midi/              Generated MIDI library
│   ├── bach/               8 works (BWV 846–1080)
│   ├── mozart/             8 works (K.331–622)
│   ├── orff/               7 works (Carmina Burana)
│   ├── rock/               24 tracks (Lou Reed, Led Zeppelin, Bowie)
│   ├── georgian/           93 tracks (19 regions, 22 scales)
│   ├── pophits/            20 tracks
│   └── opera/              Opera MIDI files
│
└── data/results/           CSV analysis, plots, composition matrix
```

## Georgian Folk Music

93 tracks across 19 historical Georgian regions, each with its own scale and polyphonic style: Guria, Kartli, Imereti, Svaneti, Khevsureti, Megrelia, Racha, Tusheti, Adjara, Meskheti, Abkhazia, Mtiuleti, Javakheti, Kakheti, Ossetia, Lechkhumi, Pshavi, Khevi, Hereti, Tao-Klarjeti, and Fereydan.

Georgian polyphony (UNESCO Intangible Heritage) consistently produces the highest Ze Scores — a finding that warrants further ethnomusicological investigation.

## Quick Start

```bash
pip install mido numpy scipy matplotlib librosa

# Analyze a MIDI file
python3 ze_music.py analyze file.mid

# Generate a superhit
python3 ze_music.py superhit C major 120 output.mid

# Batch analyze all MIDIs in a folder
python3 ze_research.py batch data/midi/georgian --csv results.csv

# Visualize results
python3 ze_visualise.py data/results/synthetic_analysis.csv
```

## Dependencies

- Python 3.8+
- mido (MIDI I/O)
- numpy, scipy (computation)
- matplotlib (visualization)
- librosa (audio extraction)

## License

Apache 2.0 — see LICENSE file.

## Author

Jaba Tqemaladze, MD  
Georgia Longevity Alliance  
jaba@longevity.ge

---
*Ze Vectors Theory: 13 axioms. v* = 1 − ln 2 ≈ 0.30685.*
