# Music — MAP

```
Music/                              # Проект: Ze Music — супер-популярная музыка
│
├── _pi.md                          # Правила для pi
├── CONCEPT.md                      # v4.0 — Концепт: нейронаука, гипотезы H1–H3, валидация
├── THEORY.md                       # v2.0 — Математика: обогащение Ze-потоков (группы, циклы, аттракторы)
├── PARAMETERS.md                   # v2.0 — Параметры: Ze, композиторские профили, Ze Score
├── REFERENCES.md                   # v1.0 — Верифицированные ссылки (22 источника, PMID/DOI)
├── TODO.md                         # Задачи: H1–H3, код, документация
├── MAP.md                          # ← этот файл
├── STATE.md                        # Текущий статус (post autofix Cycle 1)
├── MEMORY.md                       # История решений (autofix Cycle 1)
├── README.md                       # Краткое описание для внешних
│
├── ze_music.py                     # Основной модуль: анализ + генерация + Ze Score
│   ├── ZeEvent, ZeStream           #   Базовые структуры Ze
│   ├── ZeMusicAnalysis             #   MIDI → 4-канальный Ze-анализ
│   ├── ZeMusicGenerator            #   Генератор (Бах/Моцарт/Орф)
│   ├── SuperhitGenerator           #   Генератор поп-песен (T→S→T цикл)
│   ├── GrooveGenerator             #   Генератор грува
│   ├── HookGenerator               #   Генератор хуков (earworm)
│   └── ZeScore                     #   Метрика хитовости (0–100)
│
├── ze_research.py                  # Исследовательский модуль (autofix Cycle 2)
│   ├── batch_analyze()             #   Пакетный анализ MIDI → CSV
│   ├── cross_validate_ze_score()   #   K-fold кросс-валидация
│   ├── random_baseline()           #   Случайный baseline (перестановки)
│   ├── test_h1_v_pleasure()        #   Проверка H1 (quadratic regression)
│   ├── test_h2_tau_engagement()    #   Проверка H2
│   ├── test_h3_ze_vs_baseline()    #   Проверка H3 (t-test)
│   ├── export_to_csv/json()        #   Экспорт результатов
│   └── summary_statistics()        #   Описательная статистика
│
├── docs/                           # Документация
│   └── ...
│
├── scripts/                        # Скрипты
│   └── ...
│
├── Samnu_Azuzi/                    # Подпроект: музыка для Sulkalmakhi
│   ├── CONCEPT.md
│   ├── TODO.md
│   ├── PARAMETERS.md
│   ├── MAP.md
│   ├── STATE.md
│   ├── MEMORY.md
│   ├── README.md
│   ├── _pi.md
│   ├── docs/
│   └── scripts/
│
└── _archive/                       # Архив
    └── ...

Внешние зависимости:
├── ~/Desktop/LC/Ze/                # Ze Vectors Theory (13 аксиом, v*, математика)
├── ~/Desktop/LC/Ze/Ze_Music/       # Исходный концепт + базовая версия ze_music.py
└── ~/Desktop/Marketing/            # Родительский проект
```
