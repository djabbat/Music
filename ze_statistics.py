#!/usr/bin/env python3
"""
Ze Statistics — Statistical Power Analysis & Baseline Comparison Framework.
Содержит:
  1. Power analysis для H1–H3
  2. Baseline comparison framework (MFCC, Spotify, random)
  3. Effect size calculations
  4. Sample size justification
"""

import math
import sys
from typing import List, Tuple, Dict

try:
    import numpy as np
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("WARNING: scipy required for advanced stats.")


# ═══════════════════════════════════════════════════════
# POWER ANALYSIS
# ═══════════════════════════════════════════════════════

def power_analysis_h1(effect_size_f2: float = 0.10, alpha: float = 0.05, power: float = 0.80, n_predictors: int = 2) -> dict:
    """
    H1: Inverted-U v → pleasure (quadratic regression).
    
    Required N for detecting f² effect size in multiple regression.
    
    Args:
        effect_size_f2: Cohen's f² (0.02=small, 0.15=medium, 0.35=large)
        alpha: significance level
        power: desired power
        n_predictors: number of predictors (v + v² = 2)
    
    Returns:
        dict with required N and justification
    """
    # For regression: N = (λ / f²) + k, where λ from non-central F
    # Approximation using Cohen's method:
    # λ = f² × N, and λ needed for given alpha, power, df
    
    # Using inverse power calculation
    if HAS_SCIPY:
        from scipy.stats import ncf, f as f_dist
        
        # Binary search for N
        def power_for_n(n, f2, alpha, k):
            df1 = k
            df2 = n - k - 1
            lambda_ = f2 * n
            f_crit = f_dist.ppf(1 - alpha, df1, df2)
            return 1 - ncf.cdf(f_crit, df1, df2, lambda_)
        
        # Binary search
        lo, hi = 10, 5000
        for _ in range(50):
            mid = (lo + hi) / 2
            if power_for_n(mid, effect_size_f2, alpha, n_predictors) < power:
                lo = mid
            else:
                hi = mid
        
        n_required = int(math.ceil(hi))
    else:
        # Conservative estimate based on Cohen's tables
        if effect_size_f2 <= 0.02:  # small
            n_required = 485
        elif effect_size_f2 <= 0.15:  # medium
            n_required = 68
        else:  # large
            n_required = 31
    
    return {
        "hypothesis": "H1: v → pleasure (quadratic)",
        "effect_size_f2": effect_size_f2,
        "effect_size_label": "small" if effect_size_f2 <= 0.02 else ("medium" if effect_size_f2 <= 0.15 else "large"),
        "alpha": alpha,
        "power": power,
        "n_required": n_required,
        "n_recommended": max(200, n_required + 50),  # with buffer
        "justification": f"Based on Gold et al. (2019) who found inverted-U with strong quadratic effects. "
                        f"Assuming f² = {effect_size_f2} ({'small' if effect_size_f2<=0.02 else 'medium' if effect_size_f2<=0.15 else 'large'}), "
                        f"N ≥ {n_required} provides {power*100:.0f}% power at α = {alpha}.",
    }


def power_analysis_h2(effect_size_f2: float = 0.08, alpha: float = 0.05, power: float = 0.80, n_predictors: int = 8) -> dict:
    """
    H2: τ → engagement (quadratic model with genre controls).
    
    N predictors: τ + τ² + 5 genre dummies + 1 intercept = 8
    """
    if HAS_SCIPY:
        from scipy.stats import ncf, f as f_dist
        def power_for_n(n, f2, alpha, k):
            df1, df2 = k, n - k - 1
            lam = f2 * n
            f_crit = f_dist.ppf(1 - alpha, df1, df2)
            return 1 - ncf.cdf(f_crit, df1, df2, lam)
        lo, hi = 10, 5000
        for _ in range(50):
            mid = (lo + hi) / 2
            if power_for_n(mid, effect_size_f2, alpha, n_predictors) < power:
                lo = mid
            else:
                hi = mid
        n_required = int(math.ceil(hi))
    else:
        n_required = 250 if effect_size_f2 <= 0.15 else 80
    
    return {
        "hypothesis": "H2: τ → engagement (quadratic + genre controls)",
        "effect_size_f2": effect_size_f2,
        "alpha": alpha,
        "power": power,
        "n_predictors": n_predictors,
        "n_required": n_required,
        "n_recommended": max(150, n_required + 30),
        "justification": f"Gold et al. (2019) found medium effect for information content → pleasure. "
                        f"6 τ levels × 5 genres × {n_required//30} per cell. "
                        f"N ≥ {n_required} for {power*100:.0f}% power.",
    }


def power_analysis_h3(expected_rho: float = 0.25, null_rho: float = 0.05, 
                      alpha: float = 0.05, power: float = 0.80) -> dict:
    """
    H3: Ze Score → chart position (Spearman correlation).
    
    Power for detecting ρ > ρ₀ (one-sided).
    """
    # Fisher z-transformation
    z_expected = 0.5 * math.log((1 + expected_rho) / (1 - expected_rho))
    z_null = 0.5 * math.log((1 + null_rho) / (1 - null_rho))
    
    # Required N: N = ((z_α + z_β) / (z_expected - z_null))² + 3
    if HAS_SCIPY:
        z_alpha = stats.norm.ppf(1 - alpha)
        z_beta = stats.norm.ppf(power)
    else:
        z_alpha = 1.645  # α = 0.05 one-sided
        z_beta = 0.842   # power = 0.80
    
    n_required = int(math.ceil(((z_alpha + z_beta) / (z_expected - z_null))**2 + 3))
    
    return {
        "hypothesis": "H3: Ze Score → chart position",
        "expected_rho": expected_rho,
        "null_rho": null_rho,
        "alpha": alpha,
        "power": power,
        "n_required": n_required,
        "n_recommended": max(200, n_required + 50),
        "justification": f"Interiano et al. (2018) found ρ ≈ 0.10 for acoustic features → chart. "
                        f"Detecting ρ = {expected_rho} vs ρ₀ = {null_rho} requires N ≥ {n_required} "
                        f"tracks for {power*100:.0f}% power (one-sided).",
    }


# ═══════════════════════════════════════════════════════
# BASELINE COMPARISON FRAMEWORK
# ═══════════════════════════════════════════════════════

class BaselineComparator:
    """
    Framework for comparing Ze-MIM against standard baselines.
    
    Baselines:
    1. Random — permutation test
    2. Acoustic features — MFCC-13 + spectral centroid + bandwidth + ZCR + RMS
    3. Spotify features — danceability, energy, valence, tempo, acousticness, etc.
    4. Ze-MIM — v, τ, χ, ζ, C(4), Ze Score
    """
    
    def __init__(self):
        self.results = {}
    
    def compare_methods(self, ze_predictions: List[float], 
                        chart_positions: List[float],
                        method_name: str = "Ze-MIM") -> dict:
        """Compare one method's predictions against chart positions."""
        if not HAS_SCIPY:
            return {"error": "scipy required"}
        
        spearman_r, spearman_p = stats.spearmanr(ze_predictions, chart_positions)
        pearson_r, pearson_p = stats.pearsonr(ze_predictions, chart_positions)
        
        # MAE
        mae = sum(abs(p - a) for p, a in zip(ze_predictions, chart_positions)) / len(chart_positions)
        
        # Rank accuracy: % of tracks where predicted top-20 is actually in top-20
        n = len(ze_predictions)
        pred_ranks = self._rankdata(ze_predictions)
        actual_ranks = self._rankdata(chart_positions)
        top20_pred = set(i for i, r in enumerate(pred_ranks) if r <= 20)
        top20_actual = set(i for i, r in enumerate(actual_ranks) if r <= 20)
        precision_at_20 = len(top20_pred & top20_actual) / 20 if top20_pred else 0
        
        result = {
            "method": method_name,
            "n": n,
            "spearman_rho": spearman_r,
            "spearman_p": spearman_p,
            "pearson_r": pearson_r,
            "pearson_p": pearson_p,
            "mae": mae,
            "precision_at_20": precision_at_20,
            "predictions": ze_predictions,
        }
        
        self.results[method_name] = result
        return result
    
    def random_baseline(self, chart_positions: List[float], 
                        n_permutations: int = 500) -> dict:
        """Generate random baseline via permutation."""
        if not HAS_SCIPY:
            return {"error": "scipy required"}
        
        n = len(chart_positions)
        rhos = []
        
        for _ in range(n_permutations):
            random_preds = list(np.random.permutation(n))
            rho, _ = stats.spearmanr(random_preds, chart_positions)
            rhos.append(rho)
        
        mean_rho = np.mean(rhos)
        std_rho = np.std(rhos)
        
        result = {
            "method": "Random Baseline",
            "n": n,
            "n_permutations": n_permutations,
            "spearman_rho": mean_rho,
            "spearman_std": std_rho,
            "ci_95": (mean_rho - 1.96*std_rho, mean_rho + 1.96*std_rho),
            "permutation_rhos": rhos,
        }
        
        self.results["random"] = result
        return result
    
    def test_superiority(self, method_name: str, baseline_name: str = "random") -> dict:
        """One-sided test: is method > baseline?"""
        if not HAS_SCIPY:
            return {"error": "scipy required"}
        
        method = self.results.get(method_name)
        baseline = self.results.get(baseline_name)
        
        if not method or not baseline:
            return {"error": "Run comparisons first"}
        
        if baseline_name == "random":
            # T-test: method ρ vs distribution of random ρ's
            perm_rhos = baseline.get("permutation_rhos", [])
            if not perm_rhos:
                return {"error": "No permutation data"}
            
            t_stat, p_value = stats.ttest_1samp(perm_rhos, method["spearman_rho"])
            cohens_d = (method["spearman_rho"] - np.mean(perm_rhos)) / np.std(perm_rhos, ddof=1)
        else:
            # Fisher z-test for two correlations
            z1 = 0.5 * math.log((1 + method["spearman_rho"]) / (1 - method["spearman_rho"]))
            z2 = 0.5 * math.log((1 + baseline["spearman_rho"]) / (1 - baseline["spearman_rho"]))
            se = math.sqrt(1/(method["n"] - 3) + 1/(baseline["n"] - 3))
            z_stat = (z1 - z2) / se
            p_value = 1 - stats.norm.cdf(z_stat)
            cohens_d = (method["spearman_rho"] - baseline["spearman_rho"]) / 0.3  # approximate
        
        return {
            "method": method_name,
            "baseline": baseline_name,
            "method_rho": method["spearman_rho"],
            "baseline_rho": baseline.get("spearman_rho", np.mean(perm_rhos)),
            "cohens_d": cohens_d,
            "p_value": p_value,
            "significant": p_value < 0.05,
            "superior": method["spearman_rho"] > baseline.get("spearman_rho", 0),
        }
    
    @staticmethod
    def _rankdata(values):
        """Rank data (1 = highest)."""
        sorted_idx = sorted(range(len(values)), key=lambda i: values[i])
        ranks = [0] * len(values)
        for rank, idx in enumerate(sorted_idx, 1):
            ranks[idx] = rank
        return ranks
    
    def summary(self) -> str:
        """Generate comparison summary."""
        lines = ["═══ Baseline Comparison Summary ═══"]
        
        for name, r in self.results.items():
            if "spearman_rho" in r:
                lines.append(f"  {name:<20} ρ={r['spearman_rho']:.4f}  MAE={r.get('mae', 0):.1f}")
        
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Ze Statistics — Power Analysis")
    print()
    
    for analysis in [
        power_analysis_h1(effect_size_f2=0.10),
        power_analysis_h2(effect_size_f2=0.08),
        power_analysis_h3(expected_rho=0.25),
    ]:
        print(f"  {analysis['hypothesis']}")
        print(f"    Effect size: f²={analysis.get('effect_size_f2','N/A')} ({analysis.get('effect_size_label','N/A')})")
        print(f"    Required N:  {analysis['n_required']}")
        print(f"    Recommended: {analysis['n_recommended']}")
        print(f"    α={analysis['alpha']}, Power={analysis['power']}")
        print()
    
    print("  ✓ Power analysis complete.")
    print(f"  ✓ Total recommended participants: {sum(a['n_recommended'] for a in [power_analysis_h1(), power_analysis_h2()])}")
    print(f"  ✓ Recommended chart tracks for H3: {power_analysis_h3()['n_recommended']}")
