# Format JSON

Les layouts d'appareils et les scènes sont des fichiers JSON UTF-8. Les dimensions physiques et les tailles de composants sont en millimètres. Les positions `x` et `y` sont normalisées entre `0` et `1` et désignent le centre du composant.

## Layout d'appareil

Un layout décrit un appareil indépendamment de son apparence. `manufacturer`, `model` et `physical` sont requis. `components` et `ports` peuvent être omis; ils deviennent alors des listes vides.

```json
{
  "manufacturer": "Roland",
  "model": "Exemple",
  "physical": {
    "width_mm": 300,
    "height_mm": 100,
    "depth_mm": 45
  },
  "components": [],
  "ports": []
}
```

`physical.width_mm` et `physical.height_mm` doivent être positifs. `depth_mm` est facultatif.

## Composants

Tous les composants ont `type`, `x` et `y`. Les autres champs dépendent du type.

| Type | Champs géométriques requis |
| --- | --- |
| `frame` | `width_mm`, `height_mm` |
| `screen` | `width_mm`, `height_mm` |
| `button` | `width_mm`, `height_mm` |
| `pad` | `width_mm`, `height_mm` |
| `encoder` | `diameter_mm` |
| `led` | `diameter_mm` |
| `screw` | `diameter_mm` |
| `logo` | `width_mm`, `height_mm`, `icon_path_d`, `icon_view_box` |

Exemple de boutons et de commandes :

```json
{
  "components": [
    {
      "type": "button",
      "label": "Transport Play",
      "legend": "",
      "icon": "play",
      "x": 0.5,
      "y": 0.5,
      "width_mm": 15,
      "height_mm": 11
    },
    {
      "type": "pad",
      "label": "Pad 1",
      "legend": "1",
      "legend_bold": true,
      "underline": true,
      "x": 0.25,
      "y": 0.75,
      "width_mm": 16,
      "height_mm": 16
    }
  ]
}
```

### Texte et icônes

- `label` est une description destinée aux métadonnées; le renderer ne l'affiche pas.
- `legend` est le texte imprimé sur le composant. Les légendes des boutons et pads apparaissent avec `--detail` (alias `--labels`).
- `legend_bold`, `legend_font_size_mm`, `legend_color` et `underline` contrôlent la légende. Sa taille est réduite automatiquement si elle ne tient pas dans le composant.
- `legend_position` accepte `center` ou `bottom_left`; cette dernière position est utile pour un nom sur un `frame`.
- `icon` sélectionne une icône intégrée, par exemple `play`, `record`, `stop`, `keyboard`, `perform`, `save_project`, `samples`, `metronome`, `arrow_up`, `arrow_down`, `arrow_left` ou `arrow_right`.
- `icon_path_d` permet de définir un pictogramme avec un chemin SVG `d`. Il doit être accompagné de `icon_view_box`, un tableau `[x, y, largeur, hauteur]`.
- `icon_mode` vaut `fill` (par défaut) ou `stroke`. `icon_fill_rule` accepte `nonzero` (par défaut) ou `evenodd`, utile pour les logos avec des découpes.

Exemple de logo ou pictogramme défini dans les données, sans modifier le renderer :

```json
{
  "type": "logo",
  "label": "Logo constructeur",
  "icon_path_d": "M0 0H20V20H0Z M5 5V15H15V5Z",
  "icon_view_box": [0, 0, 20, 20],
  "icon_fill_rule": "evenodd",
  "x": 0.9,
  "y": 0.1,
  "width_mm": 12,
  "height_mm": 12
}
```

`fill` et `stroke` remplacent localement le style de forme du thème. Ils sont prévus pour les exceptions matérielles, par exemple FUNC orange. Les styles par défaut sont définis par type dans le thème.

## Ports

Les ports décrivent les entrées et sorties physiques ou logiques d'un appareil. Chaque `id` doit être unique dans le layout.

```json
{
  "ports": [
    {
      "id": "main-out-l",
      "label": "Main Out L",
      "direction": "output",
      "signal": "audio",
      "connector": "6.35mm TRS jack",
      "channels": 1,
      "balanced": true
    },
    {
      "id": "usb",
      "label": "USB 2.0",
      "direction": "input",
      "signal": "usb",
      "connector": "USB-B",
      "capabilities": ["audio", "midi", "overbridge"]
    },
    {
      "id": "power-in",
      "label": "12V DC In",
      "direction": "input",
      "signal": "power",
      "connector": "DC barrel jack",
      "voltage_v": 12
    }
  ]
}
```

`direction` vaut `input`, `output` ou `bidirectional`; `signal` vaut `audio`, `midi`, `usb` ou `power`. `connector`, `channels`, `balanced`, `voltage_v`, `current_a` et `capabilities` sont facultatifs. `channels` décrit le nombre de canaux sur le connecteur; `balanced` indique une liaison audio équilibrée; `voltage_v` et `current_a` décrivent une alimentation. `capabilities` est une liste ouverte pour les fonctions combinées comme MIDI Thru, DIN Sync ou Overbridge. Ces métadonnées n'empêchent pas les anciens ports `audio` et `midi` de rester valides.

## Thèmes

Un thème contient `name`, `background` et `components`. `components` associe un type de composant à `fill`, `stroke`, `stroke_width` et éventuellement `rx`. `labels` peut définir `fill`, `font_family` et `font_size_mm` pour les légendes. Un composant peut remplacer localement `fill` ou `stroke`.

Les pads utilisent le style `pad` du thème. Pour qu'ils aient le même aspect que les boutons, donne à `pad` les mêmes valeurs que `button`.

## Scènes

Une scène positionne des instances de layouts et relie leurs ports. `device` est le chemin du JSON de layout; `id` identifie une instance dans la scène.

```json
{
  "name": "Live",
  "devices": [
    {"id": "octatrack", "device": "devices/elektron/octatrack.json", "x": 0.25, "y": 0.5},
    {"id": "synth", "device": "devices/roland/exemple.json", "x": 0.75, "y": 0.5}
  ],
  "connections": [
    {
      "source": {"device_id": "octatrack", "port_id": "midi-out"},
      "target": {"device_id": "synth", "port_id": "midi-in"}
    }
  ]
}
```

Après chargement des layouts, `validate_scene_connections(scene, layouts_by_instance)` vérifie les appareils, les ports, le sens sortie-vers-entrée et la compatibilité des signaux. Les scènes sont modélisées et validables; leur rendu multi-appareils reste à implémenter.