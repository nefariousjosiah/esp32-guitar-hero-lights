# ESP32 LED Reflex Game, configuration
# Copyright 2026 @nefariousjosiah

LANE_LENGTH = 8          # LEDs per strip
BRIGHTNESS = 0.15        # 0.0 to 1.0, keep low so USB power is enough

STEP_INTERVAL_MS = 150   # time for a note to move one LED
HIT_WINDOW_MS = 400      # how long a note waits in the hit zone for a press
SPAWN_MIN_MS = 700       # fastest gap between new notes
SPAWN_MAX_MS = 1500      # slowest gap between new notes
DEBOUNCE_MS = 200        # button debounce window
FLASH_MS = 120           # how long the hit zone flashes white on a hit

LANES = ("blue", "green", "yellow")

STRIP_PINS = {"blue": 13, "green": 12, "yellow": 14}
BUTTON_PINS = {"blue": 32, "green": 33, "yellow": 25}

RAW_COLORS = {
    "blue": (0, 0, 255),
    "green": (0, 255, 0),
    "yellow": (255, 255, 0),
}

WHITE = (255, 255, 255)
OFF = (0, 0, 0)
