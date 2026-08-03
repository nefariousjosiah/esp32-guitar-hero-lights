# ESP32 LED Reflex Game, main game loop
# Copyright 2026 @nefariousjosiah

import time
import random

from config import LANES, STRIP_PINS, BUTTON_PINS, RAW_COLORS, SPAWN_MIN_MS, SPAWN_MAX_MS, DEBOUNCE_MS
from lane import Lane


class Game:
    def __init__(self):
        self.lanes = {
            name: Lane(name, STRIP_PINS[name], BUTTON_PINS[name], RAW_COLORS[name])
            for name in LANES
        }
        self.score = 0
        self.misses = 0
        self.next_spawn_ms = 0

    def _maybe_spawn(self, now):
        if time.ticks_diff(now, self.next_spawn_ms) < 0:
            return
        free = [name for name, lane in self.lanes.items() if lane.is_free()]
        if free:
            self.lanes[random.choice(free)].spawn(now)
        self.next_spawn_ms = time.ticks_add(now, random.randint(SPAWN_MIN_MS, SPAWN_MAX_MS))

    def run(self):
        print("ESP32 LED reflex game starting.")
        print("Press the button matching the lane when its note reaches the last LED.")

        now0 = time.ticks_ms()
        self.next_spawn_ms = time.ticks_add(now0, 500)

        while True:
            now = time.ticks_ms()
            self._maybe_spawn(now)

            for name, lane in self.lanes.items():
                result = lane.update(now)
                if result == "missed":
                    self.misses += 1
                    print("Missed! lane=%s score=%d misses=%d" % (name, self.score, self.misses))

                outcome = lane.check_button(now, DEBOUNCE_MS)
                if outcome == "hit":
                    self.score += 1
                    print("Hit! lane=%s score=%d misses=%d" % (name, self.score, self.misses))
                elif outcome == "whiff":
                    print("Whiff on %s, nothing to hit" % name)

                lane.tick_flash(now)
                lane.render()

            time.sleep_ms(20)  # keeps CPU usage sane, buttons still feel instant
