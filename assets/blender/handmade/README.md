# Modelle von Hand in Blender bearbeiten

Normalerweise erzeugen die Python-Skripte in `assets/blender/` alle Modelle.
Eine `.blend` in diesem Ordner **überschreibt** einzelne Teile davon: beim
Bauen wird jedes Objekt mit der Eigenschaft `ds_export` über das erzeugte OBJ
gleichen Namens geschrieben.

> ⚠ Solange `characters.blend` hier liegt, kommen Nina und Mats **aus dieser
> Datei**. Änderungen in `models_characters.py` landen dann nicht mehr im
> Spiel. `tools/build_assets.sh` schreibt bei jedem Lauf mit, welche Teile aus
> einer `.blend` stammen (Zeilen `handmade …`).

## Einmal einrichten

Add-on installieren: Blender → *Bearbeiten → Einstellungen → Add-ons* →
Dropdown oben rechts → *Von Datenträger installieren…* →
`assets/blender/ds_palette_addon.py` → Haken setzen.

Es bringt den Reiter **DS** in die Seitenleiste der 3D-Ansicht (Taste `N`).

## Arbeiten

1. `assets/blender/handmade/characters.blend` öffnen. Nina und Mats stehen
   zusammengesetzt da, so wie das Spiel sie aufbaut.
2. Bearbeiten. Zum Sehen der Farben *Materialvorschau* einschalten
   (Taste `Z` → *Materialvorschau*).
3. Farbe ändern: Flächen auswählen → im DS-Panel auf ein Farbfeld klicken.
   Im Objektmodus färbt ein Klick das ganze Teil.
4. Im Panel *Teil* steht die Dreieckszahl und was noch nicht stimmt.
5. Speichern, dann `wf.cmd sh tools/build_assets.sh` und `build.cmd`.

## Regeln, die der DS erzwingt

- **Farbe kommt aus der UV**, nicht aus dem Material: obj2dl wirft Materialien
  weg, behält aber UVs. Deshalb das DS-Panel benutzen und nicht den
  Material-Reiter.
- **Der Objekt-Ursprung ist der Gelenkpunkt** (Hüfte, Schulter, Hals, Füße).
  Das Spiel hängt die Teile dort auf. Ein Teil im Objektmodus zu verschieben
  ändert im Spiel **nichts** – dafür die Vertices verschieben oder im Panel
  *Verschiebung ins Mesh übernehmen* drücken.
- **Keine Objekt-Drehung und -Skalierung** (Strg+A anwenden), sonst wandern sie
  beim Export unbemerkt ins Mesh.
- **Koordinaten innerhalb ±8** – weiter kann obj2dl nicht kodieren.
- **Dreiecke zählen:** jedes Dreieck kostet auf dem DS 3 Vertices, und pro Bild
  sind nur 2048 Polygone / 6144 Vertices da. Im Wald sind davon rund 1660
  belegt (Tag 7). Nina hat 260, Mats 322 Dreiecke; wer das verdoppelt, riskiert
  wieder eine flackernde Textbox.
- **Flach schattieren.** Der Rest des Spiels ist flach, glatte Flächen fallen auf.

Der zweite Arm und das zweite Bein sind in der Sammlung *Referenz* – dieselben
Meshes, nur ein zweites Mal aufgehängt. Das Spiel zeichnet sie genauso: ein
Modell, zweimal versetzt gezeichnet, nicht gespiegelt. Sie werden nicht
exportiert und ändern sich automatisch mit.

## Neu anfangen

```
blender --background --factory-startup --python assets/blender/make_handmade.py -- characters
```

Das baut die Datei aus den Python-Generatoren neu und **verwirft alle
Handarbeit darin**. Andere Gruppen gehen genauso: `items`, `mushrooms`,
`mushrooms_detail`, `world`, `cow`.

## Zurück zu den erzeugten Modellen

`.blend` aus diesem Ordner löschen (oder umbenennen, z. B. `.blend.aus`) –
dann gilt wieder das, was `models_*.py` erzeugt.
