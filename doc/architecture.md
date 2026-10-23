# Architecture — riglayout

> Doc de référence pour Claude. Dernière mise à jour : 2026-10-23.

## But du projet

Générer des **schémas SVG vectoriels** de machines musicales (Elektron Digitakt II, Octatrack, Roland JX-08, TB-3…) à partir de **descriptions JSON** :
- vue de face d'un appareil seul (composants : boutons, pads, encodeurs, écran, LEDs, vis, cadres, logo) ;
- **scène** = plusieurs appareils positionnés + câbles MIDI/audio entre leurs ports (« rig layout »).

Séparation stricte **données (layouts JSON) / apparence (thèmes JSON) / moteur (Python)**.

## Stack

| Élément | Choix | Remarque |
|---|---|---|
| Langage | Python 3.11 | venv local dans `venv/` (layout `venv/bin/…`), ignoré par git |
| Validation | **pydantic 1.10** (v1 !) | `root_validator`, `Field(...)`, `Model(**dict)`. Ne pas utiliser l'API v2 (`model_validator`, `model_dump`) |
| SVG | svgwrite 1.4.3 | unités = mm (viewBox en mm, `size="…mm"`) |
| CLI | typer 0.27 (+ rich) | |
| Tests | pytest 9.1 | `tests/`, config `pytest.ini` (`pythonpath = .`) |
| Dépendances | `requirements.txt` / `requirements-dev.txt` | `pydantic==1.10.26 svgwrite==1.4.3 typer==0.27.3` ; dev : `+ pytest==9.1.1` |

Lancer : `.\venv\bin\python.exe cli.py <commande> ...` (ou activer `.\venv\bin\Activate.ps1`).
Sous Git Bash, préfixer `PYTHONIOENCODING=utf-8` sinon l'emoji ✅ du `typer.echo` final lève `UnicodeEncodeError` (le SVG est déjà écrit à ce moment-là).

## Arborescence

```
cli.py                 Point d'entrée Typer : commandes `render` et `render-scene`
renderer/
  __init__.py          vide
  models/              Modèles pydantic, aucune dépendance au rendu
    device.py          DeviceLayout, composants, ports
    theme.py           Theme, ComponentStyle, LabelStyle
    scene.py           Scene, positions, connexions
  device/              Rendu d'un appareil
    draw.py            draw_device_to_group (moteur partagé), render_svg
    legends.py         Couleur / taille / placement des légendes
    icons.py           Registre ICONS des pictogrammes + icônes custom par path SVG
  scene/               Rendu de scène
    validation.py      validate_scene_connections
    layout.py          Positions absolues/relatives, encombrement
    cables.py          Routage et couleur des câbles
    render.py          Orchestration render_scene_svg
tests/                 pytest, indépendants du design des vrais appareils
devices/<marque>/*.json   Layouts d'appareils (données)
  elektron/digitakt2.json   Digitakt II (215×176 mm, ~68 composants, 10 ports)
  elektron/octatrack2.json  Octatrack (340×176 mm, ~79 composants, 14 ports) — remplace octatrack.json (supprimé)
  roland/jx-08.json         JX-08 (300×128 mm, maquette simplifiée)
  roland/tb-3.json          TB-3 (240×173 mm, maquette simplifiée)
themes/*.json          Thèmes : dark_slate, flat ("Elektron Dark Pro"), outlined_dark, outlined_light
scenes/*.json          Scènes : nays_2026.json ("Live Rig Principal", 4 appareils, 7 câbles)
output/*.svg           SVG générés (versionnés, pas forcément à jour ; contient un doublon "… copy.svg")
README.md, JSON.md     Doc utilisateur (FR) : usage CLI / schéma JSON
requirements*.txt      Dépendances épinglées (runtime / dev)
pytest.ini             Config pytest
.gitignore             venv/, __pycache__/, *.pyc, .pytest_cache/
CLAUDE.md              Pointeur vers doc/ pour Claude
doc/                   Cette doc technique
```

## Flux de données

### Appareil seul (`cli.py render`)
```
device.json ──json.load──> DeviceLayout(**data)   (pydantic, validation)
theme (nom|chemin|prompt) ──select_theme──> Theme(**data)
render_svg(device, theme, out, show_labels)
   ├─ Rect de fond = theme.background
   └─ draw_device_to_group(dwg, layout, theme, show_labels)
         pour chaque composant : forme selon type + style thème (override fill/stroke composant)
         si show_labels : add_control_legend → texte | icône intégrée | icône custom
```

### Scène (`cli.py render-scene`)
```
render.load_scene / load_scene_layouts    (chemins device relatifs au CWD, pas au fichier scène)
validation.validate_scene_connections
layout.resolve_positions                  (absolute | relative en cascade, max 10 passes)
layout.compute_bounds                     (bbox + padding_mm 80 → taille SVG + offset)
render : par appareil <g translate> + Rect fond thème + device.draw_device_to_group
         + coordonnées absolues des ports (port.x/y normalisés sur l'appareil)
cables.draw_cables                        (tracé orthogonal "goulotte" au-dessus de l'appareil source)
```

Dépendances entre paquets à sens unique : `models` ← `device` ← `scene` ← `cli`. Un module de `models/` n'importe jamais `device/` ou `scene/`.

## Conventions de coordonnées (essentiel)

- **Toutes les tailles en millimètres**; le SVG a `viewBox="0 0 W H"` en mm → 1 unité = 1 mm.
- `x`, `y` des composants **et des ports** : normalisés `[0,1]` sur l'appareil, **centre** du composant. Origine en haut à gauche. Port `y=0.0` = bord haut (face arrière vue de dessus), défaut `y=1.0`.
- Scène : `AbsolutePosition.x/y` en **mm**, coin **haut-gauche** de l'appareil, valeurs négatives permises (la bbox est recalée). `RelativePosition` : collé à `target` sur `anchor` avec `spacing_mm`.

## Choix techniques notables

- **Données pilotent le rendu** : un nouvel appareil = un JSON, pas de code. Logos/pictos spécifiques via `icon_path_d` + `icon_view_box` dans le JSON.
- `label` = métadonnée jamais rendue ; `legend` = texte imprimé, rendu seulement avec `--detail`/`--labels`.
- Le thème définit un style **par type de composant** ; un type absent du thème n'est **pas dessiné** (sauf `logo`, toujours dessiné).
- pydantic v1 ignore les champs inconnus (ex. `"name"` dans les JSON Roland) → pas d'erreur.
- `Component` est une `Union` discriminée de fait par `type: Literal[...]` (pydantic v1 essaie chaque modèle dans l'ordre).
