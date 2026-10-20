# Format des layouts

Voir [JSON.md](JSON.md) pour le schéma des appareils, composants, icônes vectorielles, ports et scènes.

python -m venv venv
.\venv\bin\Activate.ps1

# Choix interactif du thème et nom de sortie automatique
python cli.py devices/elektron/digitakt2.json

# Choisir directement un thème par son nom ou son chemin
python cli.py devices/elektron/digitakt2.json --theme flat
python cli.py devices/elektron/digitakt2.json --theme themes/flat.json

# Le chemin de sortie reste personnalisable
python cli.py devices/elektron/digitakt2.json --theme flat --output output/mon-export.svg

# Afficher les légendes et pictogrammes imprimés sur les commandes
python cli.py devices/elektron/digitakt2.json --theme flat --detail

## Modèle des appareils

`label` décrit un composant pour les métadonnées et n'est jamais rendu. `legend` désigne le texte réellement imprimé sur une touche; `icon` ajoute un pictogramme à la place. Les icônes disponibles comprennent le transport, les flèches, le clavier, Perform, Save Project, Samples et Tap Tempo. `fill`, `stroke` et `legend_color` permettent les exceptions par composant. `--detail` (alias `--labels`) affiche uniquement les `legend` et icônes déclarés; sans option, le rendu reste minimal. Les thèmes peuvent régler le style des légendes dans `labels` (`fill`, `font_family`, `font_size_mm`).

Le layout Digitakt II décrit notamment la touche FUNC orange, les pictogrammes de transport et de navigation monochromes, ainsi que les légendes PERFORM, SAVE PROJECT, SAMPLES, TAP TEMPO et KB SETUP. Play, Record et Stop sont tracés en outline; le clavier et les numéros soulignés des pads restent des formes SVG simples.

Les appareils peuvent aussi définir leurs ports. Les layouts existants restent valides et obtiennent une liste de ports vide par défaut.

```json
{
	"ports": [
		{"id": "audio-out", "label": "Audio Out", "direction": "output", "signal": "audio"},
		{"id": "midi-in", "label": "MIDI In", "direction": "input", "signal": "midi"}
	]
}
```

`direction` vaut `input` ou `output`; `signal` vaut `audio` ou `midi`.

## Scènes

Le module `renderer.scenes` définit les instances d'appareils positionnées dans une scène et les connexions entre leurs ports. Une connexion référence un appareil et un port source, puis un appareil et un port cible.

```json
{
	"name": "Live",
	"devices": [
		{"id": "drum-machine", "device": "devices/elektron/digitakt2.json", "x": 0.25, "y": 0.5},
		{"id": "synth", "device": "devices/synth/synth.json", "x": 0.75, "y": 0.5}
	],
	"connections": [
		{
			"source": {"device_id": "drum-machine", "port_id": "midi-out"},
			"target": {"device_id": "synth", "port_id": "midi-in"}
		}
	]
}
```

Après chargement des layouts référencés, `validate_scene_connections(scene, layouts_by_instance)` vérifie que les appareils et ports existent, que la source est une sortie, la cible une entrée, et que les deux ports utilisent le même type de signal. La scène est modélisée et validable; son rendu multi-appareils pourra être ajouté sans modifier les layouts individuels.