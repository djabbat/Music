#!/usr/bin/env python3
"""
Ze Music Visualisation — графики Ze-потоков и статистики.
Генерирует:
  1. Ze-траекторию трека в (v, τ)-пространстве
  2. Распределение Ze Score по грейдам
  3. Scatter-plot: Ze Score vs. позиция в чарте
  4. Тепловую карту корреляций Ze-параметров

Использование:
  python3 ze_visualise.py data/results/synthetic_analysis.csv
"""

import sys
import os
import csv
import math
from collections import defaultdict, Counter

try:
    import matplotlib
    matplotlib.use('Agg')  # без GUI
    import matplotlib.pyplot as plt
    import numpy as np
    HAS_MPL = True
except ImportError:
    HAS_MPL = False
    print("ERROR: matplotlib not installed. pip install matplotlib")
    sys.exit(1)


def load_analyses(csv_path):
    """Загрузить CSV с результатами анализа."""
    rows = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def plot_ze_trajectory(analyses, output='data/results/ze_trajectory.png'):
    """График: все треки в (v, τ)-пространстве."""
    v_vals = [float(r['v']) for r in analyses]
    tau_vals = [float(r['tau']) for r in analyses]
    scores = [float(r['ze_score']) for r in analyses]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Left: v vs τ scatter, coloured by Ze Score
    sc = ax1.scatter(v_vals, tau_vals, c=scores, cmap='RdYlGn', 
                     alpha=0.7, s=30, edgecolors='black', linewidth=0.3)
    ax1.axvline(x=0.30685, color='blue', linestyle='--', alpha=0.5, label="v* = 0.307")
    ax1.axvline(x=0.35, color='green', linestyle='--', alpha=0.3)
    ax1.axvline(x=0.50, color='green', linestyle='--', alpha=0.3)
    ax1.axhline(y=0.25, color='orange', linestyle='--', alpha=0.3)
    ax1.axhline(y=0.50, color='orange', linestyle='--', alpha=0.3)
    
    # Highlight impact zone
    ax1.axvspan(0.35, 0.50, alpha=0.08, color='green')
    ax1.axhspan(0.25, 0.50, alpha=0.08, color='orange')
    
    ax1.set_xlabel('Ze Velocity (v)', fontsize=12)
    ax1.set_ylabel('Ze Complexity (τ)', fontsize=12)
    ax1.set_title('Ze Parameter Space: v vs τ', fontsize=14)
    ax1.legend(loc='upper right')
    cbar = plt.colorbar(sc, ax=ax1)
    cbar.set_label('Ze Score', fontsize=10)
    
    # Right: histogram of Ze Scores
    ax2.hist(scores, bins=20, color='steelblue', edgecolor='black', alpha=0.7)
    ax2.axvline(x=np.mean(scores), color='red', linestyle='--', linewidth=2, label=f'Mean = {np.mean(scores):.1f}')
    ax2.axvline(x=np.median(scores), color='orange', linestyle='-', linewidth=1.5, label=f'Median = {np.median(scores):.1f}')
    ax2.set_xlabel('Ze Score', fontsize=12)
    ax2.set_ylabel('Number of Tracks', fontsize=12)
    ax2.set_title('Ze Score Distribution', fontsize=14)
    ax2.legend()
    
    plt.tight_layout()
    plt.savefig(output, dpi=150, bbox_inches='tight')
    print(f'Saved: {output}')
    plt.close()


def plot_chart_correlation(analyses, output='data/results/chart_correlation.png'):
    """Scatter-plot: Ze Score vs. позиция в чарте + линия регрессии."""
    scores = [float(r['ze_score']) for r in analyses if r.get('chart_position')]
    positions = [float(r['chart_position']) for r in analyses if r.get('chart_position')]
    
    if len(scores) < 5:
        print("Not enough chart data for correlation plot.")
        return
    
    fig, ax = plt.subplots(figsize=(10, 7))
    
    # Scatter
    ax.scatter(scores, positions, alpha=0.6, c='steelblue', edgecolors='black', linewidth=0.3, s=40)
    
    # Regression line
    if len(scores) > 2:
        coeffs = np.polyfit(scores, positions, 1)
        poly = np.poly1d(coeffs)
        x_line = np.linspace(min(scores), max(scores), 100)
        ax.plot(x_line, poly(x_line), 'r-', linewidth=2, alpha=0.8, 
                label=f'Linear fit (slope={coeffs[0]:.2f})')
    
    # Spearman correlation
    from scipy import stats as sp_stats
    rho, pval = sp_stats.spearmanr(scores, positions)
    
    ax.set_xlabel('Ze Score', fontsize=12)
    ax.set_ylabel('Chart Position (1 = #1)', fontsize=12)
    ax.set_title(f'Ze Score vs. Chart Position\nSpearman ρ = {rho:.3f} (p = {pval:.4f})', fontsize=14)
    ax.invert_yaxis()  # #1 at top
    ax.legend()
    
    # Annotate: expected direction
    ax.annotate('Higher Ze Score →\nbetter chart position', 
                xy=(max(scores)*0.8, max(positions)*0.8),
                fontsize=10, color='gray', fontstyle='italic')
    
    plt.tight_layout()
    plt.savefig(output, dpi=150, bbox_inches='tight')
    print(f'Saved: {output}')
    plt.close()


def plot_grade_distribution(analyses, output='data/results/grade_distribution.png'):
    """Pie chart распределения грейдов."""
    grades = Counter(r['ze_grade'] for r in analyses)
    
    fig, ax = plt.subplots(figsize=(8, 8))
    
    labels = list(grades.keys())
    sizes = list(grades.values())
    colors = ['#2ecc71', '#27ae60', '#f1c40f', '#e67e22', '#e74c3c', '#95a5a6']
    explode = [0.05] * len(labels)
    
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, autopct='%1.1f%%',
        colors=colors[:len(labels)], explode=explode,
        shadow=False, startangle=90,
        textprops={'fontsize': 10}
    )
    
    for at in autotexts:
        at.set_fontweight('bold')
    
    ax.set_title(f'Ze Score Grade Distribution\n(N = {len(analyses)} tracks)', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output, dpi=150, bbox_inches='tight')
    print(f'Saved: {output}')
    plt.close()


def plot_parameter_heatmap(analyses, output='data/results/parameter_correlation.png'):
    """Тепловая карта корреляций между Ze-параметрами и позицией в чарте."""
    params = ['v', 'tau', 'chi', 'zeta', 'C(4)', 'C(8)', 'ze_score']
    if any(r.get('chart_position') for r in analyses):
        params.append('chart_position')
    
    # Extract data
    data = {}
    for p in params:
        if p == 'chart_position':
            vals = [float(r.get('chart_position', 0)) for r in analyses if r.get('chart_position')]
        else:
            vals = [float(r[p]) for r in analyses]
        data[p] = vals
    
    # Only use rows where all params exist
    n = min(len(data[p]) for p in params)
    matrix = np.zeros((len(params), n))
    for i, p in enumerate(params):
        matrix[i, :] = data[p][:n]
    
    # Correlation matrix
    corr = np.corrcoef(matrix)
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    im = ax.imshow(corr, cmap='RdBu_r', vmin=-1, vmax=1, aspect='equal')
    
    # Labels
    ax.set_xticks(range(len(params)))
    ax.set_yticks(range(len(params)))
    ax.set_xticklabels(params, fontsize=10, rotation=45)
    ax.set_yticklabels(params, fontsize=10)
    
    # Annotate values
    for i in range(len(params)):
        for j in range(len(params)):
            text = ax.text(j, i, f'{corr[i, j]:.2f}',
                          ha='center', va='center',
                          color='white' if abs(corr[i, j]) > 0.5 else 'black',
                          fontsize=9, fontweight='bold' if abs(corr[i, j]) > 0.7 else 'normal')
    
    ax.set_title('Ze Parameter Correlation Matrix', fontsize=14, fontweight='bold')
    
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('Pearson r', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(output, dpi=150, bbox_inches='tight')
    print(f'Saved: {output}')
    plt.close()


def plot_v_distribution(analyses, output='data/results/v_distribution.png'):
    """Распределение v с отмеченными критическими точками."""
    v_vals = [float(r['v']) for r in analyses]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.hist(v_vals, bins=30, color='steelblue', edgecolor='black', alpha=0.7, density=True)
    
    # KDE (simple: normal fit)
    mu, std = np.mean(v_vals), np.std(v_vals)
    x = np.linspace(-1, 1, 200)
    kde = (1/(std * np.sqrt(2*np.pi))) * np.exp(-0.5 * ((x - mu) / std)**2)
    ax.plot(x, kde, 'r-', linewidth=2, alpha=0.7, label=f'Normal fit (μ={mu:.2f}, σ={std:.2f})')
    
    # Critical values
    ax.axvline(x=0.0, color='gray', linestyle=':', alpha=0.5, label='v = 0 (balanced)')
    ax.axvline(x=0.30685, color='blue', linestyle='--', linewidth=2, label='v* = 0.307 (max τ)')
    ax.axvline(x=0.35, color='green', linestyle='--', alpha=0.7)
    ax.axvline(x=0.50, color='green', linestyle='--', alpha=0.7)
    ax.axvspan(0.35, 0.50, alpha=0.1, color='green', label='Impact zone (0.35–0.50)')
    
    ax.set_xlabel('Ze Velocity (v)', fontsize=12)
    ax.set_ylabel('Density', fontsize=12)
    ax.set_title(f'Distribution of Ze Velocity (N={len(v_vals)})', fontsize=14)
    ax.legend(fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output, dpi=150, bbox_inches='tight')
    print(f'Saved: {output}')
    plt.close()


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 ze_visualise.py <analysis_csv>")
        print("  Uses data/results/synthetic_analysis.csv by default")
        csv_path = 'data/results/synthetic_analysis.csv'
    else:
        csv_path = sys.argv[1]
    
    print(f"Loading: {csv_path}")
    analyses = load_analyses(csv_path)
    print(f"Loaded {len(analyses)} tracks.")
    
    os.makedirs('data/results', exist_ok=True)
    
    print("\nGenerating plots...")
    plot_ze_trajectory(analyses)
    plot_v_distribution(analyses)
    plot_grade_distribution(analyses)
    plot_chart_correlation(analyses)
    plot_parameter_heatmap(analyses)
    
    print(f"\nAll plots saved to data/results/")


if __name__ == "__main__":
    main()
