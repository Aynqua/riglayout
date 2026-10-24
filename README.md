# riglayout

Génère des schémas SVG (et PNG transparents) de machines musicales et de setups complets à partir de fichiers JSON. Les layouts d'appareils, les thèmes et les scènes sont de simples données : ajouter une machine ne demande pas de code.

Voir [JSON.md](JSON.md) pour le schéma des appareils, composants, icônes vectorielles, ports, thèmes et scènes.

## Installation

Python 3.13 officiel (python.org) requis : le rendu PNG utilise une bibliothèque précompilée qui n'existe pas pour le Python de MSYS2.

```powershell
py -3.13 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt        # ou requirements-dev.txt pour lancer les tests
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

# Mode détail : légendes, pictogrammes, ports et leurs noms
python cli.py render devices/elektron/digitakt2.json --theme flat --detail

# PNG transparent en plus du SVG (300 dpi par défaut)
python cli.py render devices/elektron/digitakt2.json --theme flat --png --dpi 600
```

## Rendu d'une scène

```powershell
python cli.py render-scene scenes/nays_2026.json --theme flat
python cli.py render-scene scenes/nays_2026.json --theme flat --detail --png
```

Une scène place plusieurs appareils (positions absolues en mm ou relatives à un autre appareil) et trace les câbles entre leurs ports comme dans la réalité : les câbles partent de la tranche des machines, en font le tour sans jamais passer dessus, et sont posés côte à côte quand ils suivent le même chemin. Leur couleur dépend du signal (audio, MIDI, USB, alimentation) et se règle dans le thème. En mode `--detail`, les ports sont nommés et les câbles qui ont un `label` l'affichent. Des appareils qui se superposent, un port utilisé deux fois ou un câble impossible à brancher arrêtent le rendu avec un message explicite.

Les chemins des appareils dans une scène sont relatifs au fichier de scène. La scène n'a pas de fond : le SVG et le PNG sont transparents, prêts pour l'impression.

## Texte et titres

```powershell
# Texte direct : **gras**, le reste fin ; lignes séparées par |
python cli.py render-text --text "**NAYS** LIVE SETUP|DIGITAKT II · OCTATRACK MKII" --theme tshirt_dark --png

# Texte décrit en JSON (tailles, espacements, graisses par ligne)
python cli.py render-text texts/nays_live_setup.json --theme tshirt_dark --print-width 20
```

Le SVG est recadré au plus juste sur le texte. Une scène peut aussi avoir un titre (`title`), voir [JSON.md](JSON.md).

## Impression sur t-shirt

```powershell
python cli.py render-scene scenes/nays_2026_portrait.json --theme tshirt_dark --print-width 28
```

`--print-width` (en cm) active le mode impression : le PNG transparent est produit exactement à cette largeur, à 300 dpi, et la commande vérifie qu'une fois réduits les traits restent ≥ 0,5 mm et les textes ≥ 2,1 mm (seuils courants en DTF/DTG, à confirmer avec l'imprimeur). Les formes pleines (logos, pictogrammes) sont aussi contrôlées sur l'image finale : les zones trop fines sont listées et montrées en rouge dans `…-controle.png`. Les **espaces entre traits** trop étroits (moins de 0,5 mm imprimés, qui risquent de se boucher quand l'encre s'étale) sont signalés en bleu dans `…-espaces.png` ; ceux autour des textes (souvent l'intérieur des lettres) sont donnés à titre indicatif dans `…-espaces-textes.png`.

Le thème `tshirt_dark` est pensé pour un t-shirt noir : traits clairs épais, LED en points rouges pleins, sans vis, câbles épais et opaques, graisse minimale des textes (`labels.min_font_weight`).

## Tout générer

```powershell
python cli.py render-all                 # toutes les machines et scènes, tous les thèmes, avec et sans --detail (SVG)
python cli.py render-all --png           # idem + PNG transparents (300 dpi, ~4 min)
python cli.py render-all --theme flat    # limité à un thème
```

Un rendu en erreur n'arrête pas les autres : ils sont listés à la fin et la commande sort en erreur.

## Fichiers de sortie

Sans `--output`, chaque machine a son dossier dans `output/`, et chaque scène le sien dans `output/scenes/`. Chaque thème et chaque mode a son propre fichier :

| Rendu | Fichier |
| --- | --- |
| Appareil | `output/<fabricant>-<modèle>/<fabricant>-<modèle>-<thème>.svg` |
| Appareil, `--detail` | `output/<fabricant>-<modèle>/<fabricant>-<modèle>-<thème>-detail.svg` |
| Scène | `output/scenes/<nom du fichier>/scene-<nom du fichier>-<thème>.svg` |
| Scène, `--detail` | `output/scenes/<nom du fichier>/scene-<nom du fichier>-<thème>-detail.svg` |

Avec `--png`, un `.png` du même nom est écrit à côté du SVG.

## Modèle des appareils

`label` décrit un composant pour les métadonnées et n'est jamais rendu. `legend` désigne le texte réellement imprimé sur une touche; `icon` ajoute un pictogramme à la place. Les icônes intégrées sont `play`, `record`, `stop`, `keyboard`, `perform`, `save_project`, `samples`, `metronome` et `arrow_up/down/left/right`; un pictogramme spécifique peut être fourni en path SVG (`icon_path_d`). `fill`, `stroke` et `legend_color` permettent les exceptions par composant (ex. la touche FUNC orange du Digitakt II). `--detail` (alias `--labels`) affiche les `legend`, icônes et ports déclarés; sans option, le rendu reste minimal. Les thèmes règlent le style des légendes dans `labels` (`fill`, `font_family`, `font_size_mm`).

Les appareils définissent aussi leurs ports (`direction`, `signal`, position `x`/`y`), utilisés pour valider et tracer les connexions des scènes.

## Contenu

| Dossier | Contenu |
| --- | --- |
| `devices/` | Layouts : Elektron Digitakt II, Octatrack ; Roland JX-08, TB-3 |
| `themes/` | `dark_slate`, `flat` (Elektron Dark Pro), `outlined_dark`, `outlined_light`, `tshirt_dark` (impression sur t-shirt noir) |
| `scenes/` | `nays_2026` et ses variantes de mise en page : `_bloc` (affiche paysage), `_carre` (t-shirt), `_portrait`, `_bandeau` (panoramique), `_colonne` (verticale), `_tshirt` (portrait + titre) |
| `texts/` | Titres : `nays_live_setup` |
| `output/` | SVG et PNG générés |
