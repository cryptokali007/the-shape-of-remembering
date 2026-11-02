from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import soundfile as sf


ROOT = Path(__file__).resolve().parents[1] / "assets" / "audio"
SAMPLE_RATE = 48_000
DURATION = 300
CHANNELS = 2
BLOCK_SECONDS = 5
BLOCK_FRAMES = SAMPLE_RATE * BLOCK_SECONDS
FLOAT_PATH = ROOT / "score-float-work.wav"
WAV_PATH = ROOT / "score.wav"
FEATURES_PATH = ROOT / "score-features.json"
REPORT_PATH = ROOT / "SCORE_REPORT.md"

# The section boundaries follow the film's dramatic beats.  The gain, tempo,
# pulse, and color each change at the listed start time, then settle smoothly.
SECTIONS = [
    {"start": 0, "end": 20, "name": "signal and stakes", "level": 0.40, "bpm": 0, "kick_every": 0, "kick": 0.0, "arp_beats": 3.8, "arp": 0.36, "air": 0.35},
    {"start": 20, "end": 35, "name": "inherited method", "level": 0.49, "bpm": 72, "kick_every": 4, "kick": 0.13, "arp_beats": 1.8, "arp": 0.43, "air": 0.40},
    {"start": 35, "end": 65, "name": "genuine recall", "level": 0.64, "bpm": 82, "kick_every": 2, "kick": 0.15, "arp_beats": 1.0, "arp": 0.64, "air": 0.50},
    {"start": 65, "end": 80, "name": "Walrus blob", "level": 0.57, "bpm": 76, "kick_every": 4, "kick": 0.14, "arp_beats": 1.0, "arp": 0.55, "air": 0.70},
    {"start": 80, "end": 110, "name": "encoding", "level": 0.70, "bpm": 88, "kick_every": 2, "kick": 0.17, "arp_beats": 0.75, "arp": 0.67, "air": 0.56},
    {"start": 110, "end": 140, "name": "distribution", "level": 0.82, "bpm": 96, "kick_every": 2, "kick": 0.20, "arp_beats": 0.5, "arp": 0.78, "air": 0.70},
    {"start": 140, "end": 170, "name": "coordination chamber", "level": 0.57, "bpm": 72, "kick_every": 4, "kick": 0.11, "arp_beats": 1.5, "arp": 0.43, "air": 0.82},
    {"start": 170, "end": 200, "name": "application meaning", "level": 0.70, "bpm": 84, "kick_every": 2, "kick": 0.15, "arp_beats": 0.75, "arp": 0.66, "air": 0.58},
    {"start": 200, "end": 215, "name": "managed memory and access", "level": 0.79, "bpm": 92, "kick_every": 2, "kick": 0.20, "arp_beats": 0.5, "arp": 0.70, "air": 0.62},
    {"start": 215, "end": 230, "name": "deterministic world", "level": 0.52, "bpm": 88, "kick_every": 4, "kick": 0.12, "arp_beats": 1.0, "arp": 0.48, "air": 0.45},
    {"start": 230, "end": 260, "name": "evidence gallery", "level": 0.65, "bpm": 94, "kick_every": 2, "kick": 0.15, "arp_beats": 0.75, "arp": 0.65, "air": 0.68},
    {"start": 260, "end": 275, "name": "applications", "level": 0.77, "bpm": 100, "kick_every": 2, "kick": 0.17, "arp_beats": 0.5, "arp": 0.74, "air": 0.80},
    {"start": 275, "end": 289, "name": "architectural crescendo", "level": 0.96, "bpm": 110, "kick_every": 1, "kick": 0.23, "arp_beats": 0.5, "arp": 0.91, "air": 1.0},
    {"start": 289, "end": 300, "name": "warm return and credits", "level": 0.53, "bpm": 0, "kick_every": 0, "kick": 0.0, "arp_beats": 2.5, "arp": 0.20, "air": 0.38},
]
BOUNDARIES = [s["start"] for s in SECTIONS[1:]]

# All harmony belongs to one gently shifting D-minor / F-major palette.  The
# long chords let the score breathe under narration; a recurring D-F-A-D-C-A-F
# contour gives the film a recognizable musical memory.
CHORD_DATA = [
    (0, "Dm(add9)", [38, 45, 50, 53, 57, 62, 64]),
    (10, "Bbmaj7", [34, 41, 46, 50, 53, 57, 62]),
    (20, "F(add9)", [29, 41, 48, 53, 57, 60, 64, 67]),
    (27, "C/E", [40, 48, 52, 55, 60, 64, 67]),
    (35, "Dm11", [38, 45, 50, 53, 57, 60, 64]),
    (45, "Gm9", [31, 43, 50, 53, 57, 62, 65]),
    (55, "C(add9)", [36, 43, 48, 50, 55, 60, 62, 64]),
    (65, "Bbmaj9", [34, 41, 46, 50, 53, 57, 60, 62]),
    (72, "F/A", [33, 45, 48, 53, 57, 60, 64, 67]),
    (80, "Dm9", [38, 45, 50, 53, 57, 60, 62, 64]),
    (90, "C/E", [40, 48, 52, 55, 60, 64, 67]),
    (100, "Bbmaj7", [34, 41, 46, 50, 53, 57, 62]),
    (110, "Fmaj9", [29, 41, 48, 53, 57, 60, 64, 67]),
    (120, "C(add9)", [36, 43, 48, 50, 55, 60, 64]),
    (130, "Dm9", [38, 45, 50, 53, 57, 60, 62, 64]),
    (140, "Gm11", [31, 43, 50, 53, 57, 60, 62, 65]),
    (150, "Bbmaj7", [34, 41, 46, 50, 53, 57, 62]),
    (160, "F(add9)", [29, 41, 48, 53, 57, 60, 64, 67]),
    (170, "Dm9", [38, 45, 50, 53, 57, 60, 62, 64]),
    (180, "Gm9", [31, 43, 50, 53, 57, 62, 65]),
    (190, "Bbmaj7", [34, 41, 46, 50, 53, 57, 62]),
    (200, "Dm/A", [45, 50, 53, 57, 60, 62, 65]),
    (207, "C(add9)", [36, 43, 48, 50, 55, 60, 64]),
    (215, "Fmaj9", [29, 41, 48, 53, 57, 60, 64, 67]),
    (222, "Bbmaj7", [34, 41, 46, 50, 53, 57, 62]),
    (230, "Dm9", [38, 45, 50, 53, 57, 60, 62, 64]),
    (240, "C(add9)", [36, 43, 48, 50, 55, 60, 64]),
    (250, "Bbmaj7", [34, 41, 46, 50, 53, 57, 62]),
    (260, "Fmaj9", [29, 41, 48, 53, 57, 60, 64, 67]),
    (268, "C(add9)", [36, 43, 48, 50, 55, 60, 64]),
    (275, "Bbmaj9", [34, 41, 46, 50, 53, 57, 60, 62]),
    (280, "Fmaj9", [29, 41, 48, 53, 57, 60, 64, 67]),
    (285, "C(add9)", [36, 43, 48, 50, 55, 60, 64]),
    (289, "F6(add9)", [41, 48, 53, 55, 57, 60, 62, 64, 67]),
]
CHORDS = [
    {"start": float(item[0]), "end": float(CHORD_DATA[i + 1][0] if i + 1 < len(CHORD_DATA) else DURATION),
     "name": item[1], "notes": item[2]}
    for i, item in enumerate(CHORD_DATA)
]
CHORD_STARTS = np.array([c["start"] for c in CHORDS], dtype=np.float64)


def midi_hz(note: float) -> float:
    return 440.0 * (2.0 ** ((float(note) - 69.0) / 12.0))


def section_levels(times: np.ndarray) -> np.ndarray:
    starts = np.array([s["start"] for s in SECTIONS])
    levels = np.array([s["level"] for s in SECTIONS])
    ids = np.clip(np.searchsorted(starts, times, side="right") - 1, 0, len(SECTIONS) - 1)
    result = levels[ids].astype(np.float64, copy=True)
    # A transition begins at each exact boundary and settles over 1.7 sec.
    for i, boundary in enumerate(starts[1:], start=1):
        mask = (times >= boundary) & (times < boundary + 1.7)
        if np.any(mask):
            x = np.clip((times[mask] - boundary) / 1.7, 0.0, 1.0)
            mix = 0.5 - 0.5 * np.cos(np.pi * x)
            result[mask] = levels[i - 1] * (1.0 - mix) + levels[i] * mix
    return result


def section_index(t: float) -> int:
    return max(0, min(len(SECTIONS) - 1, int(np.searchsorted([s["start"] for s in SECTIONS], t, side="right") - 1)))


def make_events() -> tuple[list[tuple], list[tuple], list[tuple], list[tuple]]:
    kicks: list[tuple] = []
    plucks: list[tuple] = []
    ticks: list[tuple] = []
    snares: list[tuple] = []
    motif = (62, 65, 69, 74, 72, 69, 65, 69)
    event_id = 0

    for si, sec in enumerate(SECTIONS):
        if sec["bpm"] == 0:
            # A few exposed notes establish the shape before the pulse exists.
            sparse_notes = ((0.45, 62), (5.3, 65), (11.4, 69), (18.0, 74)) if sec["start"] == 0 else ((289.18, 64), (292.4, 67))
            for j, (onset, note) in enumerate(sparse_notes):
                plucks.append((onset, note, 0.48, event_id, -0.28 + 0.18 * j, "motif"))
                event_id += 1
            continue
        beat = 60.0 / sec["bpm"]
        count = 0
        onset = sec["start"] + 0.06
        while onset < sec["end"] - 0.12:
            if sec["kick_every"] and count % sec["kick_every"] == 0:
                accent = 1.0 if count % 4 == 0 else 0.68
                kicks.append((onset, sec["kick"] * accent, count, si))
            if sec["kick_every"] and count % 4 == 2 and sec["kick"] >= 0.17:
                snares.append((onset, 0.075 if sec["start"] < 275 else 0.12, count, si))
            if sec["start"] >= 65 and count % 2 == 1 and sec["air"] > 0.55:
                ticks.append((onset + beat * 0.5, 0.14 + 0.08 * sec["air"], event_id))
                event_id += 1
            count += 1
            onset = sec["start"] + 0.06 + count * beat

        step = beat * sec["arp_beats"]
        n = 0
        onset = sec["start"] + (0.36 if si in (1, 3, 6, 9) else 0.12)
        while onset < min(sec["end"] - 0.15, 289.0):
            ci = int(np.clip(np.searchsorted(CHORD_STARTS, onset, side="right") - 1, 0, len(CHORDS) - 1))
            chord = CHORDS[ci]
            # The recurring contour is interleaved with chord tones so the
            # phrase changes color with the harmony while keeping its identity.
            note = motif[n % len(motif)]
            if n % 3 == 1:
                chord_pitches = [x for x in chord["notes"] if 53 <= x <= 74]
                if chord_pitches:
                    note = chord_pitches[(n // 3) % len(chord_pitches)] + (12 if n % 2 else 0)
            velocity = sec["arp"] * (0.84 if n % 4 else 1.0)
            pan = 0.56 * math.sin(onset * 0.091 + event_id * 0.71)
            plucks.append((onset, note, velocity, event_id, pan, "motif" if n % 3 else "glass"))
            event_id += 1
            n += 1
            onset = sec["start"] + (0.36 if si in (1, 3, 6, 9) else 0.12) + n * step

    return tuple(sorted(kicks)), tuple(sorted(plucks)), tuple(sorted(ticks)), tuple(sorted(snares))


KICKS, PLUCKS, TICKS, SNARES = make_events()
KICK_TIMES = np.array([e[0] for e in KICKS], dtype=np.float64)
PLUCK_TIMES = np.array([e[0] for e in PLUCKS], dtype=np.float64)
TICK_TIMES = np.array([e[0] for e in TICKS], dtype=np.float64)
SNARE_TIMES = np.array([e[0] for e in SNARES], dtype=np.float64)


def add_strings(y: np.ndarray, times: np.ndarray) -> None:
    for ci, chord in enumerate(CHORDS):
        mask = (times >= chord["start"]) & (times < chord["end"])
        if not np.any(mask):
            continue
        tt = times[mask]
        elapsed = tt - chord["start"]
        remaining = chord["end"] - tt
        attack = np.sin(0.5 * np.pi * np.clip(elapsed / 2.1, 0.0, 1.0))
        release = np.sin(0.5 * np.pi * np.clip(remaining / 2.4, 0.0, 1.0))
        breath = 0.91 + 0.09 * np.sin(2.0 * np.pi * (0.105 + 0.003 * (ci % 4)) * tt + ci * 0.37)
        env = np.minimum(attack, release) * breath
        for j, midi in enumerate(chord["notes"]):
            f = midi_hz(midi)
            amp = 0.032 if f < 165 else (0.033 if f < 520 else (0.023 if f < 1050 else 0.013))
            vibrato = 0.0034 * np.sin(2.0 * np.pi * (0.16 + j * 0.006) * tt + j * 0.81)
            fl = f * (0.99925 + 0.000035 * j)
            fr = f * (1.00075 - 0.00003 * j)
            left_phase = 2.0 * np.pi * fl * tt + vibrato
            right_phase = 2.0 * np.pi * fr * tt + vibrato + 0.18
            left = np.sin(left_phase) + 0.18 * np.sin(2.0 * left_phase + 0.16) + 0.045 * np.sin(3.0 * left_phase + 0.4)
            right = np.sin(right_phase) + 0.18 * np.sin(2.0 * right_phase + 0.25) + 0.045 * np.sin(3.0 * right_phase + 0.53)
            y[mask, 0] += amp * env * left
            y[mask, 1] += amp * env * right


def add_pluck(y: np.ndarray, block_start: float, event: tuple) -> None:
    onset, midi, velocity, eid, pan, color = event
    duration = 1.65 if color == "motif" else 1.25
    i = max(0, int(math.floor((onset - block_start) * SAMPLE_RATE)))
    j = min(len(y), int(math.ceil((onset + duration - block_start) * SAMPLE_RATE)))
    if i >= j:
        return
    u = block_start + np.arange(i, j, dtype=np.float64) / SAMPLE_RATE - onset
    f = midi_hz(midi + (0.012 if eid % 2 else -0.009))
    attack = 1.0 - np.exp(-u * 210.0)
    env = attack * np.exp(-u * (2.45 if color == "motif" else 3.0))
    phase = 2.0 * np.pi * f * u
    fundamental = np.sin(phase)
    shimmer = 0.31 * np.exp(-u * 5.2) * np.sin(2.013 * phase + 0.17)
    tine = (0.095 if color == "glass" else 0.055) * np.exp(-u * 8.0) * np.sin(4.07 * phase + 0.39)
    tone = (fundamental + shimmer + tine) * env
    transient = 0.06 * np.exp(-u * 95.0) * np.sin(2.0 * np.pi * (f * 2.8) * u)
    amp = (0.084 if color == "motif" else 0.072) * velocity
    left_gain = math.sqrt(max(0.0, 1.0 - 0.48 * pan))
    right_gain = math.sqrt(max(0.0, 1.0 + 0.48 * pan))
    y[i:j, 0] += amp * left_gain * (tone + transient)
    y[i:j, 1] += amp * right_gain * (tone + 0.88 * transient)


def add_kick(y: np.ndarray, block_start: float, event: tuple) -> None:
    onset, strength, beat_no, si = event
    if strength <= 0:
        return
    i = max(0, int((onset - block_start) * SAMPLE_RATE))
    j = min(len(y), int(math.ceil((onset + 0.42 - block_start) * SAMPLE_RATE)))
    if i >= j:
        return
    u = block_start + np.arange(i, j, dtype=np.float64) / SAMPLE_RATE - onset
    phase = 2.0 * np.pi * (47.0 * u + 2.8 * (1.0 - np.exp(-22.0 * u)))
    body = np.exp(-8.6 * u) * np.sin(phase)
    click = np.exp(-78.0 * u) * np.sin(2.0 * np.pi * 156.0 * u)
    value = strength * (0.49 * body + 0.08 * click)
    y[i:j, 0] += value
    y[i:j, 1] += value


def add_snare(y: np.ndarray, block_start: float, event: tuple, noise: np.ndarray) -> None:
    onset, strength, beat_no, si = event
    i = max(0, int((onset - block_start) * SAMPLE_RATE))
    j = min(len(y), int(math.ceil((onset + 0.24 - block_start) * SAMPLE_RATE)))
    if i >= j:
        return
    u = block_start + np.arange(i, j, dtype=np.float64) / SAMPLE_RATE - onset
    n0 = max(0, i)
    burst = noise[n0:j]
    tone = np.sin(2.0 * np.pi * (112.0 - 21.0 * u) * u + 0.3)
    value = strength * (0.23 * np.exp(-u * 23.0) * burst + 0.13 * np.exp(-u * 17.0) * tone)
    pan = -0.12 if beat_no % 4 == 2 else 0.12
    y[i:j, 0] += value * (1.0 - pan)
    y[i:j, 1] += value * (1.0 + pan)


def add_tick(y: np.ndarray, block_start: float, event: tuple) -> None:
    onset, velocity, eid = event
    i = max(0, int((onset - block_start) * SAMPLE_RATE))
    j = min(len(y), int(math.ceil((onset + 0.075 - block_start) * SAMPLE_RATE)))
    if i >= j:
        return
    u = block_start + np.arange(i, j, dtype=np.float64) / SAMPLE_RATE - onset
    f = 1320.0 + 110.0 * math.sin(eid * 1.71)
    strike = np.exp(-u * 68.0) * np.sin(2.0 * np.pi * f * u + 0.2)
    ring = 0.36 * np.exp(-u * 34.0) * np.sin(2.0 * np.pi * f * 2.73 * u + 0.61)
    pan = 0.58 * math.sin(eid * 0.83)
    val = 0.018 * velocity * (strike + ring)
    y[i:j, 0] += val * (1.0 - pan)
    y[i:j, 1] += val * (1.0 + pan)


def add_transitions(y: np.ndarray, times: np.ndarray, filtered_noise: np.ndarray) -> None:
    for idx, boundary in enumerate(BOUNDARIES):
        # A rising breath of filtered air resolves into a tiny glass impact on
        # the cut, making transitions tactile without turning into a trailer hit.
        u = times - (boundary - 1.65)
        mask = (u >= 0.0) & (u < 1.65)
        if np.any(mask):
            x = np.clip(u[mask] / 1.65, 0.0, 1.0)
            env = np.sin(0.5 * np.pi * x) ** 1.7
            phase = 2.0 * np.pi * (320.0 + 470.0 * x) * u[mask]
            shimmer = 0.0085 * env * np.sin(phase + idx * 0.31)
            air = 0.013 * env * filtered_noise[mask]
            y[mask, 0] += shimmer + air
            y[mask, 1] += 0.91 * shimmer - 0.88 * air
        hit = (times >= boundary) & (times < boundary + 0.095)
        if np.any(hit):
            local = times[hit] - boundary
            env = np.exp(-local * 54.0)
            f = 870.0 + 95.0 * (idx % 5)
            hit_tone = 0.015 * env * np.sin(2.0 * np.pi * f * local + idx * 0.2)
            y[hit, 0] += hit_tone
            y[hit, 1] += 0.83 * hit_tone


def add_echo(dry: np.ndarray, history: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    ext = np.concatenate((history, dry), axis=0)
    n = len(dry)
    base = len(history)
    wet = dry.copy()
    taps = ((0.19, 0.12), (0.31, 0.09), (0.47, 0.065), (0.63, 0.045))
    for delay, gain in taps:
        d = int(delay * SAMPLE_RATE)
        past = ext[base - d:base - d + n]
        wet[:, 0] += gain * past[:, 1]
        wet[:, 1] += gain * past[:, 0]
    return wet, ext[-len(history):].copy()


def fade_envelope(times: np.ndarray) -> np.ndarray:
    x = np.clip((times - 289.0) / 10.8, 0.0, 1.0)
    return np.where(times >= 299.8, 0.0, np.cos(0.5 * np.pi * x))


def synthesize() -> None:
    rng = np.random.default_rng(20261022)
    echo_history = np.zeros((int(0.66 * SAMPLE_RATE) + 2, CHANNELS), dtype=np.float64)
    noise_envelope_times = np.arange(-2.0, DURATION + 2.1, 1.25)
    envelope_raw = rng.normal(size=len(noise_envelope_times))
    kernel_x = np.arange(-12, 13, dtype=np.float64)
    envelope_kernel = np.exp(-0.5 * (kernel_x / 4.0) ** 2)
    envelope_kernel /= envelope_kernel.sum()
    padded = np.pad(envelope_raw, (12, 12), mode="reflect")
    noise_envelope_values = np.convolve(padded, envelope_kernel, mode="valid")

    with sf.SoundFile(FLOAT_PATH, mode="w", samplerate=SAMPLE_RATE, channels=CHANNELS, subtype="FLOAT", format="WAV") as out:
        for frame_start in range(0, DURATION * SAMPLE_RATE, BLOCK_FRAMES):
            count = min(BLOCK_FRAMES, DURATION * SAMPLE_RATE - frame_start)
            block_start = frame_start / SAMPLE_RATE
            times = block_start + np.arange(count, dtype=np.float64) / SAMPLE_RATE
            y = np.zeros((count, CHANNELS), dtype=np.float64)

            add_strings(y, times)

            # Quiet filtered air creates depth and movement in the stereo field.
            # Interpolated seeded noise keeps the air texture soft and avoids
            # needing external filter binaries in the assigned read-only runtime.
            reduced_count = (count + 3) // 4
            source_positions = np.arange(reduced_count, dtype=np.float64) * 4.0
            target_positions = np.arange(count, dtype=np.float64)
            raw_l = rng.standard_normal(reduced_count)
            raw_r = rng.standard_normal(reduced_count)
            noise_l = np.interp(target_positions, source_positions, raw_l)
            noise_r = np.interp(target_positions, source_positions, raw_r)
            noise_l -= 0.54 * np.roll(noise_l, 1)
            noise_r -= 0.54 * np.roll(noise_r, 1)
            air = np.interp(times, noise_envelope_times, noise_envelope_values)
            sec_ids = np.searchsorted([s["start"] for s in SECTIONS], times, side="right") - 1
            sec_ids = np.clip(sec_ids, 0, len(SECTIONS) - 1)
            air_amount = np.array([SECTIONS[k]["air"] for k in sec_ids])
            y[:, 0] += (0.0016 + air_amount * 0.0021) * noise_l + 0.00045 * air
            y[:, 1] += (0.0016 + air_amount * 0.0021) * noise_r + 0.00041 * air
            filtered_noise = 0.5 * (noise_l + noise_r)

            for event in PLUCKS[np.searchsorted(PLUCK_TIMES, block_start - 1.7):np.searchsorted(PLUCK_TIMES, block_start + count / SAMPLE_RATE)]:
                add_pluck(y, block_start, event)
            for event in KICKS[np.searchsorted(KICK_TIMES, block_start - 0.45):np.searchsorted(KICK_TIMES, block_start + count / SAMPLE_RATE)]:
                add_kick(y, block_start, event)
            for event in SNARES[np.searchsorted(SNARE_TIMES, block_start - 0.25):np.searchsorted(SNARE_TIMES, block_start + count / SAMPLE_RATE)]:
                add_snare(y, block_start, event, filtered_noise)
            for event in TICKS[np.searchsorted(TICK_TIMES, block_start - 0.09):np.searchsorted(TICK_TIMES, block_start + count / SAMPLE_RATE)]:
                add_tick(y, block_start, event)

            add_transitions(y, times, filtered_noise)
            y *= section_levels(times)[:, None]
            y, echo_history = add_echo(y, echo_history)
            y *= fade_envelope(times)[:, None]
            out.write(y.astype(np.float32))


def render_pcm24() -> tuple[float, float]:
    peak = 0.0
    channel_sums = np.zeros(CHANNELS, dtype=np.float64)
    frames = 0
    with sf.SoundFile(FLOAT_PATH, mode="r") as src:
        while True:
            block = src.read(BLOCK_FRAMES, dtype="float64", always_2d=True)
            if not len(block):
                break
            peak = max(peak, float(np.max(np.abs(block))))
            channel_sums += block.sum(axis=0)
            frames += len(block)
    if peak <= 0.0:
        raise RuntimeError("Empty score render")
    gain = (10.0 ** (-3.0 / 20.0)) / peak
    with sf.SoundFile(FLOAT_PATH, mode="r") as src, sf.SoundFile(WAV_PATH, mode="w", samplerate=SAMPLE_RATE, channels=CHANNELS, subtype="PCM_24", format="WAV") as dst:
        while True:
            block = src.read(BLOCK_FRAMES, dtype="float64", always_2d=True)
            if not len(block):
                break
            dst.write((block * gain).astype(np.float32))
    return peak, gain


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def analyze() -> dict:
    info = sf.info(WAV_PATH)
    expected = (SAMPLE_RATE, CHANNELS, DURATION * SAMPLE_RATE, "PCM_24")
    actual = (info.samplerate, info.channels, info.frames, info.subtype)
    if actual != expected:
        raise RuntimeError(f"Unexpected WAV format: {actual}; expected {expected}")

    window_samples = SAMPLE_RATE // 20
    if BLOCK_FRAMES % window_samples:
        raise RuntimeError("Analysis block must contain whole feature windows")
    window = np.hanning(window_samples)
    frequencies = np.fft.rfftfreq(window_samples, 1.0 / SAMPLE_RATE)
    band_masks = (
        (frequencies >= 20) & (frequencies < 180),
        (frequencies >= 180) & (frequencies < 2400),
        (frequencies >= 2400) & (frequencies <= 12_000),
    )
    one_sided = np.full(len(frequencies), 2.0)
    one_sided[0] = 1.0
    if window_samples % 2 == 0:
        one_sided[-1] = 1.0
    power_scale = one_sided / (window_samples * np.sum(window * window))

    rms: list[float] = []
    bands = [[], [], []]
    per_section: dict[str, list[float]] = {sec["name"]: [] for sec in SECTIONS}
    peak = 0.0
    dc = np.zeros(CHANNELS, dtype=np.float64)
    total_frames = 0
    tail_peak = 0.0
    tail_start = int(299.8 * SAMPLE_RATE)

    with sf.SoundFile(WAV_PATH, mode="r") as stream:
        frame_position = 0
        while True:
            stereo = stream.read(BLOCK_FRAMES, dtype="float64", always_2d=True)
            if not len(stereo):
                break
            peak = max(peak, float(np.max(np.abs(stereo))))
            dc += np.sum(stereo, axis=0)
            total_frames += len(stereo)
            if frame_position + len(stereo) > tail_start:
                tail = stereo[max(0, tail_start - frame_position):]
                if len(tail):
                    tail_peak = max(tail_peak, float(np.max(np.abs(tail))))
            mono = np.mean(stereo, axis=1)
            frames = mono.reshape(-1, window_samples)
            frame_rms = np.sqrt(np.mean(frames * frames, axis=1))
            spectrum = np.fft.rfft(frames * window[None, :], axis=1)
            power = (np.abs(spectrum) ** 2) * power_scale[None, :]
            rms.extend(frame_rms.tolist())
            for band_id, mask in enumerate(band_masks):
                bands[band_id].extend(np.sqrt(np.sum(power[:, mask], axis=1)).tolist())
            offset = frame_position // window_samples
            for i, value in enumerate(frame_rms):
                center = (offset + i + 0.5) / 20.0
                per_section[SECTIONS[section_index(center)]["name"]].append(float(value * value))
            frame_position += len(stereo)

    dc /= total_frames
    section_rms = {name: float(np.sqrt(np.mean(values))) if values else 0.0 for name, values in per_section.items()}
    overall_rms = float(np.sqrt(np.mean(np.square(rms))))
    if len(rms) != 6000 or any(len(values) != 6000 for values in bands):
        raise RuntimeError("20 Hz feature arrays must each contain exactly 6,000 values")
    if not np.all(np.isfinite(np.asarray(rms))) or any(not np.all(np.isfinite(np.asarray(v))) for v in bands):
        raise RuntimeError("Non-finite feature data")
    if peak >= 1.0 or peak > 10.0 ** (-2.8 / 20.0):
        raise RuntimeError(f"Clipping or peak ceiling failure: {peak:.8f}")
    if np.max(np.abs(dc)) > 0.0002:
        raise RuntimeError(f"DC offset exceeds limit: {dc.tolist()}")
    if tail_peak > 1.0 / (2**23):
        raise RuntimeError(f"Audio is not silent from 299.8 seconds: {tail_peak:.10g}")
    if any(section_rms[s["name"]] < 0.003 for s in SECTIONS[:-1]):
        raise RuntimeError("A dramatic section is unexpectedly inactive")

    feature_data = {
        "source": "Decoded finished score.wav PCM_24",
        "sample_rate_hz": SAMPLE_RATE,
        "channels": CHANNELS,
        "duration_seconds": DURATION,
        "feature_rate_hz": 20,
        "window_samples": window_samples,
        "band_ranges_hz": {"low": [20, 180], "mid": [180, 2400], "high": [2400, 12000]},
        "times_seconds": [round((i + 0.5) / 20.0, 3) for i in range(6000)],
        "rms": [round(float(x), 8) for x in rms],
        "low_rms": [round(float(x), 8) for x in bands[0]],
        "mid_rms": [round(float(x), 8) for x in bands[1]],
        "high_rms": [round(float(x), 8) for x in bands[2]],
        "section_rms": {k: round(v, 8) for k, v in section_rms.items()},
    }
    FEATURES_PATH.write_text(json.dumps(feature_data, separators=(",", ":")), encoding="utf-8")

    return {
        "info": info,
        "peak": peak,
        "dc": dc,
        "tail_peak": tail_peak,
        "overall_rms": overall_rms,
        "section_rms": section_rms,
        "feature_data": feature_data,
    }


def write_report(float_peak: float, gain: float, result: dict) -> None:
    info = result["info"]
    peak = result["peak"]
    section_rms = result["section_rms"]
    wav_hash = sha256(WAV_PATH)
    feature_hash = sha256(FEATURES_PATH)
    script_hash = sha256(Path(__file__))
    lines = [
        "# The Shape of Remembering — original score",
        "",
        "A five-minute original stereo score composed and rendered from deterministic NumPy/SciPy synthesis. The sound is authored from oscillators, filtered noise, event-driven percussion, a recurring melodic contour, and short stereo reflections; no sample packs, existing songs, downloads, cloud generators, or paid media were used.",
        "",
        "## Musical arc",
        "",
        "The opening holds close to a low D-minor field. A four-note glass motif appears with long pauses, then grows into a repeating seven-note line as the inherited method and genuine recall emerge. Each film chapter has its own pulse density and air: the blob passage opens into ringing space, encoding and distribution increase the mallet subdivisions, and the coordination chamber strips back the low beat. The ribbon-studio passage returns with a firmer bass pulse; the deterministic-world cut drops the arrangement to expose the next image. The evidence gallery warms into a steady, clear pattern. Applications broaden the strings, the 275-second section gathers bass, ticks, and brighter harmonics for the peak, and the 289-second F6/add9 cadence returns to the opening's intimacy before the 299.8-second silence.",
        "",
        "The bowed-string-like bed uses slow detuning and breath modulation. Soft low pulses, close mallet attacks, occasional wood and glass ticks, filtered transition breaths, and restrained echoes provide tactile motion. The middle register remains open for af_heart narration. This is the unducked music stem; narration ducking is a parent-stage operation.",
        "",
        "Section changes begin at the exact requested times: 0, 20, 35, 65, 80, 110, 140, 170, 200, 215, 230, 260, 275, and 289 seconds. The final fade runs from 289 seconds and is silent from 299.8 seconds onward.",
        "",
        "## Signal validation",
        "",
        f"- Finished WAV: {info.samplerate} Hz, {info.channels} channels, {info.subtype}, {info.frames:,} frames, {info.duration:.3f} seconds.",
        f"- Float mix peak before final gain: {float_peak:.8f}; applied uniform gain: {gain:.8f} ({20 * math.log10(gain):.2f} dB).",
        f"- Encoded peak: {peak:.8f} ({20 * math.log10(peak):.2f} dBFS); samples at full scale: 0.",
        f"- Encoded channel DC: [{result['dc'][0]:.10g}, {result['dc'][1]:.10g}].",
        f"- Maximum absolute sample from 299.8–300.0 seconds: {result['tail_peak']:.10g}.",
        f"- Overall RMS from 20 Hz feature windows: {result['overall_rms']:.8f}.",
        "- Feature data was measured from decoded PCM_24 audio at 20 Hz; low/mid/high arrays each contain exactly 6,000 samples.",
        "",
        "## Section RMS",
        "",
    ]
    for sec in SECTIONS:
        lines.append(f"- {sec['start']:g}–{sec['end']:g}s, {sec['name']}: {section_rms[sec['name']]:.6f}")
    lines.extend([
        "",
        "## SHA-256",
        "",
        f"- `score.wav`: `{wav_hash}`",
        f"- `score-features.json`: `{feature_hash}`",
        f"- `generate_score.py`: `{script_hash}`",
        "",
        "Generation is reproducible with the included script and the provided Python runtime with NumPy, SciPy, and SoundFile.",
        "",
    ])
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    synthesize()
    float_peak, gain = render_pcm24()
    result = analyze()
    write_report(float_peak, gain, result)
    FLOAT_PATH.unlink(missing_ok=True)
    info = result["info"]
    print(json.dumps({
        "score_wav": str(WAV_PATH),
        "features": str(FEATURES_PATH),
        "report": str(REPORT_PATH),
        "frames": info.frames,
        "duration_seconds": info.duration,
        "subtype": info.subtype,
        "peak_dbfs": round(20.0 * math.log10(result["peak"]), 4),
        "dc": result["dc"].tolist(),
        "tail_peak_after_299_8s": result["tail_peak"],
        "feature_rate_hz": result["feature_data"]["feature_rate_hz"],
        "feature_samples": len(result["feature_data"]["low_rms"]),
        "wav_sha256": sha256(WAV_PATH),
        "section_rms": {k: round(v, 6) for k, v in result["section_rms"].items()},
    }, indent=2))


if __name__ == "__main__":
    main()
