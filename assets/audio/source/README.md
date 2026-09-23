# Audio-Quellmaterial

Hier liegt das Rohmaterial für die Wald-Ambience. Die Dateien sind zu groß fürs
Repo und deshalb in `.gitignore` ausgenommen – im Repo steht nur der fertige
Loop `audio/amb_forest.wav`.

## `forest_birdsong.mp3`

Feldaufnahme eines Laubwaldes mit Vogelgesang, 3:00:00 h, MP3 192 kbit/s
Stereo 44,1 kHz (259 MB).

- **Herkunft / Lizenz:** _noch einzutragen_ – bitte nachtragen, bevor das Spiel
  weitergegeben wird.
- Die Aufnahme ist selbst schon geschleift: das Material wiederholt sich alle
  **24,4 Minuten** (gemessene Hüllkurven-Korrelation r = 0,85). Nur die ersten
  ~24 Minuten sind also einzigartig, alles danach ist eine Wiederholung.

## Daraus wird der Loop

```
python assets/audio/make_ambience.py audio           # -> audio/amb_forest.wav
python assets/audio/make_ambience.py <ordner> --start 279.0   # anderes Fenster
```

Braucht `ffmpeg` (MSYS2: `pacman -S mingw-w64-ucrt-x86_64-ffmpeg`, liegt dann
unter `C:\msys64\ucrt64\bin`). Fehlt ffmpeg oder die MP3, überspringt das
Skript den Schritt und die eingecheckte Fassung bleibt unverändert – ein
frischer Checkout kann die Asset-Pipeline also trotzdem durchlaufen.

Welches Fenster genommen wird, steht als `START` in `make_ambience.py`.
