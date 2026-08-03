# ESP32 LED Reflex Game (MicroPython)

Copyright 2026 @nefariousjosiah

This is a 3 lane reflex game. A colored note starts at the far end of each lane and travels toward the ESP32. Press the matching button when it reaches the last LED to score a hit.

It runs in MicroPython instead of Arduino C++, so you write plain Python in `main.py` and it runs directly on the board.

## Is MicroPython a problem for a beginner

Not really. If anything it's easier than Arduino C++. The only extra step is a one time firmware flash: before you can run Python on the board, you replace its default firmware with MicroPython firmware. That's a single command, done once. After that you just edit and upload `.py` files. No compiling, no `#include` lines.

Compared to Arduino C++: it runs a bit slower (doesn't matter for LEDs and buttons), there are fewer libraries for obscure sensors (not an issue here since `neopixel` is built in), and the code itself reads like normal Python: variables, functions, loops, no semicolons or curly braces required.

## Parts you need (around $25 to $30 total)

An ESP32 dev board (any generic ESP32 DevKit, about $6 to $8). Three WS2812B "NeoPixel" LED strips with 8 LEDs each, one per lane for blue, green and yellow (about $3 to $4 each). Look for the pre wired "stick" style modules with data, 5V and GND pads so you don't need to solder. Three tactile push buttons (about 50 cents each). A breadboard and jumper wires (about $5). A USB cable for power and programming.

Keep the LED brightness low in software, which the code already does, so the ESP32's USB power can run all 24 LEDs comfortably. You won't need a separate power supply.

## Wiring

See `wiring_diagram.svg`. Here's the summary:

Blue strip data goes to GPIO 13. Green strip data goes to GPIO 12. Yellow strip data goes to GPIO 14. All three strips share power: 5V to the ESP32's 5V or VIN pin, GND to the ESP32's GND pin. The blue button goes to GPIO 32 with its other leg to GND. The green button goes to GPIO 33 with its other leg to GND. The yellow button goes to GPIO 25 with its other leg to GND.

Each strip's LED closest to the ESP32 is the "hit zone," the spot the note travels toward.

One small note: GPIO12 (used for the green strip) is a "strapping pin" that affects boot voltage on some ESP32 boards. It's unlikely to cause a problem here since the LED strip only drives that pin after boot, but if your board won't boot after wiring it up, move the green strip's data wire to GPIO27 instead and update `STRIP_PINS["green"]` in `main.py` to match.

## Setting up the software (one time)

Install Python from python.org if you don't already have it. Then install esptool by running `pip install esptool`. Download Thonny, a simple Python editor with built in ESP32 support, from thonny.org.

Next, download the MicroPython firmware for ESP32 from micropython.org/download/ESP32_GENERIC/. Grab the latest stable `.bin` file.

Now erase and flash the board. Adjust the port for your system: `COM3` on Windows, `/dev/ttyUSB0` on Linux, or `/dev/tty.usbserial-xxxx` on Mac.

```
esptool.py --chip esp32 --port COM3 erase_flash
esptool.py --chip esp32 --port COM3 --baud 460800 write_flash 0x1000 esp32_firmware.bin
```

If flashing fails partway through, try again without `--baud 460800`. It's slower but more reliable on some cables and boards.

Open Thonny, click the interpreter picker in the bottom right corner, choose "MicroPython (ESP32)," and select the port. You should see a `>>>` prompt in the shell, which means MicroPython is running on the board.

In Thonny, open `main.py` from this project. Then use File, "Save copy," and choose the MicroPython device option to save it onto the board as `main.py`. Saving it under that exact name makes it run automatically on boot.

Press the ESP32's reset button, or use Thonny's stop and restart option, to run it. Keep Thonny's shell open since the game prints hits, misses, and score there as you play.

## How to play

Notes spawn on a random lane and glow that lane's color as they move toward the last LED. When a note reaches the last LED, press that lane's button within about 0.4 seconds. A correct, well timed press flashes the LED white and adds to your score, which prints in Thonny's shell. Missing the window counts as a miss. Pressing a button with no note in the zone just logs a "whiff" with no penalty.

## Ideas for later

Add a fourth lane in red for more difficulty. Speed up `STEP_INTERVAL_MS` gradually as the score climbs. Add a small piezo buzzer for a hit or miss sound. Track combos or streaks, or add a "song mode" with a scripted note pattern instead of random spawns. Add a small OLED screen to show the score instead of relying on the serial shell.

This folder also has an earlier Arduino sketch, `esp32_pir_alarm.ino`, from a previous version of this project idea (a motion alarm). It's unrelated to the LED game above, so ignore it unless you want that separate project too.
