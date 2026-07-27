# Threshold Stand — MAP

```
Threshold_Stand/                 # Опера «Threshold Stand»
├── _pi.md                       # Правила для pi
├── CONCEPT.md                   # Концепция оперы
├── SCORE.md                     # Полная партитура (29 секций, Ze-нотация)
├── PARAMETERS.md                # Параметры: State Machine, стили, оркестровка
├── TODO.md                      # Задачи
├── MAP.md                       # ← этот файл
├── STATE.md                     # Статус
├── MEMORY.md                    # История решений
├── README.md                    # Краткое описание
│
├── opera_generator.py           # Генератор оперы (OperaGen)
├── Threshold_Stand.mid          # MIDI-файл (2025 нот, 28′41″)
│
├── score/                       # Партитуры по голосам
│   ├── tenor.md                 # Партия тенора
│   ├── soprano.md               # Партия сопрано
│   ├── baritone.md              # Партия баритона
│   ├── chorus.md                # Хоровая партия
│   └── orchestra.md             # Оркестровая партия
│
├── docs/                        # Документация
│   ├── libretto.md              # Либретто (текст)
│   ├── synopsis.md              # Синопсис
│   └── analysis.md              # Музыковедческий анализ
│
├── scripts/                     # Скрипты
│   └── render_audio.sh          # MIDI → аудио рендеринг
│
└── _archive/                    # Архив
    └── ...
```

## Внешние зависимости

```
~/Desktop/Marketing/Music/       # Ze-MIM система
  ├── ze_music.py                # OperaGenerator
  ├── ze_research.py             # Анализ
  ├── ze_statistics.py           # Power analysis
  └── data/midi/opera/           # Сгенерированные MIDI
```
