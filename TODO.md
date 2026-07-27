# Music — TODO

**Version:** 2.0 (post autofix Cycle 1)
**Date:** 2026-07-27

---

## 🔴 КРИТИЧЕСКИЕ (для достижения 95+/100)

### Эмпирическая валидация

- [ ] **H1: v-Pleasure эксперимент.** N ≥ 200, 100 синтетических отрывков (v от −0.5 до +0.8, τ фиксирован = 0.40). Mixed-effects quadratic regression. OSF preregistration.
- [ ] **H2: τ-Engagement эксперимент.** N ≥ 150, 60 отрывков (6 τ × 5 жанров). Dwell time + continuous arousal. OSF preregistration.
- [ ] **H3: Ze Score vs. Billboard.** N_train = 500, N_test = 200. Spearman ρ vs. peak chart position. 10-fold CV. Compare with MFCC baseline, Spotify features baseline, random baseline.
- [ ] **Калибровка весов Ze Score.** Ridge regression на training set вместо эвристических весов.
- [ ] **Сбор MIDI-датасета.** Скачать/создать MIDI для ≥ 100 треков из Billboard Hot 100 (2000–2024).

### Код

- [ ] **Batch-анализ в ze_music.py.** Функция `batch_analyze(directory)` — Ze-анализ всех MIDI в папке, вывод CSV.
- [ ] **Кросс-валидация Ze Score.** Функция `cross_validate(midi_dir, chart_data_csv, k=10)`.
- [ ] **Сравнение с baseline.** Функция `benchmark_against_baselines(ze_scores, mfcc_features, spotify_features)`.
- [ ] **Визуализация Ze-потоков.** matplotlib: график v(t), τ(t) для трека. Сохранение в PNG/SVG.

---

## 🟡 ВАЖНЫЕ

### Документация

- [x] CONCEPT.md v4.0 — переработан (autofix Cycle 1)
- [x] THEORY.md v2.0 — переработан (autofix Cycle 1)
- [x] PARAMETERS.md v2.0 — обновлён
- [x] REFERENCES.md v1.0 — создан
- [x] STATE.md — обновлён
- [x] MEMORY.md — обновлён
- [ ] MAP.md — обновить под новые файлы (REFERENCES.md)
- [ ] README.md — обновить под v4.0

### MIDI-тестирование

- [ ] Загрузить реальные MIDI: Bach WTC Book I, Mozart piano sonatas, Orff Carmina Burana
- [ ] Сравнить Ze-анализ реальных MIDI с теоретическими профилями (Таблица 5.2 CONCEPT.md)
- [ ] Загрузить поп-хиты в MIDI: Bohemian Rhapsody, Billie Jean, Smells Like Teen Spirit, и др.

### Визуализация

- [ ] Web-интерфейс: генерация + анализ + визуализация Ze-потоков
- [ ] График «Ze-траектории» трека в (v, τ)-пространстве
- [ ] Heatmap корреляции Ze-параметров с позициями в чартах

---

## 🟢 ОПЦИОНАЛЬНЫЕ

### Расширение теории

- [ ] Формальное доказательство Theorem 1 (group orbit → τ increase)
- [ ] Анализ связи φ и Z*: является ли близость φ/(1+φ) ≈ 0.618 к Z* ≈ 0.653 случайной?
- [ ] SU(2) как группа симметрий для мажоро-минорных модуляций Моцарта?
- [ ] Квантово-механическая аналогия Орф-остинато (гармонический осциллятор)?

### Продукт

- [ ] VST3 плагин (после валидации H1–H3)
- [ ] Интеграция с Ableton Live / FL Studio
- [ ] Мобильное приложение «Ze Hit Analyzer»

---

## Выполнено

- [x] 2026-07-27: Autofix Cycle 1 — CONCEPT.md v4.0, THEORY.md v2.0, REFERENCES.md, верификация всех ссылок
- [x] 2026-07-27: Создание проекта Music в ~/Desktop/Marketing/Music/
- [x] 2026-07-27: ze_music.py v1.0 — ZeMusicGenerator + SuperhitGenerator + GrooveGenerator + HookGenerator
