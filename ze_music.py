"""
Ze Music Analyzer & Synthesizer
================================
Анализ MIDI-файлов через Ze-теорию и генерация музыки
на основе композиторских профилей (Bach, Mozart, Orff).

Зависимости: pip install mido numpy scipy
"""

import math
import random
from collections import Counter
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional, Literal
from enum import Enum

# ============================================================
# ZE CORE
# ============================================================

class ZeEvent(Enum):
    T = "T"  # Tension — рост
    S = "S"  # Stretch — спад

@dataclass
class ZeStream:
    """Бинарный поток T/S событий."""
    events: List[ZeEvent] = field(default_factory=list)
    
    def append(self, a, b):
        """Добавить событие: T если a > b, S иначе."""
        self.events.append(ZeEvent.T if a > b else ZeEvent.S)
    
    def append_direct(self, event: ZeEvent):
        self.events.append(event)
    
    @property
    def N(self) -> int:
        return len(self.events)
    
    @property
    def n_t(self) -> int:
        return sum(1 for e in self.events if e == ZeEvent.T)
    
    @property
    def n_s(self) -> int:
        return sum(1 for e in self.events if e == ZeEvent.S)
    
    @property
    def v(self) -> float:
        """Ze velocity: (N_T - N_S) / N ∈ [-1, +1]"""
        if self.N == 0:
            return 0.0
        return (self.n_t - self.n_s) / self.N
    
    @property
    def Z(self) -> float:
        """Ze index: N_T / N"""
        if self.N == 0:
            return 0.5
        return self.n_t / self.N
    
    @property
    def tau(self) -> float:
        """Ze complexity: нормализованная энтропия Шеннона."""
        if self.N <= 1:
            return 0.0
        p_t = self.n_t / self.N
        p_s = self.n_s / self.N
        
        def safe_entropy(p):
            return -p * math.log2(p) if p > 0 else 0.0
        
        H = safe_entropy(p_t) + safe_entropy(p_s)
        return H / math.log2(self.N) if self.N > 1 else 0.0
    
    @property
    def chi(self) -> float:
        """Ze variability: амплитуда осцилляции."""
        if self.N < 2:
            return 0.0
        # Вычисляем вариабельность по окнам
        window = max(2, self.N // 10)
        ratios = []
        for i in range(0, self.N - window, window):
            chunk = self.events[i:i+window]
            t_count = sum(1 for e in chunk if e == ZeEvent.T)
            ratios.append(t_count / len(chunk))
        if not ratios or sum(ratios) == 0:
            return 0.0
        return (max(ratios) - min(ratios)) / (sum(ratios) / len(ratios))
    
    @property
    def zeta(self) -> float:
        """Ze impedance: ζ = τ / |v|"""
        if abs(self.v) < 1e-10:
            return float('inf')
        return self.tau / abs(self.v)
    
    def autocorrelation(self, lag: int) -> float:
        """Автокорреляция с лагом k."""
        if lag >= self.N:
            return 0.0
        values = [1 if e == ZeEvent.T else -1 for e in self.events]
        mean = sum(values) / len(values)
        num = sum((values[i] - mean) * (values[i + lag] - mean) 
                  for i in range(len(values) - lag))
        den = sum((v - mean) ** 2 for v in values)
        return num / den if den != 0 else 0.0
    
    def sliding_v(self, window: int) -> List[float]:
        """Скользящее окно v."""
        if window >= self.N:
            return [self.v]
        vs = []
        for i in range(self.N - window + 1):
            chunk = ZeStream()
            chunk.events = self.events[i:i+window]
            vs.append(chunk.v)
        return vs
    
    def __repr__(self):
        return f"ZeStream(N={self.N}, v={self.v:.4f}, τ={self.tau:.4f}, Z={self.Z:.4f})"


# ============================================================
# MIDI → ZE CONVERTER
# ============================================================

@dataclass
class Note:
    pitch: int      # MIDI номер ноты (60 = C4)
    start: float    # начало в секундах
    duration: float # длительность в секундах
    velocity: int   # громкость (0-127)

@dataclass
class ZeMusicAnalysis:
    """Полный Ze-анализ музыкального произведения."""
    name: str
    notes: List[Note] = field(default_factory=list)
    
    # 4 канала Ze
    pitch_stream: ZeStream = field(default_factory=ZeStream)
    rhythm_stream: ZeStream = field(default_factory=ZeStream)
    dynamics_stream: ZeStream = field(default_factory=ZeStream)
    harmony_stream: ZeStream = field(default_factory=ZeStream)
    
    # Агрегированный поток
    combined_stream: ZeStream = field(default_factory=ZeStream)
    
    def analyze(self, notes: List[Note]) -> "ZeMusicAnalysis":
        """Преобразовать ноты в 4-канальный Ze-поток."""
        if len(notes) < 2:
            return self
        
        self.notes = notes
        sorted_notes = sorted(notes, key=lambda n: n.start)
        
        for i in range(1, len(sorted_notes)):
            prev = sorted_notes[i-1]
            curr = sorted_notes[i]
            
            # 1. Pitch: T если мелодия идёт вверх
            self.pitch_stream.append(curr.pitch, prev.pitch)
            
            # 2. Rhythm: T если длительность растёт
            self.rhythm_stream.append(curr.duration, prev.duration)
            
            # 3. Dynamics: T если громкость растёт
            self.dynamics_stream.append(curr.velocity, prev.velocity)
            
            # 4. Harmony: T если интервал диссонантный (> 6 полутонов)
            interval = abs(curr.pitch - prev.pitch)
            is_dissonant = (interval % 12) not in [0, 3, 4, 5, 7, 8, 9]  # не в мажорной/минорной гамме
            self.harmony_stream.append_direct(
                ZeEvent.T if is_dissonant else ZeEvent.S
            )
            
            # Комбинированный: мажоритарное голосование 4 каналов
            t_count = (
                (1 if self.pitch_stream.events[-1] == ZeEvent.T else 0) +
                (1 if self.rhythm_stream.events[-1] == ZeEvent.T else 0) +
                (1 if self.dynamics_stream.events[-1] == ZeEvent.T else 0) +
                (1 if self.harmony_stream.events[-1] == ZeEvent.T else 0)
            )
            self.combined_stream.append_direct(
                ZeEvent.T if t_count >= 2 else ZeEvent.S
            )
        
        return self
    
    def summary(self) -> str:
        """Сводка Ze-анализа."""
        lines = [
            f"═══ Ze Music Analysis: {self.name} ═══",
            f"Нот: {len(self.notes)} | Событий: {self.pitch_stream.N}",
            "",
            f"{'Канал':<12} {'v':>8} {'τ':>8} {'Z':>8} {'χ':>8} {'ζ':>8}",
            f"{'─'*12} {'─'*8} {'─'*8} {'─'*8} {'─'*8} {'─'*8}",
        ]
        
        for name, stream in [
            ("Pitch", self.pitch_stream),
            ("Rhythm", self.rhythm_stream),
            ("Dynamics", self.dynamics_stream),
            ("Harmony", self.harmony_stream),
            ("Combined", self.combined_stream),
        ]:
            zeta_str = f"{stream.zeta:.2f}" if stream.zeta != float('inf') else "∞"
            lines.append(
                f"{name:<12} {stream.v:>+8.4f} {stream.tau:>8.4f} "
                f"{stream.Z:>8.4f} {stream.chi:>8.4f} {zeta_str:>8}"
            )
        
        # Близость к v*
        v_star = 1.0 - math.log(2)  # ≈ 0.3069
        v_dist = abs(self.combined_stream.v - v_star)
        lines.append("")
        lines.append(f"v* = {v_star:.4f} (точное)")
        lines.append(f"Расстояние до v*: {v_dist:.4f}")
        
        # Определение композитора по Ze-сигнатуре
        composer = self._guess_composer()
        lines.append(f"Ze-сигнатура → {composer}")
        
        return "\n".join(lines)
    
    def _guess_composer(self) -> str:
        """Угадать композитора по Ze-сигнатуре."""
        v = self.combined_stream.v
        tau = self.combined_stream.tau
        zeta = min(self.combined_stream.zeta, 10.0)
        chi = self.combined_stream.chi
        
        scores = {
            "Bach":     abs(v - 0.0) * 0.3 + abs(tau - 0.8) * 0.4 + abs(zeta - 0.2) * 0.3,
            "Mozart":   abs(v - 0.2) * 0.3 + abs(tau - 0.5) * 0.4 + abs(zeta - 0.5) * 0.3,
            "Orff":     abs(v - 0.0) * 0.2 + abs(tau - 0.25) * 0.3 + abs(zeta - 5.0) * 0.2 + abs(chi - 0.9) * 0.3,
        }
        
        return min(scores, key=scores.get)


# ============================================================
# COMPOSER PROFILES
# ============================================================

@dataclass
class ComposerProfile:
    """Параметры Ze для композитора."""
    name: str
    v_target: float       # целевая Ze-скорость
    tau_target: float     # целевая сложность
    zeta: float           # импеданс (персистентность)
    chi: float            # вариабельность
    scale: List[int]      # звукоряд (полутоны от тоники)
    base_octave: int = 4
    tonic: int = 0        # 0 = C, 2 = D, и т.д.
    
    # Дополнительные параметры
    voices: int = 1
    ostinato_period: int = 0
    golden_ratio: float = 1.0
    form: str = "free"


# Стандартные профили
BACH = ComposerProfile(
    name="Bach",
    v_target=0.0,         # сбалансированный (v* в длинных произведениях)
    tau_target=0.85,      # высокая сложность (полифония)
    zeta=0.15,            # низкий импеданс (трансформации)
    chi=0.4,              # умеренная вариабельность
    scale=[0, 2, 3, 5, 7, 8, 10],  # минор
    tonic=2,              # D minor
    voices=4,
    form="fugue",
)

MOZART = ComposerProfile(
    name="Mozart",
    v_target=0.20,        # лёгкий T-уклон (восходящие мелодии)
    tau_target=0.55,      # умеренная сложность
    zeta=0.45,            # средний импеданс (сонатная форма)
    chi=0.25,             # низкая вариабельность (элегантность)
    scale=[0, 2, 4, 5, 7, 9, 11],  # мажор
    tonic=0,              # C major
    voices=1,
    golden_ratio=1.618,
    form="sonata",
)

ORFF = ComposerProfile(
    name="Orff",
    v_target=0.0,         # сбалансированный (остинато)
    tau_target=0.25,      # низкая сложность
    zeta=0.90,            # ОЧЕНЬ высокий импеданс (остинато)
    chi=0.95,             # экстремальная динамика
    scale=[0, 2, 3, 5, 7, 8, 10],  # минор
    tonic=2,              # D minor
    voices=1,
    ostinato_period=8,
    form="ostinato",
)

PROFILES = {
    "Bach": BACH,
    "Mozart": MOZART,
    "Orff": ORFF,
}


# ============================================================
# ZE MUSIC GENERATOR (СИНТЕЗ)
# ============================================================

class ZeMusicGenerator:
    """
    Генератор музыки на основе Ze-теории.
    
    Алгоритм:
    1. Генерируем 4-канальный Ze-поток с целевыми v, τ, ζ
    2. Преобразуем Ze-поток в последовательность нот (MIDI)
    3. Применяем композиторские трансформации (фуга, соната, остинато)
    """
    
    def __init__(self, profile: ComposerProfile, seed: int = 42):
        self.profile = profile
        random.seed(seed)
        
        # Текущее состояние
        self.current_pitch: int = 60 + profile.tonic  # MIDI номер
        self.current_duration: float = 1.0  # в долях (1.0 = четверть)
        self.current_velocity: int = 80
        
        # Масштабные ступени
        self.scale_pitches = self._build_scale()
        
        # Сгенерированные ноты
        self.notes: List[Note] = []
        
        # Ze-потоки (для анализа)
        self.pitch_stream = ZeStream()
        self.rhythm_stream = ZeStream()
        self.dynamics_stream = ZeStream()
        self.harmony_stream = ZeStream()
    
    def _build_scale(self) -> List[int]:
        """Построить звукоряд от тоники на 3 октавы."""
        pitches = []
        base = 60 + self.profile.tonic  # MIDI C4 = 60
        for octave in range(3):
            for step in self.profile.scale:
                pitch = base + step + (octave * 12)
                if 21 <= pitch <= 108:  # диапазон фортепиано
                    pitches.append(pitch)
        return pitches
    
    def _apply_ze_dynamics(self, zv: float, zt: float) -> Tuple[ZeEvent, ZeEvent, ZeEvent, ZeEvent]:
        """
        Сгенерировать 4 Ze-события, стремясь к целевым v и τ.
        Использует обратную связь: сравнивает текущие v с целевыми.
        """
        zeta = self.profile.zeta
        
        # Отклонение от цели
        dv = self.profile.v_target - zv
        dt = self.profile.tau_target - zt
        
        # Вероятность T для каждого канала
        p_t_pitch = 0.5 + 0.3 * dv        # основной драйвер v
        p_t_rhythm = 0.5 - 0.1 * dv       # ритм противодействует для баланса
        p_t_dynamics = 0.5 + 0.4 * dv     # динамика усиливает драйвер
        p_t_harmony = 0.5 + 0.2 * (dv + dt)  # гармония — сложность
        
        # Импеданс: сохраняем предыдущее состояние
        if self.pitch_stream.N > 0:
            prev_v = self.pitch_stream.v
            # Чем выше ζ, тем сильнее тянем к предыдущему v
            p_t_pitch = p_t_pitch * (1 - zeta) + (0.5 + 0.5 * prev_v) * zeta
        
        def sample(p):
            return ZeEvent.T if random.random() < max(0.05, min(0.95, p)) else ZeEvent.S
        
        return (
            sample(p_t_pitch),
            sample(p_t_rhythm),
            sample(p_t_dynamics),
            sample(p_t_harmony),
        )
    
    def _ze_to_note(self, z_pitch: ZeEvent, z_rhythm: ZeEvent, 
                    z_dynamics: ZeEvent, z_harmony: ZeEvent) -> Note:
        """Преобразовать 4 Ze-события в музыкальную ноту."""
        
        # 1. PITCH — T: вверх, S: вниз
        current_idx = self.scale_pitches.index(self.current_pitch) if self.current_pitch in self.scale_pitches else 0
        
        if z_pitch == ZeEvent.T:
            step = random.choice([1, 2, 3])  # поступенное или терцовое движение
        else:
            step = random.choice([-1, -2, -3])
        
        new_idx = max(0, min(len(self.scale_pitches) - 1, current_idx + step))
        self.current_pitch = self.scale_pitches[new_idx]
        
        # 2. RHYTHM — T: длиннее, S: короче
        DURATIONS = [0.25, 0.5, 0.5, 1.0, 1.0, 1.5, 2.0, 4.0]
        dur_idx = DURATIONS.index(self.current_duration) if self.current_duration in DURATIONS else 3
        
        if z_rhythm == ZeEvent.T:
            dur_idx = min(len(DURATIONS) - 1, dur_idx + 1)
        else:
            dur_idx = max(0, dur_idx - 1)
        
        self.current_duration = DURATIONS[dur_idx]
        
        # 3. DYNAMICS — T: громче, S: тише
        if z_dynamics == ZeEvent.T:
            self.current_velocity = min(127, self.current_velocity + random.randint(5, 15))
        else:
            self.current_velocity = max(20, self.current_velocity - random.randint(5, 15))
        
        # 4. HARMONY — T: диссонанс (добавляем случайное смещение), S: консонанс
        if z_harmony == ZeEvent.T and random.random() < 0.3:
            # Изредка добавляем диссонантный скачок
            self.current_pitch += random.choice([-6, -5, 5, 6, 11, -11])
            self.current_pitch = max(21, min(108, self.current_pitch))
        
        return Note(
            pitch=self.current_pitch,
            start=0.0,  # будет вычислено позже
            duration=max(0.125, min(4.0, self.current_duration)),
            velocity=self.current_velocity,
        )
    
    def generate(self, n_events: int, apply_form: bool = True) -> List[Note]:
        """
        Сгенерировать музыкальное произведение из n_events Ze-событий.
        
        Args:
            n_events: количество событий (≈ количество нот)
            apply_form: применять композиторскую форму (фуга, соната, остинато)
        
        Returns:
            Список Note с вычисленными start-временами
        """
        self.notes = []
        self.pitch_stream = ZeStream()
        self.rhythm_stream = ZeStream()
        self.dynamics_stream = ZeStream()
        self.harmony_stream = ZeStream()
        
        form_events = n_events
        
        if apply_form and self.profile.form == "fugue" and self.profile.voices > 1:
            form_events = self._generate_fugue(n_events)
        elif apply_form and self.profile.form == "sonata":
            form_events = self._generate_sonata(n_events)
        elif apply_form and self.profile.form == "ostinato":
            form_events = self._generate_ostinato(n_events)
        else:
            form_events = self._generate_free(n_events)
        
        # Вычисляем времена начала
        current_time = 0.0
        for note in form_events:
            note.start = current_time
            current_time += note.duration
        
        self.notes = form_events
        return self.notes
    
    def _generate_free(self, n: int) -> List[Note]:
        """Свободная генерация (без формы)."""
        notes = []
        for _ in range(n):
            zv = self.pitch_stream.v
            zt = self.pitch_stream.tau
            
            zp, zr, zd, zh = self._apply_ze_dynamics(zv, zt)
            
            # Обновляем потоки
            self.pitch_stream.events.append(zp)
            self.rhythm_stream.events.append(zr)
            self.dynamics_stream.events.append(zd)
            self.harmony_stream.events.append(zh)
            
            notes.append(self._ze_to_note(zp, zr, zd, zh))
        
        return notes
    
    def _generate_ostinato(self, n: int) -> List[Note]:
        """
        Орф-остинато: повторяющийся паттерн с высокой ζ.
        Генерируем паттерн длиной ostinato_period, затем повторяем.
        """
        period = self.profile.ostinato_period
        
        # Генерируем базовый паттерн
        base_notes = self._generate_free(period)
        
        # Повторяем, варьируя динамику (χ очень высокий)
        notes = []
        for i in range(n // period + 1):
            for j, note in enumerate(base_notes):
                new_note = Note(
                    pitch=note.pitch,
                    start=0.0,
                    duration=note.duration,
                    velocity=min(127, max(20, note.velocity + 
                        random.randint(-40, 40) if self.profile.chi > 0.8 else 0)),
                )
                notes.append(new_note)
                if len(notes) >= n:
                    break
            if len(notes) >= n:
                break
        
        return notes[:n]
    
    def _generate_sonata(self, n: int) -> List[Note]:
        """
        Моцарт-соната: экспозиция → разработка → реприза.
        Золотое сечение в пропорциях.
        """
        phi = 1.618
        
        # Экспозиция (тема A + тема B)
        n_expo = int(n / (1 + 1/phi + 1/phi**2))  # ~38% длины
        n_dev = int(n_expo / phi)                   # ~24% длины
        n_recap = n - n_expo - n_dev                # ~38% длины
        
        # Экспозиция — T-доминантная (v > 0)
        self.profile.v_target = 0.25
        expo_notes = self._generate_free(n_expo)
        
        # Разработка — S-доминантная (v < 0), высокая τ
        self.profile.v_target = -0.15
        dev_notes = self._generate_free(n_dev)
        
        # Реприза — возврат к T (v > 0)
        self.profile.v_target = 0.20
        recap_notes = self._generate_free(n_recap)
        
        return expo_notes + dev_notes + recap_notes
    
    def _generate_fugue(self, n: int) -> List[Note]:
        """
        Бах-фуга: каждая тема = Ze-поток; применяем трансформации
        (инверсия, ракоход, аугментация, стретто).
        """
        n_voices = self.profile.voices
        subject_len = max(8, n // (n_voices * 2))
        
        # 1. Генерируем тему (субъект)
        subject = self._generate_free(subject_len)
        subject_notes = subject.copy()
        
        all_voices = [[] for _ in range(n_voices)]
        
        # 2. Каждый голос — трансформация субъекта
        for voice_i in range(n_voices):
            if voice_i == 0:
                # Voice 1 = оригинал
                transformed = subject_notes.copy()
            elif voice_i == 1:
                # Voice 2 = инверсия (S = -T)
                transformed = []
                for note in subject_notes:
                    # Инвертируем относительно тоники
                    tonic = 60 + self.profile.tonic
                    inverted_pitch = tonic + (tonic - note.pitch)
                    transformed.append(Note(
                        pitch=max(21, min(108, inverted_pitch)),
                        start=0.0,
                        duration=note.duration,
                        velocity=note.velocity,
                    ))
            elif voice_i == 2:
                # Voice 3 = ракоход
                transformed = subject_notes[::-1]
            elif voice_i == 3:
                # Voice 4 = аугментация (2x медленнее)
                transformed = []
                for note in subject_notes:
                    transformed.append(Note(
                        pitch=note.pitch,
                        start=0.0,
                        duration=min(4.0, note.duration * 2.0),
                        velocity=note.velocity,
                    ))
            else:
                transformed = subject_notes.copy()
            
            # Стретто: каждый голос вступает с задержкой
            delay_notes = [Note(pitch=0, start=0.0, duration=voice_i * 4 * 0.25, velocity=0)]  # пауза
            all_voices[voice_i] = delay_notes + transformed
        
        # 3. Интерливинг голосов по времени
        combined = []
        max_len = max(len(v) for v in all_voices)
        
        time_counters = [0.0] * n_voices
        voice_idx = [0] * n_voices
        
        while len(combined) < n:
            for vi in range(n_voices):
                if voice_idx[vi] < len(all_voices[vi]):
                    note = all_voices[vi][voice_idx[vi]]
                    if note.pitch != 0:  # не пауза
                        combined.append(Note(
                            pitch=note.pitch,
                            start=0.0,
                            duration=note.duration,
                            velocity=note.velocity,
                        ))
                        if len(combined) >= n:
                            break
                    voice_idx[vi] += 1
        
        return combined[:n]
    
    def to_midi_bytes(self, tempo: int = 120) -> bytes:
        """
        Экспортировать сгенерированные ноты в MIDI-файл (байты).
        Требуется mido: pip install mido
        """
        try:
            import mido
            from mido import MidiFile, MidiTrack, Message, MetaMessage
        except ImportError:
            raise ImportError("mido не установлен. pip install mido")
        
        mid = MidiFile(ticks_per_beat=480)
        track = MidiTrack()
        mid.tracks.append(track)
        
        # Темп
        track.append(MetaMessage('set_tempo', tempo=mido.bpm2tempo(tempo)))
        track.append(MetaMessage('track_name', name=f'Ze Music - {self.profile.name}'))
        
        ticks_per_beat = mid.ticks_per_beat
        
        for note in sorted(self.notes, key=lambda n: n.start):
            start_ticks = int(note.start * ticks_per_beat * tempo / 60)
            dur_ticks = int(note.duration * ticks_per_beat * tempo / 60)
            
            track.append(Message('note_on', note=note.pitch, velocity=note.velocity, 
                                time=start_ticks if note == self.notes[0] else 0, channel=0))
            track.append(Message('note_off', note=note.pitch, velocity=0,
                                time=max(1, dur_ticks), channel=0))
        
        # Сохраняем
        import io
        buf = io.BytesIO()
        mid.save(file=buf)
        return buf.getvalue()
    
    def save_midi(self, filepath: str, tempo: int = 120):
        """Сохранить в MIDI-файл."""
        with open(filepath, 'wb') as f:
            f.write(self.to_midi_bytes(tempo))
        return filepath


# ============================================================
# MIDI FILE LOADER
# ============================================================

def load_midi(filepath: str) -> List[Note]:
    """
    Загрузить MIDI-файл и извлечь ноты.
    
    Args:
        filepath: путь к .mid файлу
    
    Returns:
        Список Note
    """
    try:
        import mido
    except ImportError:
        raise ImportError("mido не установлен. pip install mido")
    
    mid = mido.MidiFile(filepath)
    notes = []
    current_time = 0.0
    active_notes: Dict[int, Tuple[float, int]] = {}  # pitch → (start, velocity)
    
    for track in mid.tracks:
        current_time = 0.0
        for msg in track:
            current_time += msg.time
            
            if msg.type == 'note_on' and msg.velocity > 0:
                active_notes[msg.note] = (current_time, msg.velocity)
            elif msg.type in ('note_off', 'note_on') and msg.note in active_notes:
                start, vel = active_notes.pop(msg.note)
                duration = current_time - start
                if duration > 0:
                    notes.append(Note(
                        pitch=msg.note,
                        start=start,
                        duration=duration if msg.type == 'note_off' else msg.time,
                        velocity=vel,
                    ))
    
    # Если tempo не задан, используем условные единицы
    if mid.ticks_per_beat > 0:
        tempo = 500000  # 120 BPM по умолчанию
        for track in mid.tracks:
            for msg in track:
                if msg.type == 'set_tempo':
                    tempo = msg.tempo
                    break
        
        tick_to_second = tempo / (mid.ticks_per_beat * 1_000_000)
        for note in notes:
            note.start *= tick_to_second
            note.duration *= tick_to_second
    
    return sorted(notes, key=lambda n: n.start)


# ============================================================
# MAIN DEMO
# ============================================================

def demo_analysis():
    """Демонстрация: анализ сгенерированной музыки."""
    print("╔══════════════════════════════════════════╗")
    print("║   Ze Music - Анализ и Синтез            ║")
    print("║   Бах · Моцарт · Орф через Ze-теорию    ║")
    print("╚══════════════════════════════════════════╝")
    print()
    
    v_star = 1.0 - math.log(2)
    print(f"v* = 1 − ln 2 = {v_star:.6f} (точное)")
    print(f"Z* = (1 + v*)/2 = {(1 + v_star)/2:.6f}")
    print()
    
    # Генерируем произведения
    for profile in [BACH, MOZART, ORFF]:
        print(f"\n{'─'*50}")
        print(f"  Генерация: {profile.name} ({profile.form}, {profile.voices} гол.)")
        print(f"{'─'*50}")
        
        gen = ZeMusicGenerator(profile, seed=42)
        notes = gen.generate(n_events=256, apply_form=True)
        
        # Анализируем сгенерированное
        analysis = ZeMusicAnalysis(name=f"Ze-{profile.name}")
        analysis.analyze(notes)
        print(analysis.summary())
    
    print(f"\n{'═'*50}")
    print("  Сравнительная таблица")
    print(f"{'═'*50}")
    print(f"{'Композитор':<12} {'v':>8} {'τ':>8} {'Z':>8} {'χ':>8} {'Расст. до v*':>12}")
    print(f"{'─'*12} {'─'*8} {'─'*8} {'─'*8} {'─'*8} {'─'*12}")
    
    results = []
    for profile in [BACH, MOZART, ORFF]:
        gen = ZeMusicGenerator(profile, seed=42)
        notes = gen.generate(n_events=256, apply_form=True)
        analysis = ZeMusicAnalysis(name=profile.name)
        analysis.analyze(notes)
        v_dist = abs(analysis.combined_stream.v - v_star)
        results.append((profile.name, analysis, v_dist))
        print(f"{profile.name:<12} {analysis.combined_stream.v:>+8.4f} "
              f"{analysis.combined_stream.tau:>8.4f} {analysis.combined_stream.Z:>8.4f} "
              f"{analysis.combined_stream.chi:>8.4f} {v_dist:>12.4f}")
    
    # Ближайший к v*
    closest = min(results, key=lambda r: r[2])
    print(f"\n★ Ближе всех к v*: {closest[0]} (расстояние {closest[2]:.4f})")


def demo_generate_midi():
    """Генерация MIDI-файлов."""
    for profile in [BACH, MOZART, ORFF]:
        gen = ZeMusicGenerator(profile, seed=42)
        notes = gen.generate(n_events=256, apply_form=True)
        filepath = f"/tmp/ze_music_{profile.name}.mid"
        gen.save_midi(filepath)
        print(f"✅ {profile.name}: {filepath} ({len(notes)} нот)")


# ============================================================
# ZE SCORE — МЕТРИКА ХИТОВОСТИ
# ============================================================

@dataclass
class ZeScore:
    """Объективная метрика хитовости (0–100) на основе Ze-параметров."""
    v: float
    tau: float
    chi: float
    zeta: float
    has_chorus_cycle: bool = False
    has_hook: bool = False
    hook_autocorr: float = 0.0
    score: float = 0.0
    grade: str = ""
    
    def compute(self) -> float:
        """Вычислить Ze Score."""
        score = 0.0
        details = []
        
        # 1. v в зоне воздействия (0.35–0.50) — 30 баллов
        v_opt = 0.425
        if 0.30 <= self.v <= 0.55:
            v_bonus = 30 * (1 - abs(self.v - v_opt) / 0.125)
            score += v_bonus
            details.append(f"v={self.v:.3f} ✅ +{v_bonus:.0f}")
        elif 0.20 <= self.v <= 0.60:
            v_bonus = 15 * (1 - abs(self.v - v_opt) / 0.175)
            score += v_bonus
            details.append(f"v={self.v:.3f} ⚠️ +{v_bonus:.0f}")
        else:
            details.append(f"v={self.v:.3f} ❌ +0")
        
        # 2. τ в окне потока (0.25–0.50) — 25 баллов
        tau_opt = 0.375
        if 0.20 <= self.tau <= 0.55:
            tau_bonus = 25 * (1 - abs(self.tau - tau_opt) / 0.175)
            score += tau_bonus
            details.append(f"τ={self.tau:.3f} ✅ +{tau_bonus:.0f}")
        elif self.tau <= 0.70:
            tau_bonus = 10
            score += tau_bonus
            details.append(f"τ={self.tau:.3f} ⚠️ +{tau_bonus:.0f}")
        else:
            details.append(f"τ={self.tau:.3f} ❌ +0 (слишком сложно)")
        
        # 3. χ для эмоциональных качелей (0.4–0.9) — 20 баллов
        chi_opt = 0.70
        if 0.35 <= self.chi <= 0.95:
            chi_bonus = 20 * (1 - abs(self.chi - chi_opt) / 0.30)
            score += chi_bonus
            details.append(f"χ={self.chi:.3f} ✅ +{chi_bonus:.0f}")
        elif self.chi > 0.95:
            chi_bonus = 10  # Орф-режим — нишевый
            score += chi_bonus
            details.append(f"χ={self.chi:.3f} ⚠️ +{chi_bonus:.0f} (Орф-режим)")
        else:
            details.append(f"χ={self.chi:.3f} ❌ +0 (слишком плоско)")
        
        # 4. Наличие T→S→T цикла (припев) — 15 баллов
        if self.has_chorus_cycle:
            score += 15
            details.append("Цикл куплет→припев ✅ +15")
        else:
            details.append("Цикл куплет→припев ❌ +0")
        
        # 5. Hook (короткий самоподобный паттерн) — 10 баллов
        if self.has_hook and self.hook_autocorr > 0.5:
            hook_bonus = 10 * min(1.0, self.hook_autocorr)
            score += hook_bonus
            details.append(f"Hook C={self.hook_autocorr:.2f} ✅ +{hook_bonus:.0f}")
        elif self.has_hook:
            score += 5
            details.append(f"Hook слабый ⚠️ +5")
        else:
            details.append("Hook ❌ +0")
        
        self.score = min(100, score)
        self._details = details
        
        # Грейд
        if self.score >= 90:
            self.grade = "★★★★★ ГАРАНТИРОВАННЫЙ ХИТ"
        elif self.score >= 75:
            self.grade = "★★★★ Очень высокий потенциал"
        elif self.score >= 60:
            self.grade = "★★★ Хороший потенциал"
        elif self.score >= 40:
            self.grade = "★★ Средний"
        elif self.score >= 20:
            self.grade = "★ Низкий"
        else:
            self.grade = "☆ Не хит"
        
        return self.score
    
    def report(self) -> str:
        """Полный отчёт."""
        if not hasattr(self, '_details'):
            self.compute()
        
        lines = [
            "╔══════════════════════════════╗",
            "║   ZE SCORE — МЕТРИКА ХИТА   ║",
            "╚══════════════════════════════╝",
            "",
            f"  Score: {self.score:.0f}/100",
            f"  Грейд: {self.grade}",
            "",
            "  Детали:",
        ]
        for d in self._details:
            lines.append(f"    {d}")
        
        lines.append("")
        lines.append(f"  Близость к v* (0.307): {abs(self.v - 0.3069):.4f}")
        lines.append(f"  Близость к v_impact (0.425): {abs(self.v - 0.425):.4f}")
        
        return "\n".join(lines)


def compute_ze_score(notes: List[Note]) -> ZeScore:
    """Вычислить Ze Score для списка нот."""
    analysis = ZeMusicAnalysis(name="target")
    analysis.analyze(notes)
    
    zs = ZeScore(
        v=analysis.combined_stream.v,
        tau=analysis.combined_stream.tau,
        chi=analysis.combined_stream.chi,
        zeta=min(analysis.combined_stream.zeta, 20.0),
    )
    
    # Проверяем hook (автокорреляция на малых лагах)
    ac = analysis.combined_stream
    if ac.N >= 8:
        zs.hook_autocorr = max(ac.autocorrelation(k) for k in [4, 8, 12] if k < ac.N)
        zs.has_hook = zs.hook_autocorr > 0.4
    
    # Проверяем цикл куплет→припев
    if len(notes) >= 64:
        sv = analysis.combined_stream.sliding_v(16)
        if len(sv) >= 4:
            v_variance = sum((x - sum(sv)/len(sv))**2 for x in sv) / len(sv)
            zs.has_chorus_cycle = v_variance > 0.03
    
    zs.compute()
    return zs


# ============================================================
# SUPERHIT PROFILE — 4-Й ПУТЬ
# ============================================================

SUPERHIT = ComposerProfile(
    name="Superhit",
    v_target=0.40,        # зона максимального воздействия
    tau_target=0.45,      # золотое окно потока
    zeta=0.40,            # гибкий импеданс
    chi=0.70,             # эмоциональные качели
    scale=[0, 2, 4, 5, 7, 9, 11],  # мажор
    tonic=0,              # C major
    voices=1,
    form="superhit",
)

PROFILES["Superhit"] = SUPERHIT


# ============================================================
# SUPERHIT GENERATOR
# ============================================================

class SuperhitGenerator:
    """
    Генератор супер-популярной музыки.
    
    Структура поп-песни:
    intro → verse → pre-chorus → CHORUS → verse2 → pre-chorus → CHORUS →
    bridge → CHORUS×2 → outro
    
    Каждая секция имеет свои Ze-параметры, создающие дофаминовый цикл.
    """
    
    # Структура поп-песни (название, такты, параметры Ze)
    POP_STRUCTURE = [
        ("Intro",       8,  {"v": 0.20, "tau": 0.20, "chi": 0.40, "vel": 70}),
        ("Verse",      16,  {"v": 0.30, "tau": 0.40, "chi": 0.55, "vel": 75}),
        ("Pre-Chorus",  8,  {"v": 0.45, "tau": 0.55, "chi": 0.70, "vel": 85}),
        ("CHORUS",     16,  {"v": 0.55, "tau": 0.35, "chi": 0.80, "vel": 100}),
        ("Verse 2",    16,  {"v": 0.32, "tau": 0.42, "chi": 0.55, "vel": 75}),
        ("Pre-Chorus",  8,  {"v": 0.48, "tau": 0.55, "chi": 0.70, "vel": 85}),
        ("CHORUS",     16,  {"v": 0.58, "tau": 0.35, "chi": 0.85, "vel": 105}),
        ("Bridge",      8,  {"v": 0.10, "tau": 0.65, "chi": 0.60, "vel": 65}),
        ("CHORUS x2",  16,  {"v": 0.65, "tau": 0.30, "chi": 0.90, "vel": 110}),
        ("Outro",       8,  {"v": 0.25, "tau": 0.20, "chi": 0.30, "vel": 60}),
    ]
    
    def __init__(self, key: str = "C", scale: str = "major", bpm: int = 120, seed: int = 42):
        self.key = key
        self.scale_name = scale
        self.bpm = bpm
        random.seed(seed)
        
        # Тональность
        KEY_MAP = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11,
                   'Cm': 0, 'Dm': 2, 'Em': 4, 'Fm': 5, 'Gm': 7, 'Am': 9, 'Bm': 11}
        self.tonic = KEY_MAP.get(key, 0)
        
        if scale == "minor" or key.endswith('m'):
            self.scale = [0, 2, 3, 5, 7, 8, 10]
        else:
            self.scale = [0, 2, 4, 5, 7, 9, 11]
        
        self._build_scale_pitches()
        
        # Состояние генератора
        self.current_pitch = 60 + self.tonic
        self.current_duration = 1.0
        self.current_velocity = 80
        self.all_notes: List[Note] = []
        self.hooks: List[List[Note]] = []
    
    def _build_scale_pitches(self):
        """Построить звукоряд."""
        self.scale_pitches = []
        base = 60 + self.tonic
        for octave in range(3):
            for step in self.scale:
                pitch = base + step + (octave * 12)
                if 21 <= pitch <= 108:
                    self.scale_pitches.append(pitch)
    
    def generate_hook(self, length: int = 8) -> List[Note]:
        """
        Сгенерировать hook — короткий, цепляющий мотив.
        Хороший hook: v ≈ 0.4, τ ≈ 0.35, высокая автокорреляция.
        """
        notes = []
        pitch = 60 + self.tonic + 7  # начинаем с квинты
        dur = 0.5
        vel = 90
        
        # Асимметричный T/S паттерн — застревает в памяти
        hook_pattern = [
            ("T", "S", 2, 10),   # T: вверх на 2 ступени
            ("T", "S", 2, 5),    # T: ещё вверх
            ("S", "T", -1, -5),  # S: небольшой спуск
            ("T", "S", 3, 8),    # T: скачок вверх (пик)
            ("S", "T", -1, -3),  # S: спуск
            ("S", "T", -1, -3),  # S: ещё спуск
            ("T", "S", 2, 5),    # T: возврат (узнавание!)
            ("S", "T", -2, -10), # S: разрешение
        ]
        
        for i, (z_p, _, step, dvel) in enumerate(hook_pattern[:length]):
            # Применить шаг
            current_idx = self._find_scale_index(pitch)
            new_idx = max(0, min(len(self.scale_pitches) - 1, current_idx + step))
            pitch = self.scale_pitches[new_idx]
            
            # Ритм: повторяющийся паттерн
            dur = 0.5 if i % 2 == 0 else 0.25
            
            # Динамика: небольшое варьирование
            vel = min(127, max(40, vel + dvel))
            
            notes.append(Note(pitch=pitch, start=0.0, duration=dur, velocity=vel))
        
        self.hooks.append(notes)
        return notes
    
    def _find_scale_index(self, pitch: int) -> int:
        """Найти ближайший индекс в звукоряде."""
        if pitch in self.scale_pitches:
            return self.scale_pitches.index(pitch)
        # Ближайший
        closest = min(self.scale_pitches, key=lambda p: abs(p - pitch))
        return self.scale_pitches.index(closest)
    
    def generate_section(self, name: str, bars: int, params: dict) -> List[Note]:
        """Сгенерировать секцию песни с заданными Ze-параметрами."""
        n_events = bars * 4  # 4 события на такт (16th notes)
        notes = []
        
        v_target = params["v"]
        tau_target = params["tau"]
        vel_base = params["vel"]
        
        # PID-контроллер для удержания v
        ze_stream = ZeStream()
        
        for i in range(n_events):
            # Текущее v
            cv = ze_stream.v
            error = v_target - cv
            
            # Вероятность T (пропорциональный контроль)
            p_t = 0.5 + 0.4 * error
            p_t = max(0.05, min(0.95, p_t))
            
            event = ZeEvent.T if random.random() < p_t else ZeEvent.S
            ze_stream.events.append(event)
            
            # Преобразовать событие в ноту
            if event == ZeEvent.T:
                step = random.choice([1, 2, 3])
            else:
                step = random.choice([-1, -2, -3])
            
            current_idx = self._find_scale_index(self.current_pitch)
            new_idx = max(0, min(len(self.scale_pitches) - 1, current_idx + step))
            self.current_pitch = self.scale_pitches[new_idx]
            
            # Ритм — в зависимости от позиции в такте
            beat_pos = i % 4
            if beat_pos == 0:
                dur = random.choice([0.5, 1.0])  # сильная доля
            elif beat_pos == 2:
                dur = 0.5  # относительно сильная
            else:
                dur = 0.25  # слабая
            
            # Динамика с вариацией
            vel = vel_base + random.randint(-15, 15)
            vel = max(20, min(127, vel))
            
            notes.append(Note(
                pitch=self.current_pitch,
                start=0.0,
                duration=dur,
                velocity=vel,
            ))
        
        return notes
    
    def generate_superhit(self) -> List[Note]:
        """Сгенерировать полную поп-песню."""
        all_notes = []
        current_time = 0.0
        
        # Сначала генерируем hook
        hook = self.generate_hook(8)
        
        print("🎵 Генерация супер-хита...")
        print(f"{'─'*50}")
        
        for name, bars, params in self.POP_STRUCTURE:
            section_notes = self.generate_section(name, bars, params)
            
            # Вставляем hook в припевы
            if "CHORUS" in name and hook:
                # Первые 8 нот припева = hook
                for j, hn in enumerate(hook):
                    if j < len(section_notes):
                        section_notes[j] = Note(
                            pitch=hn.pitch,
                            start=0.0,
                            duration=hn.duration,
                            velocity=params["vel"] + random.randint(-10, 10),
                        )
            
            # Устанавливаем времена
            section_start = current_time
            for note in section_notes:
                note.start = current_time
                current_time += note.duration
            
            section_dur = current_time - section_start
            
            # Вычисляем Ze-параметры секции
            sect_analysis = ZeMusicAnalysis(name=name)
            sect_analysis.analyze(section_notes)
            
            print(f"  {name:<14} {bars:>2} тактов | "
                  f"v={sect_analysis.combined_stream.v:+.3f} "
                  f"τ={sect_analysis.combined_stream.tau:.3f} "
                  f"| {section_dur:.1f}s")
            
            all_notes.extend(section_notes)
        
        total_dur = current_time * 60 / self.bpm
        print(f"{'─'*50}")
        print(f"  Всего: {len(all_notes)} нот, {total_dur:.0f}с (@ {self.bpm} BPM)")
        
        self.all_notes = all_notes
        return all_notes
    
    def to_midi_bytes(self, tempo: int = 120) -> bytes:
        """Экспорт в MIDI."""
        try:
            import mido
            from mido import MidiFile, MidiTrack, Message, MetaMessage
        except ImportError:
            raise ImportError("mido не установлен. pip install mido")
        
        mid = MidiFile(ticks_per_beat=480)
        mid.tracks = []
        
        # Разделяем на каналы (мелодия + бас + аккомпанемент)
        melody_notes = [n for n in self.all_notes if n.pitch >= 60]
        bass_notes = [n for n in self.all_notes if n.pitch < 48]
        chord_notes = [n for n in self.all_notes if 48 <= n.pitch < 60]
        
        for channel, (notes, name) in enumerate([
            (melody_notes, "Melody"),
            (bass_notes if bass_notes else melody_notes, "Bass"),
            (chord_notes if chord_notes else [], "Chords"),
        ]):
            if not notes:
                continue
            
            track = MidiTrack()
            mid.tracks.append(track)
            track.append(MetaMessage('set_tempo', tempo=mido.bpm2tempo(tempo)))
            track.append(MetaMessage('track_name', name=f'Ze Superhit - {name}'))
            
            ticks_per_beat = mid.ticks_per_beat
            last_time = 0
            
            for note in sorted(notes, key=lambda n: n.start):
                start_ticks = int(note.start * ticks_per_beat * tempo / 60)
                dur_ticks = int(note.duration * ticks_per_beat * tempo / 60)
                delta = start_ticks - last_time
                
                track.append(Message('note_on', note=note.pitch, 
                                    velocity=note.velocity,
                                    time=max(0, delta), channel=channel))
                track.append(Message('note_off', note=note.pitch, velocity=0,
                                    time=max(1, dur_ticks), channel=channel))
                
                last_time = start_ticks + dur_ticks
        
        import io
        buf = io.BytesIO()
        mid.save(file=buf)
        return buf.getvalue()
    
    def save_midi(self, filepath: str, tempo: int = 120):
        """Сохранить в MIDI-файл."""
        with open(filepath, 'wb') as f:
            f.write(self.to_midi_bytes(tempo))
        return filepath


# ============================================================
# GROOVE GENERATOR
# ============================================================

class GrooveGenerator:
    """
    Генератор грува — ритмического Ze-паттерна с высоким ζ.
    Грув = стабильный v_rhythm ≈ 0.40–0.45 + низкая χ.
    """
    
    GROOVE_PATTERNS = {
        "basic":    [1, 0, 1, 0, 1, 0, 1, 0],   # базовая пульсация
        "funk":     [1, 0, 0, 1, 1, 0, 0, 0],   # фанк (syncopated)
        "house":    [1, 0, 0, 0, 1, 0, 0, 0],   # four-on-the-floor
        "hiphop":   [1, 0, 0, 1, 0, 0, 1, 0],   # хип-хоп
        "dembow":   [1, 0, 0, 1, 0, 0, 0, 1],   # реггетон
        "trap":     [1, 0, 0, 1, 0, 1, 0, 0],   # трэп
    }
    
    def __init__(self, bpm: int = 120, seed: int = 42):
        self.bpm = bpm
        random.seed(seed)
    
    def generate(self, style: str = "funk", bars: int = 8, 
                 swing: float = 0.0) -> List[Note]:
        """
        Сгенерировать грув.
        
        Args:
            style: стиль грува (basic, funk, house, hiphop, dembow, trap)
            bars: количество тактов
            swing: свинг (0.0 = ровно, 0.3 = выраженный свинг)
        """
        pattern = self.GROOVE_PATTERNS.get(style, self.GROOVE_PATTERNS["funk"])
        
        notes = []
        kick_pitch = 36   # C2 — бас-бочка
        snare_pitch = 38  # D2 — малый барабан
        hat_pitch = 42    # F#2 — хай-хэт
        
        beat_dur = 60.0 / self.bpm / 2  # длительность 1/8 ноты
        
        for bar in range(bars):
            for i, hit in enumerate(pattern):
                time = (bar * len(pattern) + i) * beat_dur
                
                # Свинг: сдвиг нечётных восьмых
                if swing > 0 and i % 2 == 0:
                    time += swing * beat_dur * 0.5
                
                if hit:
                    # Выбираем звук в зависимости от позиции
                    if i == 0:
                        pitch = kick_pitch
                        vel = 100
                    elif i == 4:
                        pitch = snare_pitch
                        vel = 90
                    else:
                        pitch = hat_pitch
                        vel = 70 + random.randint(-10, 10)
                    
                    notes.append(Note(
                        pitch=pitch,
                        start=time,
                        duration=beat_dur * 0.8,
                        velocity=vel,
                    ))
                elif i % 2 == 0:
                    # Тихий хай-хэт для грува
                    notes.append(Note(
                        pitch=hat_pitch,
                        start=time,
                        duration=beat_dur * 0.3,
                        velocity=40 + random.randint(-5, 5),
                    ))
        
        return notes


# ============================================================
# HOOK GENERATOR
# ============================================================

class HookGenerator:
    """
    Генератор хуков — коротких цепляющих мотивов.
    Хороший хук: v ≈ 0.4, τ ≈ 0.35, высокая автокорреляция на лаге 4.
    """
    
    def __init__(self, key: str = "C", scale: str = "major", seed: int = 42):
        self.key = key
        self.scale_name = scale
        random.seed(seed)
        
        KEY_MAP = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11,
                   'Cm': 0, 'Dm': 2, 'Em': 4, 'Fm': 5, 'Gm': 7, 'Am': 9, 'Bm': 11}
        self.tonic = KEY_MAP.get(key, 0)
        
        if scale == "minor" or key.endswith('m'):
            self.scale = [0, 2, 3, 5, 7, 8, 10]
        else:
            self.scale = [0, 2, 4, 5, 7, 9, 11]
        
        self._build_pitches()
    
    def _build_pitches(self):
        self.pitches = []
        base = 60 + self.tonic
        for octave in range(2):
            for step in self.scale:
                pitch = base + step + (octave * 12)
                if 48 <= pitch <= 84:
                    self.pitches.append(pitch)
    
    def generate(self, length: int = 8, complexity: float = 0.5) -> List[Note]:
        """
        Сгенерировать хук.
        
        Args:
            length: длина в нотах (рекомендуется 4–8)
            complexity: сложность (0 = просто, 1 = сложно)
        """
        notes = []
        
        # Выбираем стартовый регистр
        mid = len(self.pitches) // 2
        start_idx = mid + random.randint(-3, 3)
        idx = max(0, min(len(self.pitches) - 1, start_idx))
        
        # Генерируем Ze-паттерн хука
        for i in range(length):
            # T/S баланс: ~65% T для v ≈ 0.3
            is_T = random.random() < (0.65 if complexity < 0.7 else 0.55)
            
            # Величина шага
            if complexity < 0.3:
                step_size = random.choice([1, 2])
            elif complexity < 0.7:
                step_size = random.choice([1, 2, 2, 3])
            else:
                step_size = random.choice([1, 2, 3, 4, 5])
            
            step = step_size if is_T else -step_size
            idx = max(0, min(len(self.pitches) - 1, idx + step))
            
            # Ритм: повторяющийся паттерн
            dur = 0.5 if i % 2 == 0 else 0.25
            
            # Динамика: акцент на первой ноте
            vel = 95 if i == 0 else 80 + random.randint(-10, 10)
            
            notes.append(Note(
                pitch=self.pitches[idx],
                start=0.0,
                duration=dur,
                velocity=vel,
            ))
        
        return notes


# ============================================================
# MAIN CLI
# ============================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == "generate" and len(sys.argv) > 2:
            composer = sys.argv[2]
            n_events = int(sys.argv[3]) if len(sys.argv) > 3 else 256
            output = sys.argv[4] if len(sys.argv) > 4 else f"/tmp/ze_music_{composer}.mid"
            
            if composer == "Superhit":
                gen = SuperhitGenerator(key="C", scale="major", bpm=120, 
                                       seed=random.randint(0, 10000))
                notes = gen.generate_superhit()
                gen.save_midi(output, tempo=120)
                
                # Ze Score
                zs = compute_ze_score(notes)
                print()
                print(zs.report())
                print(f"\n✅ MIDI сохранён: {output}")
            elif composer in PROFILES:
                gen = ZeMusicGenerator(PROFILES[composer], seed=random.randint(0, 10000))
                notes = gen.generate(n_events=n_events, apply_form=True)
                gen.save_midi(output)
                
                analysis = ZeMusicAnalysis(name=f"Ze-{composer}")
                analysis.analyze(notes)
                print(analysis.summary())
                
                # Ze Score
                zs = compute_ze_score(notes)
                print()
                print(zs.report())
                print(f"\n✅ MIDI сохранён: {output}")
            else:
                print(f"Неизвестный композитор: {composer}")
                print(f"Доступны: {list(PROFILES.keys())}")
        
        elif cmd == "superhit":
            key = sys.argv[2] if len(sys.argv) > 2 else "C"
            scale = sys.argv[3] if len(sys.argv) > 3 else "major"
            bpm = int(sys.argv[4]) if len(sys.argv) > 4 else 120
            output = sys.argv[5] if len(sys.argv) > 5 else "/tmp/ze_superhit.mid"
            
            gen = SuperhitGenerator(key=key, scale=scale, bpm=bpm,
                                   seed=random.randint(0, 10000))
            notes = gen.generate_superhit()
            gen.save_midi(output, tempo=bpm)
            
            zs = compute_ze_score(notes)
            print()
            print(zs.report())
            print(f"\n✅ Супер-хит сохранён: {output}")
        
        elif cmd == "hook":
            key = sys.argv[2] if len(sys.argv) > 2 else "C"
            scale = sys.argv[3] if len(sys.argv) > 3 else "major"
            complexity = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
            
            gen = HookGenerator(key=key, scale=scale, seed=random.randint(0, 10000))
            hooks = []
            for i in range(3):
                hook = gen.generate(length=8, complexity=complexity)
                analysis = ZeMusicAnalysis(name=f"Hook {i+1}")
                analysis.analyze(hook)
                hooks.append((hook, analysis))
                
                pitches_str = " ".join(f"{n.pitch:3d}" for n in hook)
                print(f"Hook {i+1}: [{pitches_str}] | "
                      f"v={analysis.combined_stream.v:+.3f} "
                      f"τ={analysis.combined_stream.tau:.3f}")
            
            # Лучший хук
            best = max(hooks, key=lambda h: h[1].combined_stream.autocorrelation(4) 
                       if h[1].combined_stream.N > 4 else 0)
            print(f"\n★ Лучший хук: v={best[1].combined_stream.v:+.3f} "
                  f"τ={best[1].combined_stream.tau:.3f} "
                  f"C(4)={best[1].combined_stream.autocorrelation(4):.3f}")
        
        elif cmd == "groove":
            style = sys.argv[2] if len(sys.argv) > 2 else "funk"
            bpm = int(sys.argv[3]) if len(sys.argv) > 3 else 120
            bars = int(sys.argv[4]) if len(sys.argv) > 4 else 8
            output = sys.argv[5] if len(sys.argv) > 5 else f"/tmp/ze_groove_{style}.mid"
            
            gen = GrooveGenerator(bpm=bpm, seed=random.randint(0, 10000))
            notes = gen.generate(style=style, bars=bars, swing=0.15)
            
            # Сохраняем через ZeMusicGenerator (для MIDI экспорта)
            tmp_profile = ComposerProfile(
                name=f"Groove-{style}", v_target=0.4, tau_target=0.3,
                zeta=0.8, chi=0.1, scale=[0], tonic=0, form="free"
            )
            tmp_gen = ZeMusicGenerator(tmp_profile, seed=42)
            tmp_gen.notes = notes
            tmp_gen.save_midi(output, tempo=bpm)
            
            analysis = ZeMusicAnalysis(name=f"Groove {style}")
            analysis.analyze(notes)
            print(f"🎵 Groove: {style} | {bars} тактов | {bpm} BPM")
            print(f"   v={analysis.combined_stream.v:+.3f} "
                  f"τ={analysis.combined_stream.tau:.3f} "
                  f"χ={analysis.combined_stream.chi:.3f}")
            print(f"\n✅ MIDI сохранён: {output}")
        
        elif cmd == "score" and len(sys.argv) > 2:
            filepath = sys.argv[2]
            notes = load_midi(filepath)
            zs = compute_ze_score(notes)
            print(zs.report())
        
        elif cmd == "analyze" and len(sys.argv) > 2:
            filepath = sys.argv[2]
            notes = load_midi(filepath)
            analysis = ZeMusicAnalysis(name=filepath)
            analysis.analyze(notes)
            print(analysis.summary())
            
            # Добавляем Ze Score
            zs = compute_ze_score(notes)
            print()
            print(zs.report())
        
        elif cmd == "demo":
            demo_analysis()
        
        elif cmd == "midi":
            demo_generate_midi()
        
        else:
            print("╔══════════════════════════════════════════════════════╗")
            print("║   Ze Music - Анализ и Генерация                     ║")
            print("║   Супер-популярная, супер-воздействующая музыка     ║")
            print("╚══════════════════════════════════════════════════════╝")
            print()
            print("Команды:")
            print()
            print("  ГЕНЕРАЦИЯ:")
            print("    superhit [key] [scale] [bpm] [output]   — супер-хит")
            print("    generate Bach 256 output.mid            — стиль композитора")
            print("    hook [key] [scale] [complexity]         — сгенерировать хуки")
            print("    groove [style] [bpm] [bars] [output]    — грув (funk/house/hiphop/trap...)")
            print()
            print("  АНАЛИЗ:")
            print("    analyze file.mid                        — полный Ze-анализ + Ze Score")
            print("    score file.mid                          — только Ze Score")
            print()
            print("  ДЕМО:")
            print("    demo                                    — анализ Бах/Моцарт/Орф")
            print("    midi                                    — сгенерировать примеры MIDI")
            print()
            print("  ДОСТУПНЫЕ СТИЛИ:")
            print(f"    Композиторы: {list(PROFILES.keys())}")
            print(f"    Грувы: {list(GrooveGenerator.GROOVE_PATTERNS.keys())}")
    else:
        demo_analysis()
