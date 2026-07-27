# Music — PARAMETERS

**Version:** 2.0 (post autofix Cycle 1)
**Date:** 2026-07-27

---

## Ze Scalar Parameters

| Parameter | Formula | Range | Critical Value(s) | Neuroscientific Mapping |
|-----------|---------|-------|-------------------|------------------------|
| **v** (velocity) | (N_T − N_S) / N | [−1, +1] | v* = 1 − ln 2 ≈ **0.30685** (max τ); v_impact ≈ **0.35–0.50** (hypothesised max pleasure) | Balance of prediction violation vs. confirmation events (Vuust & Witek, 2014; Gold et al., 2019) |
| **τ** (complexity) | H(Z) / log₂(N) | [0, 1] | τ_flow ≈ **0.25–0.50** (hypothesised optimal engagement) | Information content / predictive complexity (Gold et al., 2019) |
| **Z** (index) | N_T / N | [0, 1] | Z* = (1+v*)/2 ≈ **0.6534** | Proportion of T-events |
| **χ** (variability) | (max−min)/mean of sliding Z | [0, ∞) | χ_impact ≈ **0.50–0.90** (emotional dynamic range) | Amplitude of T/S oscillation; emotional contrast |
| **ζ** (impedance) | τ / \|v\| | [0, ∞] | ζ_groove ≈ **5–15** (stable, hypnotic) | Resistance to change; groove stability (Matthews et al., 2020) |
| **C(k)** (autocorrelation) | ⟨Z(t), Z(t+k)⟩ | [−1, +1] | C(4) > 0.5 → earworm potential | Motivic repetition; earworm formation (Jakubowski et al., 2017) |

## Composer Profiles (Theoretical)

| Parameter | Bach | Mozart | Orff | Superhit (4th Path) |
|-----------|------|--------|------|---------------------|
| **v_target** | 0.00 (balanced via Z₂) | 0.20 (T-bias) | 0.00 (balanced via periodicity) | 0.40 (T-dominant impact zone) |
| **τ_target** | 0.85 (max complexity) | 0.55 (φ-modulated) | 0.25 (fixed by ostinato period) | 0.45 (flow window centre) |
| **χ_target** | 0.40 (moderate) | 0.25 (low — elegant) | 0.95 (extreme — ritual) | 0.70 (emotional oscillation) |
| **ζ** | 0.15 (frequent change) | 2.25 (structured change) | 12.5 (stable — trance) | 0.40 (flexible) |
| **Voices** | 4 | 1 | 1 | 1–4 |
| **Form** | Fugue (group orbit) | Sonata (closed cycle) | Ostinato (limit cycle) | Pop song (T→S→T cycle) |
| **Group structure** | Z₂ × D₄ × ℝ⁺ | S¹ (topological circle) | ℤ_p (cyclic) | All three |
| **Attractor type** | High-τ chaotic | Quasi-periodic (KAM) | Limit cycle + chaotic dynamics | Hyper-cycle |
| **Primary maximand** | τ (complexity) | C(k) (self-similarity) | χ (amplitude) | Pleasure (v, τ, χ balanced) |

## Structural Parameters

| Parameter | Value | Note |
|-----------|-------|------|
| Ze channels | 4 (pitch, rhythm, dynamics, harmony) | Combined via majority vote |
| Standard hook length | 4–8 events | C(4) > 0.5 for earworm |
| Standard ostinato period | 8 events | Orff archetype |
| Standard pop song structure | 120 bars × 4 events/bar = 480 events | Intro→Verse→Pre→Chorus×3→Bridge→Outro |
| φ (golden ratio) | 1.618033989 | Mozart structural proportions |
| v* (exact) | 0.306852819 | From Axiom 7, Ze Vectors Theory |
| Z* (exact) | 0.653426410 | (1 + v*)/2 |

## Ze Score — Weights and Thresholds

### Current Weights (heuristic — require empirical calibration)

| Component | Max Points | Condition |
|-----------|-----------|-----------|
| v in impact zone (0.30–0.55) | 30 | Triangular weighting, peak at v = 0.425 |
| τ in flow window (0.20–0.55) | 25 | Triangular weighting, peak at τ = 0.375 |
| χ for emotional contrast (0.35–0.95) | 20 | Triangular weighting, peak at χ = 0.70 |
| T→S→T chorus cycle present | 15 | Binary: has structural cycle or not |
| Hook autocorrelation C(4) > 0.4 | 10 | Proportional to C(4), max 10 |

### Grade Thresholds

| Range | Grade | Interpretation |
|-------|-------|----------------|
| 90–100 | ★★★★★ | Hypothesised guaranteed hit (requires validation) |
| 75–89 | ★★★★ | Very high potential |
| 60–74 | ★★★ | Good potential |
| 40–59 | ★★ | Average |
| 20–39 | ★ | Low |
| 0–19 | ☆ | Not a hit |

## Validation Parameters (H1–H3)

| Parameter | H1 (v-Pleasure) | H2 (τ-Engagement) | H3 (Ze Score vs. Charts) |
|-----------|-----------------|-------------------|-------------------------|
| N participants | ≥ 200 | ≥ 150 | — |
| N stimuli | 100 synthetic excerpts | 60 excerpts (6 τ × 5 genres) | N_train=500, N_test=200 |
| Primary outcome | Pleasure rating (1–9 Likert) | Dwell time + arousal rating | Peak chart position |
| Statistical test | Mixed-effects quadratic regression | Mixed-effects quadratic regression | Spearman ρ, 10-fold CV |
| Null hypothesis | No quadratic relationship | Engagement monotonic in τ | ρ ≤ 0.10 (chance baseline) |
| Preregistration | OSF | OSF | OSF |
| Target journal | Music Perception / J Neurosci | Music Perception / Cognition | Royal Society Open Science |

## Product Parameters (Post-Validation)

| Product | Price | Target Market | Market Size (Est.) |
|---------|-------|---------------|-------------------|
| Ze Pop | $19/mo | Music producers, beatmakers | ~$800M |
| Ze Hook | $9/mo | Composers, sound designers | ~$300M |
| Ze Groove | $9/mo | Electronic musicians, drummers | ~$200M |
| Ze Pro | $79/mo | Studios, labels | ~$500M |
| Ze Hit Analyzer | $299/report | A&R, record labels | ~$300M |

---

*Linked to: `~/Desktop/LC/Ze/PARAMETERS.md`, `~/Desktop/LC/Ze/Ze_Music/`*
