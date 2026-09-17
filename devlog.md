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
| maxmod | 1.23.0, Teil von BlocksDS (`libs/maxmod`, `tools/mmutil`) |
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
| `wf.cmd sh tools/build_assets.sh` | erzeugt Modelle (Blender), konvertiert sie (obj2dl, grit), patcht die Schrift und erzeugt die Geräusche |
| `wf.cmd <befehl>` | beliebiger Befehl in der BlocksDS-Umgebung |

## Projektstruktur (Stand Tag 6)
Moderne Klassen-/Service-Struktur (Wunsch des Users): `main.cpp` startet nur die `Application`.
```
Makefile                      BlocksDS (C++17, -Wall -Wextra); Standard = Debug (WALDWEG_DEBUG), Release: make RELEASE=1
source/main.cpp               nur: static Application → Run()
source/core/                  Application (Init + Hauptschleife, besitzt alle Services), Services (Referenz-Bündel für DI),
                              InputService (Tasten, Touch, Laufrichtung nur Steuerkreuz), Random, Fatal
source/math/                  Fixed (20.12, _fx-Literal), Vec2 (Bodenebene x/z), Angle (Binärwinkel, atan2, Drehen)
source/render/                RenderService (NE-Init, Atmosphäre, Nebel, Poly-IDs, Lit/Glow), AssetService (alle Modelle per ModelId, Glow-Material)
source/content/               Species (7+1 Pilzarten: Name, giftig/essbar, Standort, Anzahl), Items (Korb, Schal, Laterne, Glöckchen)
source/world/                 TimeOfDayService (6 Keyframes, BlendTo), Forest (Layout, Stümpfe, Kollision, Culling + Zeichen-Budget, FindFreeSpot),
                              MushroomField (Pilze platzieren, Reichweite), LanternLight (Punktlicht + Lichtscheibe), CameraRig
source/entities/              CharacterRig (Einzelteile, Animation, Gegenstände in Hand/am Hals), Character, Nina, Mats (Folgen + ShowItem)
source/game/                  Game (Zustandsautomat, besitzt GameProgress), GameState, ExploreState, GameProgress, StoryDirector (Story-Tore)
source/audio/                 AudioService (maxmod, Ambience-Loop + One-Shots, Winddriften, Böen, Knarzen)
source/ui/                    SubScreenService (NFLib-Layer + Sprites unten), UiLayout (Pixel-Layout), TextSurface (Basis: Umbruch/Format),
                              TextService (Text unten), TopTextService (Dialogtext oben, VRAM B), ForestMap (Karte),
                              Backpack (Slots, Drag & Drop, Blätter, Porträt), DialogBox (Auto-Weiter + Aufgaben), DebugHud, text_de
assets/blender/dsmesh.py      gemeinsame Helfer: Palette (32×32, 8×8 Felder), UV-Farbfelder, Export
assets/blender/models_world.py      Boden, Bäume, Tanne, Busch, Stein, Stumpf, Fliegenpilz (Welt)
assets/blender/models_characters.py Nina & Mats als Einzelteile (Kopf/Körper/Arm/Bein)
assets/blender/models_mushrooms.py  Welt-Pilze (7 Arten + Waldgott-Pilz) und Glitzer-Stern
assets/blender/models_items.py      Korb, Schal, Laterne, Glöckchen (3D, an Mats)
assets/audio/synth.py         Synthese ohne numpy: Rauschen, Filter, Hüllkurven, Korn-Wolken, WAV mit Loop-Punkten
assets/audio/gen_sfx.py       erzeugt audio/*.wav (Schritte, Ambience, Bö, Knarzen, Umblättern)
assets/ui/pixelart.py         Mini-Canvas für indizierte PNGs (ohne Pillow)
assets/ui/gen_ui.py           Pixelgrafik unten: Karten-Kacheln, Leiste, Dialogbox, Symbole, Gegenstände, Mats-Porträts
assets/blender/gen_models.py  Einstiegspunkt für Blender
assets/fonts/                 Schrift + Umlaut-Patch
tools/build_assets.sh         Asset-Pipeline (konvertiert automatisch alle erzeugten OBJ)
nitrofiles/                   generierte Spieldaten (models/, textures/, fnt/, ui/, book/)
audio/                        generierte WAVs; mmutil packt sie beim Build zur soundbank.bin
```

---

## Tag 1 – Mo 14.09.2026 ✅
**Erledigt**
- Toolchain installiert (MSYS2, Wonderful, BlocksDS, Nitro Engine, NFLib) und melonDS eingerichtet.
- Das offizielle Template `using_nflib` gebaut und im Emulator geprüft (Roboter oben, 2D unten).
- Neues Repo `C:\Programming\waldweg-ds` angelegt (erster Commit `ba81104`).
- Asset-Pipeline läuft durchgängig: Blender (headless) → OBJ → `obj2dl` → `.bin`; Palette-PNG → grit → `.grf`.
- Testszene läuft in melonDS und **sieht gut aus** (vom User bestätigt):
  - Moosboden, 4 Herbstbäume, 3 Fliegenpilze
  - Outlines, Nebel, 4 Tageszeiten (Goldene Stunde, Abendrot, Dämmerung, Nacht)
  - Umlaut-Text unten lesbar
  - Steuerung: Steuerkreuz dreht die Kamera, A wechselt die Tageszeit, L/R ändert die Nebel-Entfernung

**Erkenntnisse / Stolpersteine**
- **Nitro Engine unterstützt nur BlocksDS** (kein devkitPro mehr). `nitrog3d` ist ein NSBMD-Importer, **kein** Exporter.
- **Wonderful-Umgebung:** `wf.cmd` setzt dieselben Variablen wie die offizielle Shell: `MSYSTEM=UCRT64`, `MSYS2_PATH_TYPE=inherit`, `BLOCKSDS`, `BLOCKSDSEXT`, `WONDERFUL_TOOLCHAIN`. `wf-pacman -Syu wf-tools` muss beim ersten Mal zweimal laufen, weil es sich selbst aktualisiert.
- **VRAM-Aufteilung:** ~~`NE_TextureSystemReset(0, 0, NE_VRAM_AB)`~~ seit Tag 3 `NE_VRAM_A` (VRAM B = Dialogtext oben), NFLib belegt VRAM C/D auf dem Sub-Screen. Kein Dual-3D, keine NFLib-3D-Sprites, kein NFLib-BG auf dem 3D-Screen.
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

## Tag 2 – Di 15.09.2026 (in Arbeit)
**Aussehen der Figuren (vom User)**
- **Nina:** braune, schulterlange Haare, große Brille, dunkelgrüne Jacke, blaue, etwas weiter geschnittene Jeans.
- **Mats:** braun-rote Locken, beige Jacke, weite Jeans.

**Erledigt**
- Code komplett in Klassen/Services umgebaut (siehe Projektstruktur).
- Blender-Generator aufgeteilt; Palette auf 32×32 (64 Farbfelder, 16 bpp) erweitert.
- Nina & Mats als Einzelteile modelliert (Nina ~264 Tris, Mats ~322 Tris), Vorschau in Blender geprüft.
- Welt: Boden 28×28 Einheiten (200 Tris, ×2 skaliert), Baum 66, Tanne 32, Busch 15, Stein 20, Stumpf 24, Welt-Fliegenpilz 22 Tris.
- Wald wird beim Start per Seed erzeugt: doppelter Baumrand + zufällige Objekte, Lichtungen am Start (0, 9) und in der Mitte.
- Nina läuft (Steuerkreuz, Diagonalen normalisiert, Kollision mit Objekten, weiches Drehen). *(ABXY-Spiegelung an Tag 7 entfernt.)*
- Mats folgt Ninas Brotkrumen-Pfad, hält 1,0 Abstand und holt ab 2,6 Abstand schneller auf.
- Lauf-Animation: Beine/Arme schwingen abhängig von der Strecke, Wippen, Atmen im Stand.
- Kamera im Wild-World-Stil (feste Blickrichtung nach Norden, weiches Folgen).
- Tageszeit mit 6 Phasen (Gold → Bernstein → Rosé → Violett → Blaue Stunde → Nacht) und 1 s Überblendung.
- Debug-HUD unten: Polygone, gezeichnete Objekte, Positionen, Tageszeit, Nebel. SELECT = Zeit weiter, L/R = Nebel, START = HUD aus.
- Build ohne Warnungen.

**Erkenntnisse**
- `wf.cmd` aus **Git Bash** aufgerufen hängt. Aus **PowerShell** (`.\wf.cmd ...`, `.\build.cmd`) funktioniert es.
- Rotation (libnds `glRotateYi`): Modell schaut bei Winkel 0 nach +Z; Blickrichtung = `atan2(dx, dz)`.
- Poly-ID-Gruppen (Outline-Farbslot = id >> 3): Boden 0, Wald 8–15, Nina 16–23, Mats 24–31, Pilze 32–39. Jedes Körperteil hat eine eigene ID, damit es Outlines bekommt.
- Figuren-Gelenke stehen doppelt in `models_characters.py` und `CharacterRig.cpp` und müssen synchron bleiben.

**User-Feedback (15.09.)**
- Optik von Nina, Mats und Wald gefällt, bleibt erstmal so. Steuerungsgefühl „super“.
- Bug: HUD zeigte 0 Polygone, weil der Zähler nach dem VBlank (nach dem Buffer-Swap) gelesen wurde. Behoben: `RenderService::Render` liest Polygon- und Vertexzahl am Ende von `Draw3D`, direkt vor dem Flush.

**Offen für Tag 2**
1. Echte Polygonzahl vom User ablesen lassen (Budget-Entscheidung für Welt-Pilze).
2. Erster Konsolentest mit Flashcart (nicht dringend).
3. Commit (nach Rückfrage).

## Tag 3 – Di 15.09.2026 (vorgezogen) ✅
**User-Feedback vorher:** Polygonzahl im Wald 1356 – ok. Kein Commit gewünscht, weiterarbeiten.

**Erledigt**
- Palette um Pilz- und Gegenstandsfarben erweitert (62 von 64 Feldern belegt).
- Welt-Pilze (Blender): Steinpilz 28, Satans-Röhrling 28, Champignon 28, Knollenblätterpilz 36, Pfifferling 15, Fliegenpilz 36, Ölbaum-Büschel 45, Waldgott-Pilz 28 Tris; Glitzer-Stern 8 Tris.
- Gegenstände 3D: Korb 28, Schal 18, Laterne 32, Glöckchen 32 Tris. Mats trägt sie (Korb rechts, Laterne links, Schal am Hals).
- Deko-Fliegenpilz aus dem Wald entfernt; es gibt immer ≥ 4 Baumstümpfe. 14 Pilze (je 2 pro Art), Ölbaum-Trichterling auf Stümpfen.
- Pilze in Reichweite (1,7) glitzern oben (unbeleuchtet, doppelseitig) und blinken auf der Karte.
- Unterer Bildschirm (NFLib): Karte (512×512-Kachel-BG, 12 px pro Einheit, scrollt mit Nina), Leiste mit 4 Rucksack-Slots, 3 Blättern (Fehler) und Mats-Porträt (normal/fröhlich/friert), Dialogbox als eigener BG-Layer.
- Drag & Drop: Gegenstand aus dem Slot auf Mats' Porträt ziehen; sonst springt er zurück. Freigeschaltete Gegenstände hüpfen leicht.
- Story-Tore: Start-Dialog + Korb-Tutorial (ohne Korb max. 2 Pilze), 5 Pilze → Schal (Mats friert), 9 Pilze → Laterne. Zeit sinkt mit jedem Pilz (3 Bernstein, 5 Rosé, 7 Violett, 9 Blaue Stunde).
- Pilz antippen: nur in Reichweite, sonst Hinweis. **Platzhalter** bis zum Pilzbüchlein (Tag 4): Pilz wird direkt eingesammelt (Debug zeigt die Art).
- Debug-HUD jetzt in der Dialogbox, standardmäßig aus (START).

**Erkenntnisse**
- grit für NFLib: BG `-ftB -fh! -gTFF00FF -gt -gB8 -mR8 -mLs`, Sprites `... -m!` (Frames untereinander). Beispiele: GitHub `knightfox75/nds_nflib` (examples/*/assets/convert.sh).
- Kachelsatz mit fester Reihenfolge: als 8 px breite Spalte exportieren (`-m!`), `NF_LoadTilesForBg` liest nur `.img`/`.pal`. (`-mR!` bricht mit „Number of tiles exceeds field limit“ ab.)
- Sprites mit NFLib neben Nitro Engine: `NF_SpriteOamSet(1)` vor dem VBlank, `oamUpdate(&oamSub)` direkt danach.
- `NF_DefineTextColor(screen, layer, n, r, g, b)` belegt Ext-Palette n; Farbe 1 = Tinte, 2 = Sprecher, 3 = Hinweis.
- Unbeleuchtete Polygone zeigen nur die Emission des Materials → Glow-Material = Klon der Palette mit Emission weiß.
- Python-Edits unter Windows immer mit `encoding="utf-8"` öffnen (sonst werden Umlaute kaputt geschrieben).

**User-Test 1 (15.09.) → Änderungen**
- Bug: unten 4× Korb, Porträt = Korb, Karte nur Pilz-Icons. Ursache: `NF_VramSpriteGfx(..., keepframes=true)` legt nur **einen** Frame ins VRAM, `NF_SpriteFrame` kopiert dann für alle Sprites desselben Blatts (Header-Doku ist irreführend). Fix: `false` = alle Frames im VRAM.
- Glitzern der Pilze entfernt (stört die Herbststimmung). Reichweite zeigt nur noch das blinkende Karten-Icon.
- Dialoge jetzt **oben** (Wunsch des User): BG1 über dem 3D-Bild (`TopTextService`). Glyphen auf Pergament vorgerendert, Rahmen-Kacheln im Code erzeugt.
- Dialoge springen **automatisch** weiter (Lesezeit 150 Frames + 4 pro Zeichen, max. 480; Tippen auf die Karte überspringt). Aufforderungen (`Ask`, z. B. „Gib mir den Korb“) bleiben stehen, bis die Aktion erledigt ist (`DialogTask`), und verschwinden dann sofort.
- Schal: Mats trägt den Schal, **Nina setzt eine Wollmütze** auf (Idee des User). Palette jetzt voll (64/64).
- Laterne leuchtet: Leuchtglas (unbeleuchtet), flackernder warmer Lichtkegel am Boden (transluzente Scheibe) und „Punktlicht“: Licht 1 wird vor jedem Objekt auf die Laterne ausgerichtet und nach Abstand gedimmt (Radius ~4,6).
- Gemeinsame Basisklasse `TextSurface` (Zeilenumbruch, Format) für oberen und unteren Text.

**User-Test 2 (15.09.) → Änderungen**
- Symbole unten ok, Schal + Mütze „super“, Laternenlicht grundsätzlich ok.
- **Dialoge oben erschienen gar nicht** (Version mit VRAM B, 8bpp, Alpha-Blending). Ursache noch unklar (NFLib/NE überschreiben nachweislich keine Hauptbildschirm-Register, libnds-Adressen stimmen). Neuer Versuch exakt nach `NE_InitConsole`: VRAM F als Main-BG, BG1 4bpp, Map-Basis 4, Tile-Basis 0, `REG_BG0CNT = BG_PRIORITY(1)`, ohne Blending; Texturen wieder `NE_VRAM_AB`. Debug-HUD zeigt jetzt `DC`/`B0`/`B1` (REG_DISPCNT, BG0CNT, BG1CNT) zur Diagnose – erwartet: DC mit Bit 0x0200, B0 …1, B1 0400.
- Mütze herbstlich: rostrot statt pink.
- Lichtscheibe flackerte im Boden (Depth-Fighting) → Höhe 0,03 → 0,12.

**User-Test 3+4 (15.09.) → Dialoge als 3D-Quads**
- Auch die VRAM-F-Variante zeigte nichts. Diagnose (vom User abgelesen, während „Gib mir den Korb“ aktiv war): Dialog aktiv ✓, Panel-Flag ✓, Map-Eintrag „G“ ✓, Palette ✓ – aber `REG_DISPCNT` = `0x00010308` (BG1-Bit fehlt direkt nach `bgShow`) und die Kacheldaten in VRAM F lasen sich als 0. Ursache nicht gefunden (NFLib/NE/libnds-Quellen geprüft).
- **Lösung:** Dialog wird mit Nitro Engine am Ende des 3D-Frames gezeichnet (`NE_2DViewInit`): Rahmen- und Pergament-Quad (`NE_2DDrawQuad`) + ein texturiertes Quad pro Buchstabe aus `textures/font.grf` (16×8-Atlas aus der gepatchten NFLib-Schrift, `assets/fonts/make_font_texture.py`, grit `-gB16 -gTFF00FF` → Alpha). Farbe per Vertex-Farbe, ohne Nebel/Licht, Poly-ID 62 (Umriss nur um das Panel), Tiefe negativ = vorne. Kostet ~100–130 Polygone, solange ein Dialog offen ist.
- `TopTextService` hat dieselbe `TextSurface`-Schnittstelle, speichert ein Zeichenraster und zeichnet es in `Draw(render)`. Keine 2D-BG-Ebene mehr auf dem Hauptbildschirm, keine Diagnosezeilen mehr im HUD.
- **Merksatz:** 2D-BG-Ebenen auf dem 3D-Bildschirm haben hier (NE + NFLib + melonDS) nicht funktioniert – Overlays oben immer als NE-2D-Quads zeichnen.

**User-Test 5 (15.09.) → Abschluss Tag 3**
- Dialoge oben werden angezeigt ✓.
- **Design-Entscheidung des User:** keine „Tipp“-Dialoge/Tutorial-Hinweise. Das Spiel soll sich der Spieler selbst erschließen (Exploration, Coziness, Immersion). Entfernt: Drag-Hinweis, „Geh zu einem Pilz…“, „zu weit weg“, „Mehr passt nicht in deine Hände“. Mats spricht nur noch in seiner Rolle (z. B. „Gibst du mir den Korb…?“, „Deine Hände sind ja schon voll!“). Pilz außer Reichweite antippen → es passiert nichts.
- `DialogBox` hat nur noch `Say` (auto-weiter) und `Ask` (bis Aufgabe erledigt); `TextColor::Hint` entfernt.
- Tag 3 vom User als fertig abgenommen.

## Tag 4 – Di 15.09.2026 (vorgezogen) ✅
**Entscheidungen mit dem User**
- Buchseite = Name als Überschrift + **3 Bilder** (Seite, Unterseite, Merkmal) mit **Stichworten** (erstmal testen).
- Das Buch öffnet sich **automatisch beim Antippen eines Pilzes** (kein Buch-Gegenstand im Rucksack).
- Beim Bestimmen werden die **Bildschirme getauscht**: Buch oben (NFLib-Engine), 3D-Pilz unten auf dem Touchscreen zum Drehen (Idee des User, `NE_MainScreenSetOnBottom`).
- Neustart beim 4. Fehler wie im Plan (Abmildern noch offen).

**Erledigt**
- Detail-Modelle (`models_mushrooms_detail.py`, 250–520 Tris): Röhren/Poren (Schachbrett), Netz am Stiel, Lamellen als doppelseitige Finnen, Ring, Knolle + Scheide, Flocken, Leisten, Ölbaum-Büschel auf Holz.
- Buchillustrationen: `render_book.py` rendert je Art 3 × 72×72 (Workbench, orthografisch, transparent, View-Transform „Standard“); `gen_book.py` setzt Seiten (Pergament, Rahmen, Bildfelder, Blätter-Pfeile) zusammen, Farben auf DS-15-Bit + Median-Cut ≤ 200; grit → `nitrofiles/book/pageN.*` (~20–25 KB Tiles je Seite).
- NFLib-Schrift-Datei auf 128 Glyphen gekürzt. **Achtung:** `NF_LoadTextFont(file, name, w, h)` – w/h sind die Größe der Textebene und müssen Vielfache von 256 sein (sonst Fehler 115); NFLib liest ohnehin nur 127 Glyphen (8 KB).
- `IdentifyState` + `IdentifySession` (Übergabe an/aus `ExploreState`), `StateMachine`-Interface für Zustandswechsel.
- `BookView` (Seite laden, Titel/Essbarkeit/Stichworte als Text, Seitenzahl), `SubScreenService::EnterBookMode/ShowBookPage/ExitBookMode` (Karte, Leiste, Sprites aus; Seite auf Layer 1 statt Dialog-Panel).
- `InspectionView`: Pilz ziehen = drehen (auch Unterseite, ±100°), Nachschwingen; unten links Hand (zurücklegen), unten rechts Korb („Das ist er!“, wippt leicht); Hintergrund-Verlauf; eigenes neutrales Licht, kein Nebel. Blättern: L/R, Steuerkreuz, Y/A. B = zurück.
- Regeln (`StoryDirector::OnIdentified`): richtig → Mats nennt die Art (essbar: Korb, giftig: stehen lassen); essbare verwechselt → „Hm… lieber weglegen“; giftiger Pilz falsch → Blatt fällt, Mats besorgt (neues Porträt); 4. Fehler → Mats „Mir ist ganz flau…“, Abblenden (`ScreenFader`), `StartNewGame`. Platzhalter „Eingesammelt!“ entfernt.
- `RenderService`: `Lighting::LitTwoSided`, `SetFogEnabled`, `Draw2DImage` (texturierte 2D-Quads, auch für die Dialogschrift).

**User-Test (15.09.)**
- Fehler 115 beim Start: `NF_LoadTextFont` mit 256×32 → zurück auf 256×256 (siehe oben).
- Danach: Bildschirmtausch und Drehen „sehr gut“, keine Fehlermeldungen. Bestätigt: richtige Seite + Korb = richtig bestimmt.
- **Bilder stilisiert** (Wunsch: mehr Zeichnung, süßer): `render_book.py` rendert jede Ansicht zweimal in 144×144 (FLAT = Farbflächen, STUDIO mit glatten Normalen = Licht). `gen_book.py::stylize` macht daraus Cel-Shading (Schatten warm getönt, Glanzlicht, leicht pastell), dunkelbraune Tusche-Kontur um die Silhouette, weichere Linien zwischen Farbflächen, dann 2×2-Verkleinerung auf 72×72. Seiten haben jetzt nur noch 44–90 Farben.
- Fliegenpilz-Flocken größer und auf der echten Hutoberfläche (`surface_height`); Ölbaum-Unterseite aus seitlich-tiefer Perspektive.
- **Dunkler:** Rosé leicht, Violett/Blaue Stunde/Nacht deutlich dunkler; Nebel-Start je Tageszeit (`Atmosphere::fogDepth`: 0x7D80 → Nacht 0x7B80 ≈ 6 Einheiten vor der Kamera). Debug-L/R verschiebt nur noch einen Offset. Laterne heller/weiter (Radius 5,2, Lichtscheibe Alpha 12).
- **Build-Lücke behoben:** ROM hängt jetzt von allen Dateien in `nitrofiles/` ab (vorher wurde nach reinen Asset-Änderungen nicht neu gepackt).

- User: Zeichenstil + Dunkelheit „sieht super aus“. **Stichworte aus dem Buch entfernt** (Wunsch des User) – Seite zeigt nur Name, essbar/giftig, 3 Bilder, Seitenzahl.
- Tag 4 abgeschlossen ✅ (Rätselseite Waldgott-Pilz folgt mit Tag 5).

## Tag 5 – Di 15.09.2026 (vorgezogen, in Arbeit)
**Entscheidungen mit dem User**
- **Laterne lenken gestrichen.**
- **Waldgott-Pilz schwarz-weiß gefleckt und leuchtend** (wie eine Kuh). Keine Rätselseite (Buch hat keine Texte mehr); er wird ohne Buch direkt mitgenommen.
- **Schrein-Texte nur einmal**, und nur wenn man den Pilz noch nicht hat. Mit Pilz: Schrein antippen → Pilz wird darauf platziert.
- **Waldgott = Kuh**, die sich in eine riesige Gottheit verwandelt und Nina & Mats aus dem Wald trägt. Vorschlag an den User (noch zu bestätigen): Kuh trottet aus dem Wald → schnuppert an der Opfergabe → weißer Blitz, wächst ~4×, leuchtet, Blütenkranz/Hörner/Lichtring → Abblende, beide sitzen auf dem Rücken → läuft zum Waldrand, Kamera zieht hoch → Abblende → Geburtstagsbotschaft.

**Erledigt**
- Schrein (`models_world.py::make_shrine`, 76 Tris): Plattform, Altarstein mit Moos, zwei Steinsäulen mit Querstein. Als `PropKind::Shrine` in der Mitte des Waldes (Kollision, Kartensymbol Kachel 28, Lichtung Radius 2,8).
- Waldgott-Pilz Welt (32 Tris) + Detail neu gefärbt (Palette: `god_cap` weiß, `god_spot` schwarz statt ungenutztem `glow`), wird unbeleuchtet (leuchtend) gezeichnet.
- Pilz steht neben dem Schrein (Offset 1,3 | 1,1) und ist erst sichtbar/antippbar, wenn Mats die Laterne hat.
- Ablauf: erster Besuch am Schrein ohne Pilz → Mats/Nina-Kommentar (einmal) · Pilz antippen → Nina nimmt ihn mit · Schrein antippen (in Reichweite, mit Pilz) → Pilz leuchtet auf dem Altar, Glöckchen frei, Mats bittet darum (`DialogTask::GiveBell`) · Glöckchen geben → Mats hält es und läutet („Kling… kling…“).
- Debug: R halten + SELECT = sofort Blaue Stunde mit Korb, Schal, Laterne.

**Kuh-Sequenz (vom User bestätigt, ohne Blitz; der Kuh-Gott heißt „Shroomchen“ und sagt einmal „Muh.“)**
- Modelle `models_cow.py`: `cow_body` (260 Tris: Körper mit runden Flecken, Kopf, rosa Schnauze, Hörner, Ohren, Euter, Schwanz), `cow_leg` (26), `cow_crown` Blütenkranz (84), `cow_halo` Lichtring (24, unbeleuchtet).
- `Shroomchen` (Entity): Laufen mit diagonal schwingenden Beinen (Schrittlänge wächst mit der Größe), Skalierung, Gottheit-Modus (unbeleuchtet leuchtend + Kranz + Ring), Sitzplätze auf dem Rücken.
- `Finale` (in `ExploreState`): Glöckchen gegeben → „Kling…“ → Kuh kommt aus dem Wald zum Altar → schnuppert (~1,7 s) → wächst sanft auf 4× und leuchtet (Nebel weicht zurück, ihr Licht ersetzt die Laterne, Kamera zoomt raus) → „Shroomchen: Muh.“ → Abblende → Nina & Mats sitzen auf dem Rücken → Shroomchen läuft nach Süden zum Waldrand → Abblende → `EndingState`.
- `EndingState`: oben Morgenhimmel, Shroomchen dreht sich langsam mit beiden auf dem Rücken, Titel im Pergament-Panel; unten Buchseite `ending` (Pergament mit Pilzen, Herzen, Blättern) mit der Botschaft.
- Texte in `source/content/Ending.h` – **Platzhalter**, bis der User die Botschaft liefert.
- Engine: `CameraRig::SetZoom`, `RenderService::SetFogOverride`, `Character::SetElevation`, `ScreenFader::SetBlack`, `SubScreenService::ShowBookImage`, `PolyGroup::Shroomchen`.

**Bugfixes nach User-Test (15.09.)**
- **Textboxen stapelten sich** → Lesezeit kürzer (90 Frames + 3 pro Zeichen, max. 270). Eine später ausgelöste Box löst die aktuelle nach mind. 45 Frames ab und verwirft ältere wartende; Boxen aus demselben Frame (kleine Unterhaltung) bleiben in Reihenfolge (`Message::stamp`).
- **Waldrand im Nichts** → Boden ×4 skaliert (±28 statt ±14), 5 statt 2 Baumreihen am Rand (äußere lichter), `kMaxProps` 420, Nebel-Rampe halbiert (`kFogShift` 4: volle Stärke ~22 Einheiten).
- **Shroomchen schwarz beim Wachsen** → unbeleuchtete Polygone brauchen das Emissions-Material: `Shroomchen::Draw` setzt `AssetService::GlowMaterial()` auf Körper/Beine/Kranz, solange sie Gottheit ist.
- **Heiligenschein entfernt** (Wunsch des User): `cow_halo` gestrichen.

**Neues Schlussbild (Wunsch des User)**
- Alle drei sitzen mit dem Rücken zur Kamera auf einem Hügel, Sonnenaufgang, in der Ferne das Dorf mit rauchenden Schornsteinen. Mats: „Guck mal, da hinten ist unser Dorf!“ – Nina: „Ja, stimmt. Aber lass uns noch ein bisschen hier bleiben.“ – „Ende“.
- **Über beide Bildschirme verteilt**, Geburtstagsnachricht vorerst gestrichen (User).
- Oben (NFLib, Hauptbildschirm unten → `NE_MainScreenSetOnBottom`): `render_ending.py` rendert ferne Hügel, Bergkette und Dorf (`models_ending.build_backdrop`, nicht für den DS exportiert) im Buch-Zeichenstil; `gen_ending.py` setzt Himmelsverlauf (2×2-Dithering), Sonne mit Schein und Tal-Dunst zusammen → `book/ending_sky` (19 KB Tiles). Schornstein-Positionen werden in Blender projiziert → `book/ending_chimneys.txt` → Rauch-Sprites (3 Größen) steigen auf.
- Unten (3D): `end_hill` (200 Tris), Nina & Mats sitzend (neue Sitzpose im `CharacterRig`), Shroomchen liegend mit Blütenkranz (nicht leuchtend); Hintergrund und Nebel in Dunst-Farbe `RGB15(26,22,17)` = unterer Rand des oberen Bildes → nahtloser Übergang.
- Dialog im Pergament-Panel des oberen Bildschirms (NFLib-Text), feste Zeitleiste.
- Debug: L halten + SELECT springt direkt zum Schluss.

**Schönheitsrunde (Wünsche des User, 15.09.)**
- **Haare ohne Lücken:** `hair_volume` in `models_characters.py` – ein geschlossenes Haarvolumen um den ganzen Kopf mit Gesichtsöffnung (kein Haar unterm Kinn). Nina: schulterlang an Seiten/Rücken (188 Tris Kopf), Mats: lockig-unregelmäßig + Locken rundum (250 Tris Kopf).
- **Schatten:** `ShadowCaster` zeichnet transluzente Scheiben (8 Tris, alle mit derselben Poly-ID → Überlappungen werden nicht dunkler), gestreckt in Sonnenrichtung. `Atmosphere` hat jetzt `shadowLength`/`shadowAlpha`: Gold 0,55 → Bernstein 0,85 → Rosé 1,25 → Violett 1,7 (× Objekthöhe), nachts keine Schatten. Für Bäume, Büsche, Steine, Stümpfe, Schrein, Nina, Mats und Shroomchen.
- **Kuhpilz zufällig:** Position pro Spiel aus `time()` (≥ 4 vom Schrein, ≥ 5 vom Start, frei).
- **Fliegende Blätter:** `LeafParticles` (max. 10, 2-Tris-Blätter in 3 Farben, trudeln mit Wind und Drehung) im Wald (nachts seltener) und unten im Schlussbild; oben im Schlussbild Blätter-Sprites (3 Farben × 2 Flatter-Frames).
- **Schlussbild herbstlicher:** 26 kleine Herbstbäume auf den fernen Hügeln (per Raycast aufgesetzt), Hügel mit Laubfarben, weniger Dunst-Nebel (0x7E40), Deko unten: 2 kleine Herbstbäume, 3 Büsche, 2 Fliegenpilze, 1 Stumpf.

**Schlussbild, Runde 2 (User: mehr Bäume, grün statt beige, Fluss mit Brücke)**
- Oben: statt beigem Taldunst ein grünes Tal (`make_valley`) mit Fluss (Band in Jeansblau) und Holzbrücke, 18 Herbstbäume an beiden Ufern (`make_valley_trees`); Dunst nur noch leicht auf den fernen Hügeln.
- Unten: Wiese flacher und breiter (`end_hill`, Spielskala 3), Kamera schaut steiler von hinten oben, Hintergrund + Nebel in Wiesengrün `RGB15(13,15,7)`. 8 Herbstbäume, 3 Büsche, 2 Fliegenpilze, 1 Stumpf auf der Hügelhöhe (`HillHeight`, gleiche Formel wie in Blender). Laterne im Schlussbild weggelassen (Polygonbudget ~1870).

**Schlussbild, Runde 3 (User: oben „Top, bleibt so“; unten zu leer, Hügel erkennbar machen, Figuren weiter nach unten, viel mehr Wald)**
- Hügel mit klarer Kuppe (`end_hill`, 288 Tris): flache Kuppe bis z = 1,2, danach steiler Hang (0,16·Δ²) bis Talboden −9. Die drei sitzen bei z = 1,9 kurz vor der Kuppe, Kamera von hinten oben → Figuren im unteren Drittel.
- **Wald aus Baum-Aufstellern:** `treecards.grf` (64×64, 4 gezeichnete Bäume: orange, rot, gelb, Tanne, mit Tusche-Kontur) als texturierte Quads, 1 Polygon pro Baum, unbeleuchtet mit warmer Tönung, vom Nebel eingehüllt, leicht zur Kamera geneigt. Bis zu 200 Stück in Reihen über Hang und Tal (Abstand/Breite/Größe wachsen mit der Entfernung).
- Vorn nur noch 2 echte 3D-Bäume, 2 Büsche, 2 Fliegenpilze. **Budget beachten:** DS-Limit ist auch 6144 Vertices – Schätzung Schlussbild ~1770 Polygone / ~5400 Vertices.

**Schlussbild, Runde 4 (User: Bäume bis an den oberen Rand, mehr Bäume, Kamera tiefer / mehr von hinten)**
- Kamera flacher hinter den dreien (y 1,9) mit engerem Blickwinkel (`NE_SetFov(50)` im Schlussbild) → Figuren groß am unteren Rand.
- Gelände: Kuppe → Hang → Talboden → **Gegenhang** (ab z = −12 steigt es wieder bis +4), Hügel ×3,5; damit reicht der Wald bis an die Oberkante.
- 365 Baum-Aufsteller (32 seitlich neben der Kuppe + 24 Reihen bis z = −26), keine 3D-Bäume/Büsche/Pilze mehr (Vertex-Budget). Schätzung ~1770 Polygone / ~5700 Vertices.

**Schlussbild, Runde 5 (User-Screenshot: unten stimmt die Komposition nicht)**
- Befund: erste Baumreihen direkt hinter der Kuppe (fast ohne Gefälle) → wenige riesige Bäume stellen das Bild zu; Kamera zu nah → Figuren angeschnitten; Rauch-Puffs zu groß/grell.
- Neu: **Blender-Mock-up** der unteren Szene (`scratchpad/preview_ending3d.py`, gleiche Kamera/Hügel/Pflanzregel) zum Prüfen vor dem DS-Build.
- Fix: Kamera (0,1 | 2,3 | 6,2) → Blick auf (0,1 | −1 | −10), FOV 50; Baumreihen erst ab z = −3,1 (Kronen unter Augenhöhe), Gegenhang bis +5,5, ferne Bäume größer (+0,07/Einheit); einige kleine Bäume seitlich auf der Kuppe; Rauch-Puffs klein und hellgrau.
- **Merksatz:** Figuren-/Kamera-Kompositionen erst im Blender-Mock-up prüfen.

**Schlussbild, Runde 6 (User-Screenshot: unten nur Grün)**
- Ursache 1: Das grüne 2D-Hintergrund-Quad (`NE_2DDrawQuadGradient`, Tiefe 3900) wurde zuletzt gezeichnet und lag in der Tiefe **vor** allem, was weiter weg war → Hang und Wald verdeckt. Entfernt, Hintergrund ist jetzt nur die Löschfarbe.
- Ursache 2: Der Hügel wurde gegen die Sonne beleuchtet → fast schwarz. Jetzt unbeleuchtet mit eigenem Material (Palette + Emission `RGB15(29,31,24)`), nur Moos-Grüntöne (bei 4-Einheiten-Flächen wird eine Laub-Fläche zum riesigen orangen Dreieck).
- `RenderService::SetHaze` (eigene Farbe, Dichtetabelle bis max. 72/127, Hintergrund ohne Nebel) und `SetViewDistance` (Schlussbild 64 statt 32); `EndingState::Exit` stellt beides zurück.
- Wald: erste Reihe ab z = −4,5, kleinere Bäume (+0,035/Einheit), dichtere Reihen (~355 Karten), keine Karten mehr seitlich auf der Kuppe. Gegenhang steigt bis +7 → Bäume bis an die Oberkante. Löschfarbe = Olivgrün der Unterkante des oberen Bildes. Mehr Umgebungslicht für die Figuren.
- **Debug:** `make BOOT_ENDING=1` startet direkt im Schlussbild (danach `Game.cpp` neu bauen). Screenshots des melonDS-Fensters per `PrintWindow` (User hat das erlaubt).
- **Merksatz:** 2D-Quads nie als Hintergrund hinter 3D-Szenen zeichnen; Tiefe gegen weit entfernte Geometrie verliert.

**Feinschliff Finale/Ende (User: Kuh-Beine mit Lücke, Kuh bleibt vor dem Abblenden stehen, „Ende“ weglassen)**
- Kuh-Beine: reichen 0,16 über die Hüfte in den Bauch, Ansatz weiter innen (`LEG_X` 0,2, `LEG_Y` 0,3 = `kLegX`/`kLegZ`). Von hinten und von der Seite im melonDS-Screenshot geprüft: keine Lücke.
- Finale: Shroomchen läuft auf ein Ziel weit hinter dem Waldrand (`kWalkOutZ` 60) und läuft deshalb weiter, während das Bild dunkel wird.
- Schlussbild: kein „Ende“ mehr. Nach Ninas Satz verschwindet die Textbox, das Bild bleibt, bis ein Knopf (A/B/X/Y/L/R/Start/Select/Touch) gedrückt wird → Abblenden → **neues Spiel** (`StateMachine::StartNewGame`, `ExploreState::StartNewGameOnEnter`). `EndingState::Exit` stellt Hauptbildschirm oben, FOV 70, Nebel, Sichtweite und die Karte (`SubScreenService::ExitEndingMode`) wieder her; `Backpack::ShowFixedSprites` blendet Blätter und Mats-Porträt wieder ein. Neustart per Screenshot mit normalem Spielstart verglichen.
- **Stolperfalle:** In PowerShell bricht `... | Select-Object -First N` das Asset-Skript mitten im Lauf ab (Modelle gelöscht, aber nicht neu erzeugt). Ausgabe lieber in eine Logdatei umleiten.

**Offen**
0. **Nächste Sitzung: Sound und Musik** (Tag 6).
1. Test durch User: Kuh läuft beim Abblenden weiter (Finale), Haare, Schatten, Blätter, Kuhpilz-Position.
2. Geburtstagsbotschaft, Name der Freundin, Spieltitel.

## Tag 6 – Mi 16.09.2026 (in Arbeit): Geräusche

**Entscheidung mit dem User:** SFX werden **synthetisiert** statt gesammelt. Alle vier gewünschten Geräusche (Laub, Wind, Knarzen, Papier) sind rauschbasiert, also genau das, was sich gut erzeugen lässt. Passt zur übrigen Pipeline (Modelle, UI, Buchseiten werden auch generiert), keine Lizenz-Buchhaltung, exakte Loop-Punkte, sofort nachregelbar. Rückfallplan: klingt ein Sound zu synthetisch, sucht der User einen CC0-Sample von freesound.org und er wird eingebaut.

**Erledigt**
- **Build:** `AUDIODIRS := audio`, `-lmm9` + `$(BLOCKSDS)/libs/maxmod` im Makefile. mmutil packt `audio/*.wav` in `soundbank.bin`, das per NitroFS im ROM landet (`mmInitDefault("nitro:/soundbank.bin")`). ROM 685 → 860 KB.
- `assets/audio/synth.py`: kleine Synthese-Bibliothek ohne numpy (Rauschen, Ein-Pol-/Biquad-/State-Variable-Filter, Hüllkurven, Korn-Wolken, Stick-Slip-Impulse, WAV-Writer mit `smpl`-Chunk).
- `assets/audio/gen_sfx.py` erzeugt 11 Samples, 8 Bit mono, zusammen **173 KB**:
  - `step1–4` (0,20 s, 16 kHz): Laubknistern als Korn-Wolke (Dichte bricht nach dem Auftreten zusammen) + Mittel-Scharren + weicher Erdaufschlag. 4 Varianten.
  - `amb_forest` (6,00 s, 11 kHz, **Loop**): Grundrascheln + tiefer Wind. Bewusst fast gleichmäßig.
  - `gust` (2,80 s): Bö durch die Kronen, wird zufällig über den Teppich gelegt.
  - `creak1–3` (1,70 s): Stick-Slip-Impulse durch Stammresonanzen, Impulse werden zum Ende langsamer (Holz setzt sich).
  - `page1–2` (0,34 s, 16 kHz): Papier-Körner durch einen mitlaufenden Bandpass, zwei Hücker (Blatt hebt, Blatt legt sich).
- `source/audio/AudioService`: startet die Ambience als Dauer-Loop und hält den Handle für die Lautstärke. Pro Frame: langsames Winddriften (zwei Perioden ~24 s und ~10 s, die nicht aufeinander passen), Bö alle 15–37 s, Knarzen alle 12–43 s – nachts alles 1,7× seltener und die Ambience leiser (Pegel siehe User-Test 1). One-Shots bekommen zufällige Tonhöhe/Lautstärke/Panorama.
- **Schritte:** `CharacterRig::StepTaken()` meldet den Frame, in dem ein Fuß aufsetzt (Extrem der Schwingphase, zwei pro Zyklus, erst ab `walkBlend_ > 0,3`). **Die Beine laufen schnell:** ein voller Zyklus pro 1,1 Einheiten = 20 Frames = **6 Fußaufsätze/s** – optisch abgenommen, als Klang aber ein Sprint. Deshalb klingt nur **jeder dritte** Aufsatz (`kFootfallsPerSound`): exakt 2 Schritte/s, weiterhin synchron zu einem sichtbaren Aufsetzen. Die Animation bleibt unverändert. `ExploreState` spielt sie: Nina laut, Mats (läuft hinterher) deutlich leiser und weiter aus der Mitte.
- **Umblättern:** `IdentifyState::TurnPage` spielt abwechselnd `page1`/`page2`.
- Asset-Pipeline: `tools/build_assets.sh` erzeugt die WAVs mit.

**Erkenntnisse**
- **mmutil liest Loop-Punkte** aus dem `smpl`-Chunk einer WAV-Datei (empirisch geprüft: Bank mit/ohne Chunk unterscheidet sich genau in `loop_start`/`length`, `looptype` 1). Damit braucht die Ambience kein Modul.
- **Ungerade Datenlänge bricht mmutil:** das RIFF-Pad-Byte nach einem ungeraden `data`-Chunk wird als nächster Chunk gelesen → `ERROR: Can't read input file` (die Datei landet trotzdem in der Bank). `write_wav` kürzt deshalb auf Vielfache von 8 Samples – das ist ohnehin die Wortausrichtung, die die Sound-Hardware für Loop-Punkte braucht.
- `mmEffectActive` gibt es in BlocksDS-maxmod **nicht**; der Ambience-Handle wird einfach nie freigegeben (`mmEffectRelease` nur für One-Shots, damit maxmod Kanäle recyceln kann).
- maxmod und Nitro Engine vertragen sich: `mmInitDefault` nach `irqSet(IRQ_VBLANK, NE_VBLFunc)` lässt NEs Handler in Ruhe, auf dem DS braucht der ARM9 kein `mmFrame()`.
- Nahtprüfung `amb_forest` (Werte der aktuellen Fassung: Sprung am Loop-Punkt 8, im Puffer median 10 / p99 38) – kein Klick. Erreicht durch zirkulär laufende Filter (Puffer zweimal durch, zweiter Durchlauf zählt), LFOs mit ganzzahliger Zyklenzahl (2, 5, 11 pro Loop) und Korn-Wolken, die über das Puffer-Ende hinaus vorne weiterlaufen.


**User-Test 1 (16.09.) → Ambience zu laut und zu aggressiv**
- Befund des User: „Das Rauschen ist noch viel zu laut und aggressiv und präsent, das soll mehr im Hintergrund laufen.“
- Zwei getrennte Ursachen:
  - **Spektrum:** Bett-Bandpass lag bei 3100 Hz, die Blatt-Ticks bei 4200 Hz – genau im empfindlichsten Ohrbereich (2–5 kHz). Das klingt nicht nach Wald, sondern nach Zischen. Jetzt Bett 1600 Hz, Ticks 2300 Hz (Dichte 55 → 24), Tiefpass 2400 Hz über die ganze Mischung, Blattanteile heruntergezogen (0,60/0,45 → 0,26/0,13) – der tiefe Wind trägt das Bett jetzt allein. Messung: 59 % der Energie unter 500 Hz, nur noch 13 % zwischen 2 und 5 kHz.
  - **Pegel:** Rauschen hat einen niedrigen Scheitelfaktor, deshalb ist ein Dauerteppich bei gleicher Lautstärke-Einstellung viel lauter als die kurzen Effekte darüber (Ambience-RMS war 33 gegen 12 der Bö). `kAmbienceByPhase` 165…106 → **68…42**, Winddriften ±15/±7 → ±7/±3, Bö-Lautstärke 70–120 → 52–84. Effektiver Pegel 21,5 → 6,7 (gut 10 dB leiser).
- Bö bekam dieselbe Behandlung schwächer dosiert (Helligkeitsverlauf 1700+2400 → 1200+1400 Hz, mehr Luft als Blatt).
- Loop-Naht nach dem zusätzlichen Tiefpass weiter sauber (Sprung 8, p99 38).
- **Merksatz:** Dauerteppiche gehören spektral unter den Präsenzbereich und brauchen eine deutlich niedrigere Lautstärke-Einstellung als One-Shots – gleiche Zahl heißt bei Rauschen nicht gleiche Lautheit.

**Offen**
1. **Test durch User: zweiter Durchgang** – Ambience jetzt leiser und dumpfer, Lautstärkeverhältnisse, ob die Schritte zu oft/zu selten kommen, ob Bö und Knarzen zu häufig sind. Falls die Schritte gegen die Beine „schwimmen“: Alternative wäre, die Animation zu verlangsamen (`kStrideLength` 1,1 → ~3,0) – ändert aber das abgenommene Laufbild.
2. Musik (Stimmung noch offen).
3. Shroomchen läuft ohne Huftritte; Glockengeläut, Pilz-Einsammeln und Fehler-Blatt haben noch keinen Sound – auf Wunsch nachziehbar.

## Tag 7 – Do 17.09.2026: Bugfixing

**Entscheidung mit dem User:** Sound ist „noch nicht sitzend", wird aber später manuell nachgezogen. Fokus jetzt auf Bugfixing.

### Textbox verschwand einfach (behoben)
**Ursache 1 – „gleicher Moment" war nicht derselbe Frame.** `DialogBox::Say` gruppierte Nachrichten über `stamp == frame_`, aber `frame_` wurde mitten in `ExploreState::Update` hochgezählt (in `dialog_.Update`). Alles, was *vorher* im selben Spielframe sprach (`backpack_.Update` → `OnItemGiven`, `HandleMapTouch` → Schrein/Pilz, `Enter` → `ApplyIdentifyResult`), bekam einen anderen Stempel als alles *danach* (`story_.Update`, `OnNearShrine`). Zwei Sätze aus derselben Szene galten damit als „alt" und „neu".

**Ursache 2 – die Folgen davon waren zu hart.** Eine „neue" Nachricht hat (a) *alle* wartenden Nachricht mit anderem Stempel **ersatzlos gelöscht** und (b) die laufende auf `kMinShownFrames` = 45 Frames (0,75 s) gekürzt. Typischer Fall: Nina läuft am Schrein vorbei (zwei Sätze in der Warteschlange), tippt einen Pilz an → Ninas zweiter Satz war weg und Mats' Schreinsatz nach 0,75 s auch.

**Neue Regel in `DialogBox`** (Stempel-Vergleich komplett raus):
- Reine FIFO-Warteschlange, es wird **nichts mehr still verworfen**. Nur zwei Ventile: Überlauf (7. Nachricht in einem Schwall → die älteste *wartende* fällt raus, die laufende bleibt) und `kStaleFrames` = 900 (eine Nachricht, die 15 s gewartet hat, gehört nicht mehr zur Szene).
- **Jede Nachricht bleibt mindestens `kMinShownFrames` = 60 Frames (1 s) stehen** – egal was dazwischenkommt, egal ob geskippt wird.
- Warten andere Nachrichten, wird die laufende auf höchstens `kQueuedReadingFrames` = 180 Frames (3 s) gekürzt statt auf 0,75 s. Ohne Wartende gilt weiter die volle Lesezeit (90 + 3 pro Zeichen, max. jetzt 300 statt 270).
- Helfer statt Inline-Logik: `StartCurrent`, `ShortenCurrent`, `Advance`, `DropOldestWaiting`, `DropStaleWaiting`.

### Skippen mit A
- `ExploreState::SkipPressed` – **A** oder (wie bisher) ein Tipp auf die Karte, der nicht schon von einem Pilz/Schrein verbraucht wurde. Gilt auch während des Finales.
- `kSkipGraceFrames` = 30: in der ersten halben Sekunde lässt sich eine Box nicht wegdrücken, damit sie nie nur aufblitzt.
- Aufforderungen (`Ask`) lassen sich nicht skippen – die warten weiter auf die Tat.
- **Kollision mit dem Laufen (vom User entschieden):** A war seit Tag 2 zugleich „nach rechts laufen" (gespiegelte ABXY-Steuerung, `InputService.cpp::kRightKeys`). Der User hat sich für **A = nur weiterklicken** entschieden, die **ABXY-Spiegelung ist ersatzlos raus** – gelaufen wird nur noch mit dem Steuerkreuz, B/X/Y sind frei. (Im Pilzbuch blättern Y/A weiterhin, dort läuft niemand.)

**Prüfung**
- Logik 1:1 nach Python übertragen (`scratchpad/sim_dialog.py`) und drei Fälle durchgerechnet: Spielstart (Satz 5 s → Aufforderung bleibt), Ereignis während laufendem Text (3 Sätze je 2,5–3,4 s statt „einer weg, einer 0,75 s"), Schwall von 7 (nur die zweite fällt raus). Kein Host-C++-Compiler vorhanden, deshalb der Umweg über Python.
- Build ohne Warnungen, melonDS-Screenshot: Startdialog läuft ab, Korb-Aufforderung bleibt stehen.
- **Merksatz:** Was „im selben Moment" passiert, darf nicht an einem Framezähler hängen, der mitten im Frame weiterzählt.


### Textbox flackerte / fehlte ganz – Vertex-RAM war voll (behoben)
**Befund des User:** „Die Textbox flackert oder taucht gar nicht richtig auf, gefühlt ab dem zweiten Sonnen-State."

**Messung statt Raten.** Debug-HUD um Höchstwerte erweitert (`RenderService::PeakPolygons/PeakVertices`) und einen Wegwerf-Build gebaut, der Nina automatisch im Kreis durch den Wald laufen lässt. Ergebnis nach ~75 s:

| | Polygone | Vertices | Objekte |
|---|---|---|---|
| Start-Lichtung, Bernstein | 1654 / 2048 | 5059 / 6144 | 37 |
| Start-Lichtung, Blaue Stunde (ohne Schatten) | 1352 | 4151 | 37 |
| **im dichten Wald (Maximum)** | **2037** | **6144 = Limit** | 53 |

**Ursache:** Nicht die Polygone, sondern der **Vertex-RAM** (6144) lief über. Was danach an die Grafikeinheit geht, wird verworfen – und `ExploreState::Draw3D` zeichnet `topText.Draw()` als **Letztes**. Deshalb traf es immer die Textbox, und zwar frameweise wechselnd = Flackern. Der Zusammenhang mit der Tageszeit: Schatten kosten 302 Polygone / 908 Vertices (8 Tris = 24 Vertices pro Schatten, `obj2dl` erzeugt Einzeldreiecke), und bis zum zweiten Sonnenstand ist man von der Lichtung in den dichten Wald gelaufen.

**Fix – hartes Budget im Wald** (`Forest::SelectVisible`): Statt „alles im Sichtfenster" werden nur noch die **`kMaxDrawnProps` = 36 nächsten** Objekte gezeichnet, nach Abstand sortiert (Einfüge-Auswahl, die weiteste fällt raus). Schatten bekommen nur die **18 nächsten** – weiter weg sind sie ohnehin im Nebel. `Draw` und `DrawShadows` teilen sich dieselbe Auswahl (wird pro Kamerastand einmal berechnet).

Ergebnis derselben Messfahrt: **Maximum 1661 Polygone / 5088 Vertices** bei offener Textbox – 19 % bzw. 17 % Luft. Optisch kein Unterschied: an der dichtesten Stelle fehlen die hintersten Bäume, die tief im Nebel stehen.

- **Debug-HUD dauerhaft erweitert:** Zeile 1/2 zeigen jetzt `Poly x/2048 max y` und `Vtx x/6144 max y`. Die Tastenzeile ist dafür weggefallen (SELECT = Zeit, R+SELECT = Nacht mit Ausrüstung, L+SELECT = Schlussbild, START = HUD).
- **Merksatz:** Beim DS zuerst die **Vertices** prüfen, nicht die Polygone – 6144 ist bei Einzeldreiecken früher erreicht als 2048. Und: Was zuletzt gezeichnet wird, verschwindet zuerst. UI-Overlays gehören deshalb unter ein garantiertes Budget.

### Ⓐ-Symbol an der Textbox
- Freier Schriftplatz: die NFLib-Schrift hat die Slots 114–127 leer. `assets/fonts/make_font_texture.py` malt dort ein 8×8 „A im Kreis" in den 3D-Schrift-Atlas (`TextDE_SlotButtonA` = 127, nur im Atlas, nicht in `default.fnt`).
- `TopTextService::ShowSkipHint` zeichnet das Symbol als kleines Schild (Rahmen-Quad + Pergament-Quad + Glyphe) an der **unteren rechten Ecke, unterhalb der letzten Textzeile** (y 48) – es verdeckt also nie Text.
- `DialogBox::CanSkip()` steuert es: erscheint erst, wenn die Nachricht wirklich überspringbar ist (nach `kSkipGraceFrames` = 30), und **nie bei `Ask`**, denn Aufforderungen warten auf die Tat. Im Emulator geprüft: Symbol beim Startsatz da, bei „Gibst du mir den Korb…?" weg.

**Offen**
1. Test durch User: Kommen Boxen jetzt vollständig und lange genug? Flackert nichts mehr? Fühlt sich A zum Skippen richtig an, ist das Ⓐ-Symbol groß genug?
2. Weitere Bugs sammeln.
3. Sound/Musik später manuell durch den User.

## Offene Fragen an den User
- Konsolen-Setup: **Flashcart** (Modell/Konsole noch offen, nicht dringend).
- Spieltitel, Name der Freundin, Text der Geburtstagsbotschaft (nötig für das Ende, Tag 5).
- Musikstimmung.

## Arbeitsregeln (für Claude)
- Höchstens **ein Agent** gleichzeitig, keine Multi-Agent-Workflows.
- **Nie codeberg.org** öffnen, sondern die GitHub-Spiegel nutzen.
- **Screenshots nur vom melonDS-Fenster** (seit Runde 6 erlaubt), keine sonstigen Bildschirmaufnahmen.
- Commits nur nach Rückfrage.
- **Keine Tutorial-/Tipp-Dialoge** – Hinweise nur in der Rolle der Figuren; Spieler soll selbst entdecken.
- Overlays auf dem oberen (3D-)Bildschirm immer als Nitro-Engine-2D-Quads zeichnen, keine 2D-BG-Ebenen.
