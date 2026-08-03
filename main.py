# ESP32 LED Reflex Game, entry point
# Copyright 2026 @nefariousjosiah
#
# Upload this file together with config.py, lane.py, and game.py to the
# board's root. Saving this one as main.py makes it run automatically
# on boot.

from game import Game

Game().run()
