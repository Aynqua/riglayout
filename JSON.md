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

`x` et `y` (facultatifs, normalisés entre `0` et `1`) placent le port sur l'appareil; ils servent de point d'ancrage aux câbles d'une scène. Par défaut `x = 0.5` et `y = 1.0` (bord inférieur); `y = 0.0` correspond au bord supérieur, où se trouve la connectique des machines vues de dessus.

## Thèmes

Un thème contient `name`, `background` et `components`. `components` associe un type de composant à `fill`, `stroke`, `stroke_width` et éventuellement `rx`. `labels` peut définir `fill`, `font_family` et `font_size_mm` pour les légendes. Un composant peut remplacer localement `fill` ou `stroke`.

Les pads utilisent le style `pad` du thème. Pour qu'ils aient le même aspect que les boutons, donne à `pad` les mêmes valeurs que `button`.

`cables` (facultatif) règle les câbles des scènes. Tous les champs ont une valeur par défaut, y compris chaque couleur prise séparément.

```json
{
  "cables": {
    "width_mm": 1.2,
    "spacing_mm": 2.2,
    "clearance_mm": 6.0,
    "corner_radius_mm": 1.5,
    "opacity": 0.95,
    "colors": {
      "audio": "#3b82f6",
      "midi": "#f59e0b",
      "usb": "#a855f7",
      "power": "#ef4444"
    }
  }
}
```

| Champ | Rôle |
| --- | --- |
| `width_mm` | Épaisseur d'un câble |
| `spacing_mm` | Distance d'axe à axe entre deux câbles parallèles; doit être au moins égale à `width_mm` |
| `clearance_mm` | Distance minimale entre un câble et un appareil |
| `corner_radius_mm` | Rayon des coudes (`0` pour des angles vifs) |
| `opacity` | Opacité des câbles, entre `0` et `1` |
| `colors` | Couleur par type de signal : `audio`, `midi`, `usb`, `power` |

## Scènes

Une scène positionne des instances de layouts et relie leurs ports. `device` est le chemin du JSON de layout, relatif au dossier depuis lequel la commande est lancée; `id` identifie une instance dans la scène.

```json
{
  "name": "Live",
  "devices": [
    {
      "id": "digitakt",
      "device": "devices/elektron/digitakt2.json",
      "position": {"type": "absolute", "x": 0, "y": 0}
    },
    {
      "id": "octatrack",
      "device": "devices/elektron/octatrack2.json",
      "position": {"type": "relative", "anchor": "right", "target": "digitakt", "spacing_mm": 10}
    }
  ],
  "connections": [
    {
      "source": {"device_id": "digitakt", "port_id": "midi-out"},
      "target": {"device_id": "octatrack", "port_id": "midi-in"}
    }
  ]
}
```

### Positions

- `absolute` : `x` et `y` en **millimètres**, coin supérieur gauche de l'appareil. Les valeurs négatives sont permises.
- `relative` : place l'appareil à côté de `target` (un autre `id` de la scène) selon `anchor` (`right` par défaut, `left`, `top`, `bottom`), avec un écart `spacing_mm` (15 par défaut). Les dépendances peuvent s'enchaîner; une dépendance circulaire ou une cible inconnue lève une erreur.

Deux appareils ne peuvent pas se superposer : le rendu s'arrête avec une erreur qui nomme les deux appareils. Ils peuvent se toucher.

La taille du SVG est calculée automatiquement à partir de l'encombrement des appareils et des câbles, avec une marge de 20 mm.

### Connexions

Une connexion relie un port source à un port cible. Le rendu vérifie :

- que les appareils et les ports existent ;
- le sens : source `output` ou `bidirectional`, cible `input` ou `bidirectional` ;
- que les deux ports ont le même `signal` ;
- qu'un port n'est utilisé que par un seul câble, et que deux câbles ne se branchent pas au même endroit (deux ports déclarés à la même position).

`label` est facultatif et n'est pas encore rendu.

### Câblage

Le câblage reproduit un branchement réel :

- un câble se branche sur la **tranche** de l'appareil, au bord le plus proche de la position `x`/`y` du port (`y = 0` → bord supérieur, `y = 1` → bord inférieur, `x = 0` → gauche, `x = 1` → droite), et en sort perpendiculairement ;
- il ne passe **jamais au-dessus d'un appareil** : il le contourne en restant à `clearance_mm` de ses bords. Si un port est trop proche d'un autre appareil pour y brancher un câble, le rendu s'arrête avec une erreur ;
- le trajet est à angles droits et cherche le plus court chemin avec le moins de coudes ;
- les câbles qui suivent le même chemin sont **côte à côte**, espacés de `spacing_mm`, dans un ordre qui limite les croisements ;
- la couleur dépend du `signal` des ports et vient du thème.

`--detail` affiche aussi les légendes des appareils dans une scène.