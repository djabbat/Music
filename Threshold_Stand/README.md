# 🎭 Threshold Stand — A Ze Opera in 3 Acts

**Первая в мире опера, полностью сгенерированная математической теорией музыки.**

- **Длительность:** 28′41″
- **Секций:** 29 (Увертюра + 3 акта)
- **Нот:** 2025
- **Система:** Ze-MIM (8-состоянийная машина композиции)
- **Традиции:** Грузия 🇬🇪 · Бах · Моцарт · Орф · Рок-легенды
- **Статус:** 🟢 MIDI готов | ⚫ Аудио-рендер pending

## Исполнение

```bash
# Открыть MIDI в любом DAW или проигрывателе
timidity Threshold_Stand.mid

# Или сгенерировать заново
cd ~/Desktop/Marketing/Music
python3 -c "
from ze_music import OperaGen
opera = OperaGen(seed=42)
opera.compose()
opera.save('Threshold_Stand/Threshold_Stand.mid')
"
```

## Файлы

| Файл | Описание |
|------|----------|
| `CONCEPT.md` | Концепция оперы и сюжет |
| `SCORE.md` | Полная партитура — 29 секций в Ze-нотации |
| `PARAMETERS.md` | State Machine, стили, оркестровка |
| `Threshold_Stand.mid` | MIDI-файл оперы |

---
*Threshold Stand (c) 2026 Jaba Tqemaladze / Ze-MIM System*
