# riglayout

Génère des schémas SVG de machines musicales et de setups complets à partir de fichiers JSON. Les layouts d'appareils, les thèmes et les scènes sont de simples données : ajouter une machine ne demande pas de code.

Voir [JSON.md](JSON.md) pour le schéma des appareils, composants, icônes vectorielles, ports, thèmes et scènes.

## Installation

```powershell
python -m venv venv
.\venv\bin\Activate.ps1
pip install -r requirements.txt
```

## Rendu d'un appareil

```powershell
# Choix interactif du thème et nom de sortie automatique
python cli.py render devices/elektron/digitakt2.json

# Choisir directement un thème par son nom ou son chemin
python cli.py render devices/elektron/digitakt2.json --theme flat
python cli.py render devices/elektron/digitakt2.json --theme themes/flat.json

# Chemin de sortie personnalisé
python cli.py render devices/elektron/digitakt2.json --theme flat --output output/mon-export.svg

# Afficher les légendes et pictogrammes imprimés sur les commandes
python cli.py render devices/elektron/digitakt2.json --theme flat --detail
```

Sans `--output`, le fichier est écrit dans `output/<fabricant>-<modèle>-<thème>.svg`.

## Rendu d'une scène

```powershell
python cli.py render-scene scenes/nays_2026.json --theme flat
python cli.py render-scene scenes/nays_2026.json --theme flat --detail --output output/rig.svg
```

Une scène place plusieurs appareils (positions absolues en mm ou relatives à un autre appareil) et trace les câbles entre leurs ports comme dans la réalité : les câbles partent de la tranche des machines, en font le tour sans jamais passer dessus, et sont posés côte à côte quand ils suivent le même chemin. Leur couleur dépend du signal (audio, MIDI, USB, alimentation) et se règle dans le thème. Des appareils qui se superposent, un port utilisé deux fois ou un câble impossible à brancher arrêtent le rendu avec un message explicite.

La taille du SVG est calculée automatiquement. Sans `--output`, le fichier est écrit dans `output/scene-<nom du fichier>.svg`.

## Modèle des appareils

`label` décrit un composant pour les métadonnées et n'est jamais rendu. `legend` désigne le texte réellement imprimé sur une touche; `icon` ajoute un pictogramme à la place. Les icônes intégrées sont `play`, `record`, `stop`, `keyboard`, `perform`, `save_project`, `samples`, `metronome` et `arrow_up/down/left/right`; un pictogramme spécifique peut être fourni en path SVG (`icon_path_d`). `fill`, `stroke` et `legend_color` permettent les exceptions par composant (ex. la touche FUNC orange du Digitakt II). `--detail` (alias `--labels`) affiche les `legend` et icônes déclarés; sans option, le rendu reste minimal. Les thèmes règlent le style des légendes dans `labels` (`fill`, `font_family`, `font_size_mm`).

Les appareils définissent aussi leurs ports (`direction`, `signal`, position `x`/`y`), utilisés pour valider et tracer les connexions des scènes.

## Contenu

| Dossier | Contenu |
| --- | --- |
| `devices/` | Layouts : Elektron Digitakt II, Octatrack ; Roland JX-08, TB-3 |
| `themes/` | `dark_slate`, `flat` (Elektron Dark Pro), `outlined_dark`, `outlined_light` |
| `scenes/` | `nays_2026` |
| `output/` | SVG générés |
