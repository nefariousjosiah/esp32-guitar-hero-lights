# ESP32 "Guitar Hero" LED Reflex Game — MicroPython
# Copyright 2026 @nefariousjosiah
# ----------------------------------------------------
# Three lanes (blue / green / yellow), each its own short WS2812 (NeoPixel)
# strip. A colored "note" pixel starts at the top of a random lane and
# travels down toward the last LED (the hit zone). Press that lane's
# button while the note is sitting in the hit zone to score a hit.
#
# This file runs directly ON the ESP32 once MicroPython firmware is
# installed — see README_micropython.md for how to flash it and upload
# this file. No Arduino IDE needed.
#
# HARDWARE (see wiring_diagram.svg):
#   Blue strip data   -> GPIO 13
#   Green strip data  -> GPIO 12
#   Yellow strip data -> GPIO 14
#   Blue button       -> GPIO 32 (other leg to GND)
#   Green button      -> GPIO 33 (other leg to GND)
#   Yellow button     -> GPIO 25 (other leg to GND)
#   All strips: 5V -> 5V/VIN, GND -> GND
#
# Each strip is assumed to have LANE_LENGTH LEDs (default 8).

from machine import Pin
import neopixel
import time
import random

# ---------- CONFIG ----------
LANE_LENGTH = 8          # number of LEDs per strip
BRIGHTNESS = 0.15         # 0.0-1.0, keep low so USB power is enough
STEP_INTERVAL_MS = 150    # how long a note takes to move one LED
HIT_WINDOW_MS = 400       # how long a note waits in the hit zone for a press
SPAWN_MIN_MS = 700        # fastest gap between new notes
SPAWN_MAX_MS = 1500       # slowest gap between new notes
DEBOUNCE_MS = 200

LANES = ["blue", "green", "yellow"]

STRIP_PINS = {"blue": 13, "green": 12, "yellow": 14}
BUTTON_PINS = {"blue": 32, "green": 33, "yellow": 25}

RAW_COLORS = {
    "blue":   (0, 0, 255),
    "green":  (0, 255, 0),
    "yellow": (255, 255, 0),
}
WHITE = (255, 255, 255)
OFF = (0, 0, 0)


def scaled(color):
    return tuple(int(c * BRIGHTNESS) for c in color)


COLORS = {lane: scaled(c) for lane, c in RAW_COLORS.items()}
FLASH_WHITE = scaled(WHITE)

# ---------- HARDWARE SETUP ----------
strips = {lane: neopixel.NeoPixel(Pin(pin, Pin.OUT), LANE_LENGTH)
          for lane, pin in STRIP_PINS.items()}
buttons = {lane: Pin(pin, Pin.IN, Pin.PULL_UP)
           for lane, pin in BUTTON_PINS.items()}

# ---------- GAME STATE ----------
# notes_by_lane[lane] is either None or a dict:
#   {"pos": int, "last_step_ms": int, "in_zone": bool, "zone_enter_ms": int}
notes_by_lane = {lane: None for lane in LANES}
last_press_ms = {lane: 0 for lane in LANES}

score = 0
misses = 0
next_spawn_ms = 0


def clear_lane(lane):
    strips[lane].fill(OFF)
    strips[lane].write()


def render_lane(lane):
    note = notes_by_lane[lane]
    strips[lane].fill(OFF)
    if note is not None:
        color = FLASH_WHITE if note.get("flash") else COLORS[lane]
        strips[lane][note["pos"]] = color
    strips[lane].write()


def try_spawn(now):
    global next_spawn_ms
    if time.ticks_diff(now, next_spawn_ms) < 0:
        return
    # pick a lane that doesn't already have a note near the start
    free_lanes = [l for l in LANES if notes_by_lane[l] is None]
    if free_lanes:
        lane = random.choice(free_lanes)
        notes_by_lane[lane] = {
            "pos": 0,
            "last_step_ms": now,
            "in_zone": False,
            "zone_enter_ms": 0,
            "flash": False,
        }
    # schedule next spawn regardless, so a full board doesn't jam things
    next_spawn_ms = time.ticks_add(now, random.randint(SPAWN_MIN_MS, SPAWN_MAX_MS))


def update_notes(now):
    global misses
    for lane in LANES:
        note = notes_by_lane[lane]
        if note is None:
            continue

        if note["flash"]:
            # brief white "hit" flash is time-limited, handled in main loop
            continue

        if not note["in_zone"]:
            if time.ticks_diff(now, note["last_step_ms"]) >= STEP_INTERVAL_MS:
                note["pos"] += 1
                note["last_step_ms"] = now
                if note["pos"] >= LANE_LENGTH - 1:
                    note["pos"] = LANE_LENGTH - 1
                    note["in_zone"] = True
                    note["zone_enter_ms"] = now
        else:
            if time.ticks_diff(now, note["zone_enter_ms"]) >= HIT_WINDOW_MS:
                misses += 1
                print("Missed! lane=%s  score=%d  misses=%d" % (lane, score, misses))
                notes_by_lane[lane] = None


def check_buttons(now):
    global score
    for lane in LANES:
        pressed = buttons[lane].value() == 0  # active low (pull-up)
        if pressed and time.ticks_diff(now, last_press_ms[lane]) > DEBOUNCE_MS:
            last_press_ms[lane] = now
            note = notes_by_lane[lane]
            if note is not None and note["in_zone"] and not note["flash"]:
                score += 1
                note["flash"] = True
                note["flash_started"] = now
                print("HIT! lane=%s  score=%d  misses=%d" % (lane, score, misses))
            else:
                print("Whiff on %s (nothing to hit)" % lane)


def clear_finished_flashes(now):
    for lane in LANES:
        note = notes_by_lane[lane]
        if note is not None and note.get("flash"):
            if time.ticks_diff(now, note["flash_started"]) >= 120:
                notes_by_lane[lane] = None


def main():
    global next_spawn_ms
    print("Guitar Hero LED game starting...")
    print("Press the button matching the lane when its note reaches the last LED.")
    for lane in LANES:
        clear_lane(lane)

    now0 = time.ticks_ms()
    next_spawn_ms = time.ticks_add(now0, 500)

    while True:
        now = time.ticks_ms()
        try_spawn(now)
        update_notes(now)
        check_buttons(now)
        clear_finished_flashes(now)
        for lane in LANES:
            render_lane(lane)
        time.sleep_ms(20)  # small pause keeps CPU usage sane; buttons still feel instant


main()
