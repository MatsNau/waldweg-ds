# Devlog – „Der Weg aus dem Wald“ (Nina & Mats, WobbleWars 2)

Gemütliches 3D-Spiel für den Nintendo DS als Fortsetzung von WobbleWars-DS. Nina und Mats finden aus dem herbstlichen Wald heraus.
Es ist ein Geburtstagsgeschenk. Start war am 14.09.2026, das Ziel ist ein spielbares Spiel nach ca. 7 Tagen (Deadline ≥ 21.09.2026).

- **Plan (vollständig):** `C:\Users\matsn\.claude\plans\temporal-dancing-beacon.md`. Dort stehen Spielablauf, Story-Tore, Pilzbuch-Texte, Asset-Liste, Tagesplan und Risiken.
- **Vibe:** Herbst, goldene Stunde → Dämmerung → Nacht, Ghibli / Mumins / Hilda, Low-Poly à la Animal Crossing: Wild World.

---

## Kern-Entscheidungen (Kurzfassung)
- Deutsch, 10–15 Min Spielzeit, ein Waldgebiet, danach gewonnen.
- **Pilze antippen** (unterer Bildschirm) → im **Pilzbüchlein der Art zuordnen**, den Pilz dabei oben in **3D drehen**.
- **7 echte Arten:** Steinpilz, Satans-Röhrling, Wiesen-Champignon, Grüner Knollenblätterpilz, Echter Pfifferling, Fliegenpilz, Orangefarbener Ölbaum-Trichterling. Dazu der erfundene **Waldgott-Pilz** mit Rätselseite.
- **Fehler:** nur ein giftiger Pilz auf der falschen Seite. 3 Fehler sind frei, beim **4. Fehler Neustart**.
- **Zeit:** jeder bearbeitete Pilz lässt die Sonne sinken (kein Echtzeitdruck).
- **Mats** folgt automatisch. Nina gibt ihm per Stylus-Drag **Korb, Schal, Laterne, Glöckchen**.
- **Ende:** Schrein → Opfergabe + Glöckchen → Waldgott (Hirsch) führt hinaus → **Geburtstagsbotschaft**.

## Technik-Setup (installiert am 14.09.2026)
| Was | Version / Ort |
|---|---|
| MSYS2 | `C:\msys64` |
| Wonderful Toolchain | `C:\msys64\opt\wonderful` (Startmenü: „Wonderful Toolchain Shell“) |
| BlocksDS | 1.23.0 (`/opt/wonderful/thirdparty/blocksds/core`) |
| Nitro Engine | 0.16.0 (`/opt/wonderful/thirdparty/blocksds/external/nitro-engine`) |
| NFLib | 1.1.13 (`.../external/nflib`) |
| ARM-GCC | 16.2 inkl. libstdc++ (C++17) |
| melonDS | 1.1, `C:\Programming\tools\melonDS\melonDS.exe` |
| Blender | 5.2.1 LTS, `C:\Program Files\Blender Foundation\Blender 5.2` |
| Python | 3.13 (Windows) |

- Die Nitro-Engine-**Beispiele** sind nicht im Paket. Bei Bedarf holen wir sie vom GitHub-Spiegel: `git clone --depth 1 https://github.com/AntonioND/nitro-engine.git`. Der Hauptzweig entspricht 0.16.0; die GitHub-Tags gehen nur bis 0.15.5.
- Wichtige Beispiele:
  - `examples/templates/using_nflib`
  - `examples/effects/fog`
  - `examples/effects/shading_alpha_outlining`
  - `examples/loading/filesystem_textures_grf`
  - `examples/other/touch_test`

## Bedienung
| Befehl (im Projektordner) | Wirkung |
|---|---|
| `build.cmd` | baut `waldweg.nds` |
| `build.cmd clean` | löscht Build-Dateien |
| `run.cmd` | baut und startet melonDS |
| `wf.cmd sh tools/build_assets.sh` | erzeugt Modelle (Blender), konvertiert sie (obj2dl, grit) und patcht die Schrift |
| `wf.cmd <befehl>` | beliebiger Befehl in der BlocksDS-Umgebung |

## Projektstruktur (Stand Tag 1)
```
Makefile                      BlocksDS, basiert auf dem Template using_nflib (C++17, -Wall -Wextra)
wf.cmd / build.cmd / run.cmd  Windows-Wrapper
source/main.cpp               Testszene: 3D oben (Nitro Engine), Text unten (NFLib)
source/ui/text_de.*           UTF-8 → NFLib-Schrift-Slots (Umlaute)
assets/blender/gen_testmodels.py  prozedurale Modelle + Palette-Textur
assets/fonts/base_default.fnt     Originalschrift aus dem Template
assets/fonts/patch_umlauts.py     zeichnet ä ö ü Ä Ö Ü ß in die Schrift
tools/build_assets.sh         Asset-Pipeline
nitrofiles/                   generierte Spieldaten (models/, textures/, fnt/)
assets/build/                 Zwischendateien (OBJ, PNG, Blender-Log) – nicht in Git
```

---

## Tag 1 – Mo 14.09.2026 ✅
**Erledigt**
- Toolchain installiert (MSYS2, Wonderful, BlocksDS, Nitro Engine, NFLib) und melonDS eingerichtet.
- Das offizielle Template `using_nflib` gebaut und im Emulator geprüft (Roboter oben, 2D unten).
- Neues Repo `C:\Programming\waldweg-ds` angelegt (Git initialisiert, **noch kein Commit**).
- Asset-Pipeline läuft durchgängig: Blender (headless) → OBJ → `obj2dl` → `.bin`; Palette-PNG → grit → `.grf`.
- Testszene läuft in melonDS und **sieht gut aus** (vom User bestätigt):
  - Moosboden, 4 Herbstbäume, 3 Fliegenpilze
  - Outlines, Nebel, 4 Tageszeiten (Goldene Stunde, Abendrot, Dämmerung, Nacht)
  - Umlaut-Text unten lesbar
  - Steuerung: Steuerkreuz dreht die Kamera, A wechselt die Tageszeit, L/R ändert die Nebel-Entfernung

**Erkenntnisse / Stolpersteine**
- **Nitro Engine unterstützt nur BlocksDS** (kein devkitPro mehr). `nitrog3d` ist ein NSBMD-Importer, **kein** Exporter.
- **Wonderful-Umgebung:** `wf.cmd` setzt dieselben Variablen wie die offizielle Shell: `MSYSTEM=UCRT64`, `MSYS2_PATH_TYPE=inherit`, `BLOCKSDS`, `BLOCKSDSEXT`, `WONDERFUL_TOOLCHAIN`. `wf-pacman -Syu wf-tools` muss beim ersten Mal zweimal laufen, weil es sich selbst aktualisiert.
- **VRAM-Aufteilung:** `NE_TextureSystemReset(0, 0, NE_VRAM_AB)`, weil NFLib VRAM C/D auf dem Sub-Screen belegt. Kein Dual-3D, keine NFLib-3D-Sprites, kein NFLib-BG auf dem 3D-Screen.
- **obj2dl:**
  - ignoriert Materialien, deshalb bekommt jede Fläche per UV ein Farbfeld einer **16×16-Palette-Textur** (4×4 Felder à 4 px, siehe `PALETTE` in `gen_testmodels.py`)
  - V wird gespiegelt (`v = 1 - v`)
  - Flächen müssen Dreiecke oder Quads sein, Koordinaten innerhalb ±8
  - Aufruf: `--texture 16 16`
- **Blender-bmesh:** Die Int-Ebene `swatch` muss *vor* der Geometrie angelegt werden, sonst werden BMFace-Referenzen ungültig (siehe `new_bmesh()`).
- **OBJ-Export (Blender 5.2):** `bpy.ops.wm.obj_export(..., export_materials=False, export_triangulated_mesh=True, forward_axis="NEGATIVE_Z", up_axis="Y")` funktioniert.
- **Umlaute:** `NF_WriteText` kennt nur Latin-1-Bytes für die Slots 96–113. Die Zuordnung in `text_de.cpp` und `patch_umlauts.py` muss synchron bleiben:
  ä→105 (á), ö→108 (ó), ü→111 (ü), Ä→100 (Á), Ö→103 (Ó), Ü→104 (Ú), ß→110 (ï).
  Zusätzlich werden „ “ zu `"` und – zu `-` umgewandelt.
- **Polygone:** Baum 120, Fliegenpilz 106, Boden 72 Dreiecke. Die Pilze sind für die Welt zu schwer (Ziel 12–30 Tris); Detail-Versionen nur für die Inspektionsansicht. Budget pro Frame ≤ ~1600 (Hardware-Limit 2048).
- **Nebel-Testwerte:** shift 5, mass 2, depth 0x7E00 (per L/R einstellbar).

---

## Nächste Schritte – Tag 2 (Welt & Bewegung)
1. **Ersten Commit machen** (vorher kurz mit dem User abstimmen).
2. Code aufteilen: `source/world/timeofday.*` (Keyframes + weiche Übergänge über ~1 s), `source/world/scene.*`, `source/game.*` (Zustandsautomat).
3. **Nina-Steuerung:** Fixed Point, Diagonalen, ABXY gespiegelt für Linkshänder.
4. **Kamera im Wild-World-Stil**, die Nina folgt.
5. **Mats folgt** mit Stopp-Abstand.
6. Figuren als **starre Einzelteile** (Kopf/Körper/Arme/Beine) mit Wipp-/Schwing-Animation. Basis: Kenney *Mini Characters* (CC0) oder eigener Blender-Generator.
7. Größeres Waldstück mit Bäumen, Kollision mit Bäumen, Welt-Pilze auf 12–30 Tris reduzieren.
8. Debug-HUD (Polygonzähler, Zeitschritt per Taste), im Release-Build aus.
9. **Erster Konsolentest** (Build auf Flashcart/TWiLight Menu++).

## Offene Fragen an den User
- Konsolen-Setup (DS/DSi/3DS? Flashcart oder TWiLight Menu++?) – vor dem Konsolentest klären.
- Spieltitel, Name der Freundin, Text der Geburtstagsbotschaft.
- Aussehen von Nina und Mats (Haare, Kleidung, Farben), Musikstimmung.
- Dürfen für visuelle Tests Aufnahmen **nur vom melonDS-Fenster** gemacht werden?

## Arbeitsregeln (für Claude)
- Höchstens **ein Agent** gleichzeitig, keine Multi-Agent-Workflows.
- **Nie codeberg.org** öffnen, sondern die GitHub-Spiegel nutzen.
- **Keine Bildschirmaufnahmen** ohne Okay des Users.
- Commits nur nach Rückfrage.
