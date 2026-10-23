# Codebase map — riglayout

> Référence fonction par fonction. Lire avant de modifier un module. Màj : 2026-10-23.

## Où travailler selon la feature

| Je veux… | Fichier(s) |
|---|---|
| Ajouter un champ JSON d'appareil / un type de composant | `renderer/models/device.py` (+ `device/draw.py`, thèmes, `JSON.md`) |
| Changer un style de thème / ajouter une clé de thème | `renderer/models/theme.py` + `themes/*.json` |
| Ajouter / modifier une icône intégrée | `renderer/device/icons.py` (registre `ICONS`) |
| Légendes : couleur, taille, position du texte | `renderer/device/legends.py` |
| Forme d'un composant | `renderer/device/draw.py` |
| Format d'une scène (positions, connexions) | `renderer/models/scene.py` |
| Règles de connexion (sens, signal) | `renderer/scene/validation.py` |
| Placement des appareils, taille de la scène | `renderer/scene/layout.py` |
| Tracé / couleur des câbles | `renderer/scene/cables.py` |
| Orchestration du rendu de scène, fond, ports | `renderer/scene/render.py` |
| Options CLI | `cli.py` |

Dépendances entre paquets (sens unique, pas de cycle) : `models` ← `device` ← `scene` ← `cli`.

## `cli.py` — CLI Typer

| Symbole | Rôle |
|---|---|
| `app = typer.Typer()` | 2 commandes → il faut **toujours** nommer la commande (`render …`) |
| `THEMES_DIR` | `<racine>/themes` (absolu, basé sur `__file__`) |
| `available_themes()` | `[(Path, name)]` triés, `name` lu dans le JSON (fallback `stem`) |
| `select_theme(opt)` | `opt` = chemin existant → ce chemin ; sinon match insensible à la casse sur `stem`, `name` de fichier ou `name` du thème ; `None` → prompt interactif numéroté. Erreurs → `typer.BadParameter` |
| `slugify(s)` | ASCII, minuscules, `-` — sert aux noms de sortie auto |
| `render(device_path, --theme/-t, --output/-o, --labels/--no-labels, --detail)` | Sortie défaut : `output/<slug(manufacturer-model)>-<slug(theme.name)>.svg` |
| `render_scene(scene_path, --theme/-t, --output/-o, --labels, --detail)` | Sortie défaut : `output/scene-<slug(stem)>.svg`. `show_labels = labels or detail` |

## `renderer/models/` — Modèles pydantic v1 (aucune dépendance au rendu)

`__init__.py` réexporte : `DeviceLayout`, `DevicePort`, `Theme`, `Scene`, `SceneConnection`, `SceneDevice`.

### `models/device.py`
- `PhysicalDimensions` : `width_mm`, `height_mm` (>0, requis), `depth_mm` (opt).
- `BaseComponent` (commun) : `x`, `y` ∈ [0,1] ; `label`, `legend`, `icon`, `icon_path_d`, `icon_view_box (x,y,w,h)`, `icon_fill_rule` (`nonzero|evenodd`), `icon_mode` (`fill|stroke`), `fill`, `stroke`, `legend_color`, `legend_position` (`center|bottom_left`), `legend_bold`, `legend_font_size_mm`, `underline`.
  - `root_validator validate_custom_icon` : `icon_path_d` et `icon_view_box` ensemble ; viewBox w/h > 0.
- Sous-types (champ `type` Literal) :
  - `EncoderComponent` (`diameter_mm`, `variant` inutilisé), `LEDComponent`, `ScrewComponent` → `diameter_mm`
  - `ButtonComponent` (`width_mm`, `height_mm`, `shape` inutilisé), `ScreenComponent`, `PadComponent`, `FrameComponent` → `width_mm`, `height_mm`
  - `LogoComponent` → `width_mm`, `height_mm` + validator : `icon_path_d`/`icon_view_box` obligatoires.
- `DevicePort` : `id`, `label`, `direction` (`input|output|bidirectional`), `signal` (`audio|midi|usb|power`), `connector`, `channels`, `balanced`, `voltage_v`, `current_a`, `capabilities: List[str]`, `x` (déf. 0.5), `y` (déf. 1.0).
- `Component = Union[...]`, `DeviceLayout` : `manufacturer`, `model`, `physical`, `components=[]`, `ports=[]`.

### `models/theme.py`
- `ComponentStyle` : `fill` (requis), `stroke="none"`, `stroke_width=0`, `rx=0`, `indicator_color` (inutilisé).
- `LabelStyle` : `fill=None` (→ couleur auto), `font_family="sans-serif"`, `font_size_mm=2.5`.
- `Theme` : `name`, `background: Dict[str, Any]` (clés lues : `fill`, `stroke`, `stroke_width`, `rx`), `components: Dict[type, ComponentStyle]`, `labels`.

### `models/scene.py`
`AbsolutePosition(type="absolute", x, y)` (mm), `RelativePosition(type="relative", anchor right|left|top|bottom, target, spacing_mm=15)`, `SceneDevice(id, device: chemin, position)`, `PortEndpoint(device_id, port_id)`, `SceneConnection(source, target, label?)`, `Scene(name, devices=[], connections=[])`.

## `renderer/device/` — Rendu d'un appareil

`__init__.py` réexporte `draw_device_to_group`, `render_svg`.

### `device/draw.py`
| Fonction | Rôle |
|---|---|
| `draw_device_to_group(container, layout, theme, show_labels)` | **Moteur partagé** appareil/scène. Coordonnées locales en mm (0,0 = coin haut-gauche). `logo` toujours dessiné (couleur `fill` ou `label_color`). Type sans style thème → ignoré. `screen/button/pad/frame` → `Rect` centré ; `encoder/led/screw` → `Circle` |
| `render_svg(device, theme, path, show_labels)` | SVG d'un appareil : fond (`background`, rx défaut 0) + `draw_device_to_group` + `save()` |

### `device/legends.py`
| Fonction | Rôle |
|---|---|
| `label_color(theme)` | `labels.fill` sinon : fond `none` → `background.stroke` ; sinon luminance du fond → `#111111` ou `#ffffff` |
| `default_control_font_size(comp, theme)` | `legend_font_size_mm` sinon min(thème, taille qui tient en largeur ≈ `0.62·len` et 55 % de la hauteur) |
| `add_control_legend(dwg, comp, theme, cx, cy)` | `frame` : texte `center` ou `bottom_left`. `button`/`pad` : priorité **icon_path_d > icon > legend** ; légende bold forcé pour `button` ; `underline` = `Line`. Autres types (encoder…) : **rien** |

### `device/icons.py`
| Symbole | Rôle |
|---|---|
| `ICONS: Dict[str, IconDrawer]` | **Registre** nom → `draw_xxx(dwg, center_x, center_y, width, height, color)` |
| `add_control_icon(dwg, icon, cx, cy, w, h, color)` | Cherche dans `ICONS` ; inconnu → `ValueError` |
| `draw_custom_icon(dwg, d, view_box, cx, cy, w, h, color, fill_rule, mode)` | Centre et met à l'échelle (contain) un path SVG ; `mode=stroke` → trait = 6 % de min(w,h) |
| `draw_device_logo(dwg, logo, cx, cy, color)` | Wrapper → `draw_custom_icon` |
| `draw_perform/save_project/samples/metronome` | Paths importés d'un SVG source, recentrés par `_source_group(source_box, …)` (échelle 55 %) |
| `draw_play/stop` | Paths outline 16×16 / 14×14 via `_draw_transport_path` |
| `draw_record`, `draw_keyboard`, `_arrow(points)` | Formes géométriques (`scale = 0.38·min(w,h)`, trait `0.18·scale`) |

Ajouter une icône : écrire `draw_xxx`, l'enregistrer dans `ICONS`, la lister dans `JSON.md` / `README.md`. Le test `test_every_builtin_icon_draws_something` la couvre automatiquement.

## `renderer/scene/` — Rendu de scène

`__init__.py` réexporte `render_scene_svg`, `validate_scene_connections`.

### `scene/validation.py`
`validate_scene_connections(scene, layouts_by_instance)` : ids d'instance uniques, layout présent, ids de port uniques par appareil, appareils/ports référencés existants, source ∈ {output, bidirectional}, cible ∈ {input, bidirectional}, **même `signal`**. Lève `ValueError` (messages FR).

### `scene/layout.py`
| Symbole | Rôle |
|---|---|
| `Rect` | alias `(x, y, w, h)` en mm, coordonnées de scène |
| `resolve_positions(scene, layouts) -> Dict[id, Rect]` | Absolues puis relatives en cascade (≤ `MAX_RESOLUTION_PASSES`=10 passes) ; aucun progrès → `ValueError` « dépendance circulaire » |
| `SceneBounds(width_mm, height_mm, offset_x, offset_y)` | NamedTuple |
| `compute_bounds(rects, padding_mm)` | bbox + marge ; offset = translation scène → SVG |

### `scene/cables.py`
| Symbole | Rôle |
|---|---|
| `STUB_LENGTH_MM=8`, `TRAY_OFFSET_MM=12`, `TRAY_SPACING_MM=3.5`, `CABLE_WIDTH_MM=2.5` | Constantes de routage |
| `cable_color(conn)` | `#e67e22` si `"midi"` dans **l'id du port source**, sinon `#3498db` |
| `cable_path(start, end, tray_y)` | Path orthogonal : stub → piste → horizontal → descente |
| `draw_cables(dwg, connections, port_coordinates, resolved_rects)` | Piste i = `top_source − 12 − i·3.5` (⚠ `top_source` en coordonnées de scène **non décalées**, alors que les ports sont en coordonnées SVG). `opacity=0.9` (utilisé par les tests pour repérer les câbles) |

### `scene/render.py`
| Symbole | Rôle |
|---|---|
| `SCENE_BACKGROUND = "#111111"` | Fond de scène (ne dépend pas du thème) |
| `load_scene(path)`, `load_scene_layouts(scene)` | Chargement JSON ; chemins `device` relatifs au **CWD** |
| `render_scene_svg(scene_path, output_path, theme, padding_mm=80, show_labels=False)` | load → scène vide = `ValueError` → validate → resolve_positions → compute_bounds → fond → par appareil `<g translate>` + rect fond thème (rx défaut 6) + `draw_device_to_group` + coordonnées des ports → `draw_cables` → `save()` + `print` taille |

## `tests/` — pytest (`./venv/bin/python.exe -m pytest`)

Indépendants du design des vrais appareils : pas de comparaison de SVG figés.

| Fichier | Couvre |
|---|---|
| `conftest.py` | `make_device()`, `port()`, `all_components()` (un composant par type + un bouton par icône de `ICONS`), fixtures `full_device`, `theme` (paramétrée sur tous les thèmes), `write_json` |
| `test_models.py` | Défauts, validations, enums fermés ; tous les `devices/` et `themes/` du projet se chargent |
| `test_scene_validation.py` | Connexions valides / invalides, doublons |
| `test_scene_layout.py` | Ancres relatives, cascade, cycles, bbox |
| `test_render.py` | Chaque icône dessine, icône inconnue, rendu complet × thèmes, légendes seulement en `--detail`, vrais appareils rendent sans erreur, scène (taille, 1 câble par connexion, couleurs) |
| `test_cli.py` | `slugify`, `select_theme` |

## Données

- **Appareils** : voir `JSON.md`. Ids de ports utilisés dans la scène : digitakt `midi-out`, `audio-out-l/r` ; octatrack `midi-in`, `midi-thru`, `audio-in-a..d` ; jx08 `midi-in/out`, `audio-out` ; tb3 `midi-in`, `audio-out`.
- **Thèmes** : clés `components` = `frame, screen, encoder, button, pad, led, screw`. `outlined_*` n'ont pas de `labels.fill` → couleur dérivée du `background.stroke`. ⚠ `flat.json` a pour nom "Elektron Dark Pro".
- **Scènes** : `position: {type, …}` (voir `JSON.md`).
