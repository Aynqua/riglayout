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
| `text` | `legend` (le texte) |

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
- `legend_spans` découpe la légende en morceaux de styles différents; `legend` devient alors leur concaténation. Chaque morceau a `text` et, en option, `weight` (graisse CSS de `100`, très fin, à `900`, très gras), `font_family`, `color` et `font_size_mm`. Les espaces en début de morceau sont conservés.
- `font_family` choisit la police de la légende (liste de repli CSS, ex. `"Helvetica Neue, Arial, sans-serif"`); par défaut, celle du thème. Le PNG utilise les polices installées sur la machine qui fait le rendu.

```json
{
  "legend_spans": [
    {"text": "Octatrack", "weight": 700},
    {"text": " MKII", "weight": 200, "font_family": "Helvetica Neue, Segoe UI, Arial, sans-serif"}
  ],
  "font_family": "Helvetica Neue, Arial, sans-serif"
}
```

- `legend_letter_spacing_em` espace les lettres de la légende (en fraction de sa taille).
- `legend_always: true` affiche la légende même sans `--detail` : pour ce qui est imprimé sur la machine elle-même (nom du modèle, marque), par exemple le nom sous l'écran du Digitakt II.
- `legend_position` accepte `center` ou `bottom_left`; cette dernière position est utile pour un nom sur un `frame`.
- `icon` sélectionne une icône intégrée, par exemple `play`, `record`, `stop`, `keyboard`, `perform`, `save_project`, `samples`, `metronome`, `arrow_up`, `arrow_down`, `arrow_left` ou `arrow_right`.
- `icon_path_d` permet de définir un pictogramme avec un chemin SVG `d`. Il doit être accompagné de `icon_view_box`, un tableau `[x, y, largeur, hauteur]`.
- `icon_mode` vaut `fill` (par défaut) ou `stroke`. En `stroke`, `icon_stroke_width` donne l'épaisseur du trait dans les unités de `icon_view_box` (la valeur `stroke-width` du SVG d'origine). `icon_linecap` règle les extrémités des traits : `round` (par défaut), `butt` (coupées droit, comme l'emblème Roland) ou `square`.
- Le path peut être copié tel quel depuis un fichier SVG, y compris en notation compacte (`a15 15 0 0 1 15-15`). Un logo fait de plusieurs `<path>` se déclare en **liste** : `"icon_path_d": ["m192 22.7…", "m226.5 80.7…"]`, chaque `d` copié tel quel. Ne pas les concaténer en une seule chaîne : le `m` minuscule qui ouvre un path deviendrait relatif au path précédent. `icon_fill_rule` accepte `nonzero` (par défaut) ou `evenodd`, utile pour les logos avec des découpes.

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

### Inscriptions imprimées (`text`)

Le type `text` représente ce qui est sérigraphié sur la machine : marque, nom du modèle, titres de sections. Il est **toujours affiché**, avec ou sans `--detail`.

```json
{
  "type": "text",
  "label": "Model Name",
  "legend": "TB-3",
  "x": 0.801,
  "y": 0.068,
  "text_anchor": "start",
  "legend_bold": true,
  "legend_font_size_mm": 8.0,
  "width_mm": 37.0
}
```

- `x`/`y` désignent le point d'ancrage, sur la ligne médiane du texte; `text_anchor` vaut `start`, `middle` (par défaut) ou `end`.
- `width_mm` (facultatif) étire ou resserre le texte à cette largeur exacte, pratique pour imiter une typo large ou condensée.
- `detail_only: true` réserve l'inscription au mode `--detail` (texte trop petit pour la vue d'ensemble, ex. « POLYPHONIC SYNTHESIZER » du JX-08).
- `font_family` (facultatif) remplace la police du thème; `legend_color`, `legend_bold`, `legend_font_size_mm` s'appliquent comme pour une légende.

Pour un logo de marque, préférer le tracé officiel en `logo` (ex. le mot « Roland » du TB-3 et du JX-08, issu de Wikimedia Commons) ; le type `text` sert aux inscriptions typographiques (« TB-3 », « TOUCH BASSLINE »…).

### Variantes (écran / impression)

Un composant peut changer selon la variante du thème (`"variant"` dans le thème : `screen` par défaut, `print` pour `tshirt_dark`). `variants` associe une variante aux champs à redéfinir, ou à `"hidden": true` pour masquer le composant :

```json
{"type": "logo", "label": "Roland Emblem", "variants": {"print": {"hidden": true}}}
{"type": "logo", "label": "Roland Wordmark", "x": 0.1114, "variants": {"print": {"x": 0.0842, "width_mm": 32.5, "height_mm": 7.06}}}
```

Sur le TB-3 et le JX-08, la version t-shirt masque l'emblème Roland, trop fin pour l'impression, et place le mot « Roland » à sa place.

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

`label` est le nom affiché en mode `--detail`. `x` et `y` (facultatifs, normalisés entre `0` et `1`) placent le port sur l'appareil; ils servent de point d'ancrage aux câbles d'une scène. Par défaut `x = 0.5` et `y = 1.0` (bord inférieur); `y = 0.0` correspond au bord supérieur, où se trouve la connectique des machines vues de dessus.

## Thèmes

Un thème contient `name`, `background` et `components`. Un type de composant absent de `components` n'est pas dessiné (ex. `tshirt_dark` n'a pas de `screw` : pas de vis). `labels.min_font_weight` impose une graisse minimale à tous les textes, utile pour l'impression où les graisses très fines disparaissent. `components` associe un type de composant à `fill`, `stroke`, `stroke_width` et éventuellement `rx`. `labels` peut définir `fill`, `font_family` et `font_size_mm` pour les légendes. Un composant peut remplacer localement `fill` ou `stroke`.

Les pads utilisent le style `pad` du thème. Pour qu'ils aient le même aspect que les boutons, donne à `pad` les mêmes valeurs que `button`.

`ports` (facultatif) règle l'affichage des ports en mode `--detail` : un cercle sur la tranche de l'appareil et le nom (`label`) du port, écrit vers l'intérieur.

```json
{
  "ports": {
    "marker_radius_mm": 1.0,
    "stroke_width_mm": 0.3,
    "font_size_mm": 1.6,
    "label_gap_mm": 0.8
  }
}
```

`fill` (facultatif) fixe leur couleur; par défaut, c'est celle des légendes.

`cables` (facultatif) règle les câbles des scènes. Tous les champs ont une valeur par défaut, y compris chaque couleur prise séparément.

```json
{
  "cables": {
    "width_mm": 1.2,
    "spacing_mm": 2.2,
    "clearance_mm": 6.0,
    "corner_radius_mm": 1.5,
    "opacity": 0.95,
    "label_font_size_mm": 2.0,
    "colors": {
      "audio": "#3b82f6",
      "midi": "#ef4444",
      "usb": "#a855f7",
      "power": "#facc15"
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
| `label_font_size_mm` | Taille du nom d'un câble (mode détail) |
| `colors` | Couleur par type de signal : `audio`, `midi`, `usb`, `power` |

## Scènes

Une scène positionne des instances de layouts et relie leurs ports. `device` est le chemin du JSON de layout, relatif au **dossier du fichier de scène** (ex. `../devices/...` pour une scène dans `scenes/`); `id` identifie une instance dans la scène.

```json
{
  "name": "Live",
  "devices": [
    {
      "id": "digitakt",
      "device": "../devices/elektron/digitakt2.json",
      "position": {"type": "absolute", "x": 0, "y": 0}
    },
    {
      "id": "octatrack",
      "device": "../devices/elektron/octatrack2.json",
      "position": {"type": "relative", "anchor": "right", "target": "digitakt", "spacing_mm": 10}
    }
  ],
  "connections": [
    {
      "source": {"device_id": "digitakt", "port_id": "midi-out"},
      "target": {"device_id": "octatrack", "port_id": "midi-in"},
      "label": "MIDI Clock"
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

`label` est facultatif : en mode `--detail`, il est écrit le long du câble, dans sa couleur, à un endroit où il ne recouvre ni un autre câble ni un appareil.

### Câblage

Le câblage reproduit un branchement réel :

- un câble se branche sur la **tranche** de l'appareil, au bord le plus proche de la position `x`/`y` du port (`y = 0` → bord supérieur, `y = 1` → bord inférieur, `x = 0` → gauche, `x = 1` → droite), et en sort perpendiculairement ;
- il ne passe **jamais au-dessus d'un appareil** : il le contourne en restant à `clearance_mm` de ses bords. Si un port est trop proche d'un autre appareil pour y brancher un câble, le rendu s'arrête avec une erreur ;
- le trajet est à angles droits et cherche le plus court chemin avec le moins de coudes ;
- les câbles qui suivent le même chemin sont **côte à côte**, espacés de `spacing_mm`, dans un ordre qui limite les croisements ;
- la couleur dépend du `signal` des ports et vient du thème.

`--detail` affiche aussi, dans une scène, les légendes des appareils, chaque port (cercle sur la tranche et nom) et les noms des câbles.

La scène n'a pas de fond : le SVG (et le PNG avec `--png`) est transparent.

## Textes (titres)

Un bloc de texte (fichier `texts/*.json`, ou champ `title` d'une scène) est une liste de lignes. Dans chaque ligne, le texte entre `**` est en gras, le reste dans la graisse fine : `**NAYS** LIVE SETUP`.

```json
{
  "lines": [
    {"text": "**NAYS** LIVE SETUP", "size_mm": 22, "letter_spacing_em": 0.1},
    {"text": "DIGITAKT II · OCTATRACK MKII · JX-08 · TB-3", "size_mm": 5, "letter_spacing_em": 0.32, "regular_weight": 400}
  ],
  "font_family": "Helvetica Neue, Arial, sans-serif",
  "bold_weight": 700,
  "regular_weight": 200,
  "line_gap_em": 1.6,
  "align": "center"
}
```

| Champ | Rôle |
| --- | --- |
| `lines` | Lignes : une chaîne, ou un objet avec `text` et, en option, `size_mm`, `letter_spacing_em`, `bold_weight`, `regular_weight`, `font_family`, `color` (remplacent les valeurs du bloc) |
| `font_family` | Police (liste de repli CSS) |
| `size_mm` | Taille de police par défaut (12) |
| `letter_spacing_em` | Espacement des lettres, en fraction de la taille (0,08) |
| `bold_weight` / `regular_weight` | Graisses du texte `**gras**` et du reste (700 / 200) |
| `line_gap_em` | Espace entre deux lignes, en fraction de la taille de la ligne suivante |
| `align` | `left`, `center` (défaut) ou `right` |
| `color` | Couleur ; par défaut celle des légendes du thème |
| `uppercase` | Met tout en majuscules |

L'alignement et le recadrage sont mesurés sur le rendu réel : ils sont exacts quelles que soient la police et l'espacement.

Dans une scène, `title` place le bloc centré au-dessus des machines et des câbles, à `title_gap_mm` (20 par défaut) ; la taille de l'image en tient compte. Exemple : `scenes/nays_2026_tshirt.json`.

