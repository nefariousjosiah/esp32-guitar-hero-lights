# ESP32 LED Reflex Game, single lane logic
# Copyright 2026 @nefariousjosiah
#
# A Lane owns one NeoPixel strip and one button. It tracks at most one
# active note at a time: where it is, whether it has reached the hit
# zone, and whether it was just hit and should flash white.

from machine import Pin
import neopixel
import time

from config import LANE_LENGTH, BRIGHTNESS, STEP_INTERVAL_MS, HIT_WINDOW_MS, FLASH_MS, OFF, WHITE


def scale(color, factor):
    return tuple(int(c * factor) for c in color)


class Lane:
    def __init__(self, name, strip_pin, button_pin, color):
        self.name = name
        self.strip = neopixel.NeoPixel(Pin(strip_pin, Pin.OUT), LANE_LENGTH)
        self.button = Pin(button_pin, Pin.IN, Pin.PULL_UP)
        self.color = scale(color, BRIGHTNESS)
        self.flash_color = scale(WHITE, BRIGHTNESS)

        self.note = None  # dict describing the active note, or None
        self.last_press_ms = 0
        self.clear()

    def clear(self):
        self.strip.fill(OFF)
        self.strip.write()

    def is_free(self):
        return self.note is None

    def spawn(self, now):
        self.note = {
            "pos": 0,
            "last_step_ms": now,
            "in_zone": False,
            "zone_enter_ms": 0,
            "flash": False,
            "flash_started": 0,
        }

    def update(self, now):
        """Advance the note one tick. Returns a short status string."""
        note = self.note
        if note is None or note["flash"]:
            return "none"

        if not note["in_zone"]:
            if time.ticks_diff(now, note["last_step_ms"]) >= STEP_INTERVAL_MS:
                note["pos"] += 1
                note["last_step_ms"] = now
                if note["pos"] >= LANE_LENGTH - 1:
                    note["pos"] = LANE_LENGTH - 1
                    note["in_zone"] = True
                    note["zone_enter_ms"] = now
            return "moving"

        if time.ticks_diff(now, note["zone_enter_ms"]) >= HIT_WINDOW_MS:
            self.note = None
            return "missed"
        return "waiting"

    def check_button(self, now, debounce_ms):
        """Poll the button. Returns 'hit', 'whiff', or None."""
        if self.button.value() != 0:  # active low, pull up
            return None
        if time.ticks_diff(now, self.last_press_ms) <= debounce_ms:
            return None
        self.last_press_ms = now

        note = self.note
        if note is not None and note["in_zone"] and not note["flash"]:
            note["flash"] = True
            note["flash_started"] = now
            return "hit"
        return "whiff"

    def tick_flash(self, now):
        note = self.note
        if note is not None and note["flash"]:
            if time.ticks_diff(now, note["flash_started"]) >= FLASH_MS:
                self.note = None

    def render(self):
        self.strip.fill(OFF)
        note = self.note
        if note is not None:
            color = self.flash_color if note["flash"] else self.color
            self.strip[note["pos"]] = color
        self.strip.write()
