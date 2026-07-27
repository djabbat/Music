#!/usr/bin/env python3
"""
Ze Music Research Module — Batch Analysis, Cross-Validation, and Statistical Evaluation.

Дополнительный модуль для ze_music.py.
Добавляет функции для научной валидации Ze Score:
- batch_analyze: анализ всех MIDI в папке → CSV
- cross_validate: k-fold кросс-валидация Ze Score
- benchmark: сравнение с baseline-моделями
- statistical_tests: проверка гипотез H1–H3

Зависимости: ze_music.py, numpy, scipy, pandas (опционально)
"""

import os
import sys
import json
import math
import random
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

# Import from main module
try:
    from ze_music import (
        Note, ZeMusicAnalysis, ZeScore, compute_ze_score,
        load_midi, ZeStream, ZeEvent
    )
except ImportError:
    print("ERROR: ze_music.py not found in path.")
    print("Run from ~/Desktop/Marketing/Music/ or add to PYTHONPATH.")
    sys.exit(1)

# Try importing scientific libraries
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("WARNING: numpy not installed. Statistical functions limited.")

try:
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("WARNING: scipy not installed. Some tests unavailable.")


# ═══════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════

@dataclass
class TrackAnalysis:
    """Complete analysis of one track."""
    filepath: str
    track_name: str
    # Ze parameters
    v: float
    tau: float
    chi: float
    zeta: float
    autocorr_4: float
    autocorr_8: float
    # Ze Score
    ze_score: float
    ze_grade: str
    # Metadata
    n_notes: int
    n_events: int
    duration_sec: float = 0.0
    # External (to be filled from chart data)
    chart_position: Optional[int] = None
    chart_year: Optional[int] = None
    artist: str = ""
    # Ze channel breakdown
    v_pitch: float = 0.0
    v_rhythm: float = 0.0
    v_dynamics: float = 0.0
    v_harmony: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "track": self.track_name,
            "artist": self.artist,
            "v": round(self.v, 4),
            "tau": round(self.tau, 4),
            "chi": round(self.chi, 4),
            "zeta": round(self.zeta, 4),
            "C(4)": round(self.autocorr_4, 4),
            "C(8)": round(self.autocorr_8, 4),
            "ze_score": round(self.ze_score, 1),
            "ze_grade": self.ze_grade,
            "n_notes": self.n_notes,
            "n_events": self.n_events,
            "v_pitch": round(self.v_pitch, 4),
            "v_rhythm": round(self.v_rhythm, 4),
            "v_dynamics": round(self.v_dynamics, 4),
            "v_harmony": round(self.v_harmony, 4),
            "chart_position": self.chart_position,
            "chart_year": self.chart_year,
        }


@dataclass
class ValidationResult:
    """Results of a cross-validation run."""
    method: str
    spearman_rho: float
    pearson_r: float
    r_squared: float
    p_value: float
    mae: float  # Mean Absolute Error in chart position
    fold_scores: List[float] = field(default_factory=list)
    predictions: List[Tuple[float, float]] = field(default_factory=list)
    
    def summary(self) -> str:
        lines = [
            f"═══ Validation: {self.method} ═══",
            f"  Spearman ρ  = {self.spearman_rho:.4f}  (p = {self.p_value:.4f})",
            f"  Pearson r   = {self.pearson_r:.4f}",
            f"  R²          = {self.r_squared:.4f}",
            f"  MAE         = {self.mae:.1f} chart positions",
        ]
        if self.fold_scores:
            lines.append(f"  Fold ρ's    = {[f'{r:.3f}' for r in self.fold_scores]}")
            lines.append(f"  Mean ± SD   = {np.mean(self.fold_scores):.3f} ± {np.std(self.fold_scores):.3f}")
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# BATCH ANALYSIS
# ═══════════════════════════════════════════════════════════════

def batch_analyze(
    directory: str,
    pattern: str = "*.mid",
    recursive: bool = True,
    verbose: bool = True,
) -> List[TrackAnalysis]:
    """
    Анализирует все MIDI-файлы в директории.
    
    Args:
        directory: путь к папке с MIDI-файлами
        pattern: glob-паттерн (по умолчанию *.mid)
        recursive: рекурсивный обход подпапок
        verbose: печатать прогресс
    
    Returns:
        Список TrackAnalysis
    """
    results = []
    path = Path(directory)
    
    if recursive:
        files = list(path.rglob(pattern))
    else:
        files = list(path.glob(pattern))
    
    if not files:
        print(f"No files matching '{pattern}' in {directory}")
        return results
    
    print(f"Found {len(files)} MIDI files.")
    errors = 0
    
    for i, filepath in enumerate(files):
        try:
            if verbose:
                print(f"  [{i+1}/{len(files)}] {filepath.name}...", end=" ")
            
            notes = load_midi(str(filepath))
            analysis = ZeMusicAnalysis(name=filepath.stem)
            analysis.analyze(notes)
            zs = compute_ze_score(notes)
            
            # Calculate duration
            duration = notes[-1].start + notes[-1].duration if notes else 0.0
            
            ta = TrackAnalysis(
                filepath=str(filepath),
                track_name=filepath.stem,
                v=analysis.combined_stream.v,
                tau=analysis.combined_stream.tau,
                chi=analysis.combined_stream.chi,
                zeta=min(analysis.combined_stream.zeta, 20.0),
                autocorr_4=analysis.combined_stream.autocorrelation(4) if analysis.combined_stream.N > 4 else 0.0,
                autocorr_8=analysis.combined_stream.autocorrelation(8) if analysis.combined_stream.N > 8 else 0.0,
                ze_score=zs.score,
                ze_grade=zs.grade,
                n_notes=len(notes),
                n_events=analysis.combined_stream.N,
                duration_sec=duration,
                v_pitch=analysis.pitch_stream.v,
                v_rhythm=analysis.rhythm_stream.v,
                v_dynamics=analysis.dynamics_stream.v,
                v_harmony=analysis.harmony_stream.v,
            )
            results.append(ta)
            
            if verbose:
                print(f"v={ta.v:+.3f} τ={ta.tau:.3f} Score={ta.ze_score:.0f}")
                
        except Exception as e:
            errors += 1
            if verbose:
                print(f"ERROR: {e}")
    
    if verbose:
        print(f"\nDone: {len(results)} analysed, {errors} errors.")
    
    return results


def merge_chart_data(
    analyses: List[TrackAnalysis],
    chart_csv: str,
    name_column: str = "track",
    position_column: str = "peak_position",
    year_column: str = "year",
    artist_column: str = "artist",
) -> List[TrackAnalysis]:
    """
    Добавляет данные чартов к результатам анализа.
    
    Args:
        analyses: список TrackAnalysis
        chart_csv: путь к CSV с данными чартов
        name_column: название колонки с именем трека
        position_column: колонка с позицией в чарте
        year_column: колонка с годом
        artist_column: колонка с исполнителем
    
    Returns:
        Обновлённый список TrackAnalysis (in-place + return)
    """
    import csv
    
    with open(chart_csv, 'r') as f:
        reader = csv.DictReader(f)
        chart_data = {}
        for row in reader:
            key = row[name_column].strip().lower()
            chart_data[key] = row
    
    matched = 0
    for ta in analyses:
        key = ta.track_name.strip().lower()
        if key in chart_data:
            row = chart_data[key]
            try:
                ta.chart_position = int(row[position_column])
            except (ValueError, KeyError):
                ta.chart_position = None
            try:
                ta.chart_year = int(row[year_column])
            except (ValueError, KeyError):
                ta.chart_year = None
            ta.artist = row.get(artist_column, "")
            matched += 1
    
    print(f"Merged chart data: {matched}/{len(analyses)} tracks matched.")
    return analyses


# ═══════════════════════════════════════════════════════════════
# CROSS-VALIDATION
# ═══════════════════════════════════════════════════════════════

def zero_r_spearman(x, y):
    """Spearman correlation using only standard library (fallback)."""
    n = len(x)
    # Rank x
    x_ranks = _rankdata(x)
    y_ranks = _rankdata(y)
    # Pearson on ranks
    return _pearson_r(x_ranks, y_ranks)


def _rankdata(values):
    """Simple rank computation."""
    sorted_pairs = sorted(enumerate(values), key=lambda p: p[1])
    ranks = [0] * len(values)
    for rank, (idx, _) in enumerate(sorted_pairs, 1):
        ranks[idx] = rank
    return ranks


def _pearson_r(x, y):
    """Pearson correlation (pure Python)."""
    n = len(x)
    mx = sum(x) / n
    my = sum(y) / n
    sx = math.sqrt(sum((xi - mx) ** 2 for xi in x))
    sy = math.sqrt(sum((yi - my) ** 2 for yi in y))
    if sx == 0 or sy == 0:
        return 0.0
    return sum((xi - mx) * (yi - my) for xi, yi in zip(x, y)) / (sx * sy)


def cross_validate_ze_score(
    analyses: List[TrackAnalysis],
    k: int = 10,
    random_seed: int = 42,
) -> ValidationResult:
    """
    K-fold кросс-валидация Ze Score против позиций в чартах.
    
    Args:
        analyses: список TrackAnalysis с заполненными chart_position
        k: количество фолдов
        random_seed: зерно для воспроизводимости
    
    Returns:
        ValidationResult с метриками
    """
    # Фильтруем только треки с известной позицией в чарте
    valid = [a for a in analyses if a.chart_position is not None]
    
    if len(valid) < k * 2:
        print(f"WARNING: Only {len(valid)} tracks with chart data. Need at least {k*2} for {k}-fold CV.")
        if len(valid) < 5:
            return ValidationResult(
                method="Ze Score CV",
                spearman_rho=0.0, pearson_r=0.0, r_squared=0.0,
                p_value=1.0, mae=float('inf'),
            )
        k = max(2, len(valid) // 5)
        print(f"  Reducing to k={k} folds.")
    
    random.seed(random_seed)
    shuffled = valid.copy()
    random.shuffle(shuffled)
    
    fold_size = len(shuffled) // k
    all_predictions = []
    fold_rhos = []
    
    for fold in range(k):
        start = fold * fold_size
        end = start + fold_size if fold < k - 1 else len(shuffled)
        
        test = shuffled[start:end]
        train = shuffled[:start] + shuffled[end:]
        
        # "Калибровка" Ze Score на тренировочном наборе:
        # линейная регрессия ze_score → chart_position
        train_scores = [a.ze_score for a in train]
        train_positions = [a.chart_position for a in train]
        
        # Простая линейная регрессия (без numpy)
        n_train = len(train)
        mx = sum(train_scores) / n_train
        my = sum(train_positions) / n_train
        num = sum((x - mx) * (y - my) for x, y in zip(train_scores, train_positions))
        den = sum((x - mx) ** 2 for x in train_scores)
        
        if den == 0:
            slope = 0.0
            intercept = my
        else:
            slope = num / den
            intercept = my - slope * mx
        
        # Предсказания на тестовом наборе
        for a in test:
            predicted = intercept + slope * a.ze_score
            all_predictions.append((predicted, a.chart_position))
        
        # Spearman ρ для этого фолда
        test_preds = [intercept + slope * a.ze_score for a in test]
        test_actuals = [a.chart_position for a in test]
        
        if HAS_SCIPY:
            rho, pval = stats.spearmanr(test_preds, test_actuals)
        else:
            rho = zero_r_spearman(test_preds, test_actuals)
        
        fold_rhos.append(rho)
    
    # Общие метрики
    preds = [p[0] for p in all_predictions]
    actuals = [p[1] for p in all_predictions]
    
    if HAS_SCIPY:
        spearman_rho, spearman_p = stats.spearmanr(preds, actuals)
        pearson_r, pearson_p = stats.pearsonr(preds, actuals)
    else:
        spearman_rho = zero_r_spearman(preds, actuals)
        spearman_p = 1.0
        pearson_r = _pearson_r(preds, actuals)
    
    r_squared = pearson_r ** 2 if pearson_r else 0.0
    
    # MAE
    mae = sum(abs(p - a) for p, a in zip(preds, actuals)) / len(actuals) if actuals else float('inf')
    
    return ValidationResult(
        method=f"Ze Score — {k}-fold CV",
        spearman_rho=spearman_rho,
        pearson_r=pearson_r,
        r_squared=r_squared,
        p_value=spearman_p,
        mae=mae,
        fold_scores=fold_rhos,
        predictions=list(zip(preds, actuals)),
    )


def random_baseline(
    analyses: List[TrackAnalysis],
    k: int = 10,
    n_permutations: int = 100,
    seed: int = 42,
) -> ValidationResult:
    """
    Случайный baseline: перестановочный тест.
    
    Перемешивает chart_position случайно и вычисляет Spearman ρ.
    Повторяет n_permutations раз.
    """
    random.seed(seed)
    valid = [a for a in analyses if a.chart_position is not None]
    scores = [a.ze_score for a in valid]
    positions = [a.chart_position for a in valid]
    
    perm_rhos = []
    for _ in range(n_permutations):
        shuffled_pos = positions.copy()
        random.shuffle(shuffled_pos)
        
        if HAS_SCIPY:
            rho, _ = stats.spearmanr(scores, shuffled_pos)
        else:
            rho = zero_r_spearman(scores, shuffled_pos)
        
        perm_rhos.append(rho)
    
    mean_rho = sum(perm_rhos) / len(perm_rhos)
    std_rho = math.sqrt(sum((r - mean_rho) ** 2 for r in perm_rhos) / len(perm_rhos))
    
    return ValidationResult(
        method=f"Random baseline ({n_permutations} permutations)",
        spearman_rho=mean_rho,
        pearson_r=mean_rho,
        r_squared=mean_rho ** 2,
        p_value=1.0,
        mae=float('inf'),
        fold_scores=[mean_rho, mean_rho - std_rho, mean_rho + std_rho],
    )


# ═══════════════════════════════════════════════════════════════
# HYPOTHESIS TESTING FRAMEWORK
# ═══════════════════════════════════════════════════════════════

def test_h1_v_pleasure(
    v_values: List[float],
    pleasure_ratings: List[float],
) -> dict:
    """
    H1: Inverted-U relationship between v and pleasure.
    
    Tests quadratic model: pleasure ~ v + v² + (1|participant)
    """
    if not HAS_SCIPY:
        return {"error": "scipy required for hypothesis testing"}
    
    v = np.array(v_values)
    p = np.array(pleasure_ratings)
    
    # Quadratic regression
    # pleasure = β₀ + β₁·v + β₂·v² + ε
    X = np.column_stack([np.ones_like(v), v, v**2])
    
    try:
        # OLS: β = (X'X)⁻¹X'y
        beta = np.linalg.inv(X.T @ X) @ X.T @ p
        residuals = p - X @ beta
        
        n = len(v)
        k = 3  # parameters
        sigma_sq = (residuals @ residuals) / (n - k)
        var_beta = sigma_sq * np.linalg.inv(X.T @ X)
        se_beta = np.sqrt(np.diag(var_beta))
        
        # t-test for β₂ (quadratic term)
        t_stat = beta[2] / se_beta[2]
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - k))
        
        # R²
        ss_res = residuals @ residuals
        ss_tot = sum((pi - np.mean(p)) ** 2 for pi in p)
        r_squared = 1 - ss_res / ss_tot
        
        # Find peak v
        if beta[2] < 0:  # inverted-U confirmed
            v_peak = -beta[1] / (2 * beta[2])
        else:
            v_peak = None
        
        return {
            "hypothesis": "H1: v-Pleasure inverted-U",
            "beta_0": float(beta[0]),
            "beta_1": float(beta[1]),
            "beta_2": float(beta[2]),
            "se_beta_2": float(se_beta[2]),
            "t_stat_quadratic": float(t_stat),
            "p_value_quadratic": float(p_value),
            "r_squared": float(r_squared),
            "v_peak": float(v_peak) if v_peak else None,
            "inverted_u_confirmed": beta[2] < 0 and p_value < 0.05,
            "n_observations": n,
        }
    except np.linalg.LinAlgError:
        return {"error": "Singular matrix — check data"}


def test_h2_tau_engagement(
    tau_values: List[float],
    engagement_scores: List[float],
) -> dict:
    """H2: Inverted-U between τ and engagement."""
    return test_h1_v_pleasure(tau_values, engagement_scores)


def test_h3_ze_vs_baseline(
    ze_rho: float,
    baseline_rhos: List[float],
) -> dict:
    """
    H3: Ze Score significantly outperforms random baseline.
    
    One-sample t-test: is ze_rho > mean(baseline_rhos)?
    """
    if not HAS_SCIPY:
        return {"error": "scipy required"}
    
    t_stat, p_value = stats.ttest_1samp(baseline_rhos, ze_rho)
    
    mean_baseline = np.mean(baseline_rhos)
    std_baseline = np.std(baseline_rhos, ddof=1)
    
    # Effect size (Cohen's d)
    d = (ze_rho - mean_baseline) / std_baseline if std_baseline > 0 else 0.0
    
    return {
        "hypothesis": "H3: Ze Score > random baseline",
        "ze_spearman_rho": ze_rho,
        "baseline_mean_rho": float(mean_baseline),
        "baseline_std_rho": float(std_baseline),
        "t_statistic": float(t_stat),
        "p_value": float(p_value),
        "cohens_d": float(d),
        "significant": p_value < 0.05,
        "n_permutations": len(baseline_rhos),
    }


# ═══════════════════════════════════════════════════════════════
# EXPORT FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def export_to_csv(analyses: List[TrackAnalysis], output_path: str):
    """Экспорт результатов анализа в CSV."""
    import csv
    
    with open(output_path, 'w', newline='') as f:
        if not analyses:
            return
        
        fields = list(analyses[0].to_dict().keys())
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for a in analyses:
            writer.writerow(a.to_dict())
    
    print(f"Exported {len(analyses)} tracks to {output_path}")


def export_to_json(analyses: List[TrackAnalysis], output_path: str):
    """Экспорт результатов анализа в JSON."""
    with open(output_path, 'w') as f:
        json.dump([a.to_dict() for a in analyses], f, indent=2)
    
    print(f"Exported {len(analyses)} tracks to {output_path}")


def summary_statistics(analyses: List[TrackAnalysis]) -> str:
    """Описательная статистика по набору анализов."""
    if not analyses:
        return "No data."
    
    def _stats(values, name):
        if not HAS_NUMPY:
            m = sum(values) / len(values)
            sd = math.sqrt(sum((x - m) ** 2 for x in values) / len(values))
            return f"  {name:<12} mean={m:8.4f}  std={sd:8.4f}  min={min(values):8.4f}  max={max(values):8.4f}"
        arr = np.array(values)
        return f"  {name:<12} mean={np.mean(arr):8.4f}  std={np.std(arr):8.4f}  min={np.min(arr):8.4f}  max={np.max(arr):8.4f}"
    
    lines = [
        f"═══ Summary Statistics (N={len(analyses)}) ═══",
        _stats([a.v for a in analyses], "v"),
        _stats([a.tau for a in analyses], "tau"),
        _stats([a.chi for a in analyses], "chi"),
        _stats([a.zeta for a in analyses if a.zeta < 100], "zeta"),
        _stats([a.autocorr_4 for a in analyses], "C(4)"),
        _stats([a.autocorr_8 for a in analyses], "C(8)"),
        _stats([a.ze_score for a in analyses], "Ze Score"),
        "",
        f"  Grade distribution:",
    ]
    
    grades = defaultdict(int)
    for a in analyses:
        grades[a.ze_grade] += 1
    for grade, count in sorted(grades.items()):
        pct = 100 * count / len(analyses)
        lines.append(f"    {grade}: {count} ({pct:.1f}%)")
    
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print("Ze Music Research CLI")
        print()
        print("Commands:")
        print("  batch <directory> [pattern] [--csv output.csv]")
        print("  validate <directory> <chart_data.csv> [--k 10]")
        print("  stats <directory>")
        print("  export <directory> --csv output.csv")
        print("  export <directory> --json output.json")
        return
    
    cmd = sys.argv[1]
    
    if cmd == "batch":
        directory = sys.argv[2] if len(sys.argv) > 2 else "."
        pattern = "*.mid"
        output_csv = None
        
        args = sys.argv[3:]
        i = 0
        while i < len(args):
            if args[i] == "--csv" and i + 1 < len(args):
                output_csv = args[i + 1]
                i += 2
            elif not args[i].startswith("--"):
                pattern = args[i]
                i += 1
            else:
                i += 1
        
        results = batch_analyze(directory, pattern)
        
        if results:
            print()
            print(summary_statistics(results))
            
            if output_csv:
                export_to_csv(results, output_csv)
    
    elif cmd == "stats":
        directory = sys.argv[2] if len(sys.argv) > 2 else "."
        results = batch_analyze(directory, verbose=False)
        
        if results:
            print(summary_statistics(results))
    
    elif cmd == "validate":
        if len(sys.argv) < 4:
            print("Usage: validate <directory> <chart_data.csv> [--k 10]")
            return
        
        directory = sys.argv[2]
        chart_csv = sys.argv[3]
        k = 10
        
        if "--k" in sys.argv:
            k_idx = sys.argv.index("--k")
            if k_idx + 1 < len(sys.argv):
                k = int(sys.argv[k_idx + 1])
        
        print("Step 1: Analysing MIDI files...")
        results = batch_analyze(directory, verbose=False)
        
        print(f"\nStep 2: Merging chart data from {chart_csv}...")
        results = merge_chart_data(results, chart_csv)
        
        print(f"\nStep 3: Cross-validation (k={k})...")
        cv_result = cross_validate_ze_score(results, k=k)
        print()
        print(cv_result.summary())
        
        print(f"\nStep 4: Random baseline...")
        baseline = random_baseline(results, k=k)
        print(f"  Mean random ρ = {baseline.spearman_rho:.4f} ± {baseline.fold_scores[2] - baseline.spearman_rho:.4f}")
        
        if HAS_SCIPY:
            print(f"\nStep 5: H3 test (Ze vs. random)...")
            h3 = test_h3_ze_vs_baseline(cv_result.spearman_rho, baseline.fold_scores)
            for k, v in h3.items():
                print(f"  {k}: {v}")
    
    elif cmd == "export":
        if len(sys.argv) < 3:
            print("Usage: export <directory> --csv output.csv | --json output.json")
            return
        
        directory = sys.argv[2]
        results = batch_analyze(directory, verbose=False)
        
        if "--csv" in sys.argv:
            csv_idx = sys.argv.index("--csv")
            if csv_idx + 1 < len(sys.argv):
                export_to_csv(results, sys.argv[csv_idx + 1])
        elif "--json" in sys.argv:
            json_idx = sys.argv.index("--json")
            if json_idx + 1 < len(sys.argv):
                export_to_json(results, sys.argv[json_idx + 1])
        else:
            print("Specify --csv or --json output file.")
    
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
