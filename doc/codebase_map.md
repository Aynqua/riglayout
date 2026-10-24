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
| Ports d'un appareil (bord, prise, nom) | `renderer/device/ports.py` + bloc `ports` du thème |
| Export PNG | `renderer/export.py` + options `--png` / `--dpi` de `cli.py` |
| Noms de fichiers de sortie | `cli.default_output_path` |
| Format d'une scène (positions, connexions) | `renderer/models/scene.py` |
| Règles de connexion (sens, signal, port unique) | `renderer/scene/validation.py` |
| Placement des appareils, chevauchements, taille de la scène | `renderer/scene/layout.py` |
| Où un câble se branche sur une machine | `renderer/scene/cabling/anchors.py` |
| Couloirs autorisés autour des machines | `renderer/scene/cabling/grid.py` |
| Choix du trajet (longueur, coudes) | `renderer/scene/cabling/router.py` |
| Écartement des câbles parallèles, ordre des voies | `renderer/scene/cabling/nudging.py` |
| Aspect SVG d'un câble (coudes, prises) | `renderer/scene/cabling/draw.py` |
| Placement du nom d'un câble | `renderer/scene/cabling/labels.py` |
| Couleurs / épaisseur / espacement des câbles | `themes/*.json` → bloc `cables` (`CableStyle` dans `models/theme.py`) |
| Orchestration du rendu de scène, chargement des layouts | `renderer/scene/render.py` |
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
| `default_output_path(name, theme, detail, folder)` | `<folder>/<slug(name)>-<slug(theme.name)>[-detail].svg` — un fichier par thème et par mode |
| `device_output_folder(device)`, `scene_output_folder(scene_path)` | `output/<fabricant>-<modèle>/` et `output/scenes/<slug(stem)>/` (`OUTPUT_DIR` relatif au dossier courant) |
| `ROOT_DIR`, `DEVICES_DIR`, `SCENES_DIR` | Dossiers du projet (absolus) |
| `load_theme(path)`, `render_device_file(path, theme, detail, output?)`, `render_scene_file(path, theme, detail, output?)` | Rendu d'un fichier → chemin SVG écrit ; partagés par toutes les commandes |
| `render_text(texte JSON ou --text, --font, --size, --spacing, --theme, -o, --png, --dpi, --print-width)` (`render-text`) | `output/texts/<nom>/<nom>-<thème>.svg` ; `--text` : lignes séparées par `|` |
| `render_all(--theme?, --png, --dpi)` (`render-all`) | Machines + scènes × thèmes × (sans, avec détail) + textes `texts/*.json` × thèmes ; continue en cas d'erreur, liste les échecs, code 1 s'il y en a |
| `export_png(svg_path, dpi)` | `.png` à côté du SVG via `renderer.export.svg_to_png` |
| `render(device_path, --theme/-t, --output/-o, --labels/--no-labels, --detail, --png, --dpi)` | Nom : `default_output_path("<manufacturer>-<model>", …)` |
| `render_scene(scene_path, --theme/-t, --output/-o, --labels, --detail, --png, --dpi)` | Nom : `default_output_path("scene-<stem>", …)`. `show_labels = labels or detail` |

## `renderer/models/` — Modèles pydantic v1 (aucune dépendance au rendu)

`__init__.py` réexporte : `DeviceLayout`, `DevicePort`, `Theme`, `Scene`, `SceneConnection`, `SceneDevice`.

### `models/device.py`
- `PhysicalDimensions` : `width_mm`, `height_mm` (>0, requis), `depth_mm` (opt).
- `BaseComponent` (commun) : `x`, `y` ∈ [0,1] ; `label`, `legend`, `icon`, `icon_path_d`, `icon_view_box (x,y,w,h)`, `icon_fill_rule` (`nonzero|evenodd`), `icon_mode` (`fill|stroke`), `icon_stroke_width` (unités du view_box, mode stroke), `icon_linecap` (`round|butt|square`), `fill`, `stroke`, `legend_color`, `legend_position` (`center|bottom_left`), `legend_bold`, `legend_font_size_mm`, `legend_always` (légende visible hors détail : nom/marque imprimés), `legend_spans: List[TextSpan]` (morceaux stylés ; `root_validator(pre=True)` remplit `legend` par concaténation), `font_family`, `underline`, `variants: Dict[variante, Dict[champ, valeur]]` (`hidden: true` masque).
- `TextSpan` : `text`, `weight` (100–900), `font_family?`, `color?`, `font_size_mm?`.
  - `root_validator validate_custom_icon` : `icon_path_d` et `icon_view_box` ensemble ; viewBox w/h > 0.
- Sous-types (champ `type` Literal) :
  - `EncoderComponent` (`diameter_mm`, `variant` inutilisé), `LEDComponent`, `ScrewComponent` → `diameter_mm`
  - `ButtonComponent` (`width_mm`, `height_mm`, `shape` inutilisé), `ScreenComponent`, `PadComponent`, `FrameComponent` → `width_mm`, `height_mm`
  - `LogoComponent` → `width_mm`, `height_mm` + validator : `icon_path_d`/`icon_view_box` obligatoires.
  - `TextComponent` → inscription imprimée **toujours visible** : `legend` requis (ou `legend_spans`), `text_anchor` (`start|middle|end`), `width_mm?` (→ `textLength`), `detail_only` (dessiné seulement avec `show_labels`).
- `DevicePort` : `id`, `label`, `direction` (`input|output|bidirectional`), `signal` (`audio|midi|usb|power`), `connector`, `channels`, `balanced`, `voltage_v`, `current_a`, `capabilities: List[str]`, `x` (déf. 0.5), `y` (déf. 1.0).
- `Component = Union[...]`, `DeviceLayout` : `manufacturer`, `model`, `physical`, `components=[]`, `ports=[]`.

### `models/theme.py`
- `ComponentStyle` : `fill` (requis), `stroke="none"`, `stroke_width=0`, `rx=0`, `indicator_color` (inutilisé).
- `LabelStyle` : `fill=None` (→ couleur auto), `font_family="sans-serif"`, `font_size_mm=2.5`, `min_font_weight?` (100–900, appliqué par `legends._weight` au texte et à chaque span).
- `PortStyle` (`theme.ports`) : `fill=None` (→ `label_color`), `marker_radius_mm=1.0`, `stroke_width_mm=0.3`, `font_size_mm=1.6`, `label_gap_mm=0.8`.
- `CableColors` : `audio`, `midi`, `usb`, `power` (chacune avec défaut → surcharge partielle possible).
- `CableStyle` : `width_mm=1.2`, `spacing_mm=2.2` (validator : ≥ `width_mm`), `clearance_mm=6`, `corner_radius_mm=1.5`, `opacity=0.95`, `colors`.
- `Theme` : `name`, `variant` (`screen` par défaut, `print` pour `tshirt_dark`), `background: Dict[str, Any]` (clés lues : `fill`, `stroke`, `stroke_width`, `rx`), `components: Dict[type, ComponentStyle]`, `labels`, `cables: CableStyle` (défaut si absent).

### `models/scene.py`
`AbsolutePosition(type="absolute", x, y)` (mm), `RelativePosition(type="relative", anchor right|left|top|bottom, target, spacing_mm=15)`, `SceneDevice(id, device: chemin, position)`, `PortEndpoint(device_id, port_id)`, `SceneConnection(source, target, label?)`, `Scene(name, devices=[], connections=[])`.

### `models/text.py`
`parse_markup(str) -> [Run(text, bold)]` (`**…**` = gras, espaces conservés). `TextLine(text, size_mm?, letter_spacing_em?, bold_weight?, regular_weight?, font_family?, color?)`, `TextBlock(lines (str ou TextLine), font_family, color?, size_mm=12, letter_spacing_em=0.08, bold_weight=700, regular_weight=200, line_gap_em=0.45, align, uppercase)`. `Scene.title: TextBlock?`, `Scene.title_gap_mm=20`.

## `renderer/text/` — Blocs de texte

| Symbole | Rôle |
|---|---|
| `layout_text_block(block) -> BlockLayout(x_offsets, baselines, bbox)` | Chaque ligne rendue seule par resvg (résolution `MEASURE_PX_PER_EM`=120 px/em, canevas agrandi tant que le texte touche le bord) → boîte encrée → décalage pour un alignement exact. Lignes espacées de `line_gap_em` × taille + capitales (`CAP_HEIGHT_EM`=0.72). Origine = point d'alignement, haut des capitales de la 1re ligne |
| `draw_text_block(container, block, origin, theme?, layout?)` | `<g class="text-block">`, un `<text>` par ligne (`xml:space=preserve`, `letter-spacing`), un `<tspan>` par run avec sa graisse. Couleur : `block.color` ou `label_color(theme)` |
| `render_text_svg(block, path, theme?, padding_mm=2)` | SVG autonome recadré sur la boîte encrée |

Scène : `render._place_title` centre le titre (selon `align`) sur l'emprise horizontale des machines, au-dessus de tout (machines + câbles) à `title_gap_mm` ; ses coins entrent dans `compute_bounds`.

## `renderer/device/` — Rendu d'un appareil

`__init__.py` réexporte `draw_device_to_group`, `render_svg`.

### `device/draw.py`
| Fonction | Rôle |
|---|---|
| `for_variant(component, variant)` | Composant avec les champs de `component.variants[theme.variant]` appliqués (`copy(update=…)`), ou `None` si `hidden` |
| `draw_device_to_group(container, layout, theme, show_labels)` | **Moteur partagé** appareil/scène. Légendes dessinées si `show_labels` **ou** `comp.legend_always` ; composants `text` toujours. Coordonnées locales en mm (0,0 = coin haut-gauche). `logo` toujours dessiné (couleur `fill` ou `label_color`). Type sans style thème → ignoré. `screen/button/pad/frame` → `Rect` centré ; `encoder/led/screw` → `Circle` |
| `render_svg(device, theme, path, show_labels)` | SVG d'un appareil : fond (`background`, rx défaut 0) + `draw_device_to_group` + `save()` |

### `device/legends.py`
| Fonction | Rôle |
|---|---|
| `label_color(theme)` | `labels.fill` sinon : fond `none` → `background.stroke` ; sinon luminance du fond → `#111111` ou `#ffffff` |
| `default_control_font_size(comp, theme)` | `legend_font_size_mm` sinon min(thème, taille qui tient en largeur ≈ `0.62·len` et 55 % de la hauteur) |
| `legend_text(comp, theme, insert, anchor, size, color, bold, **attrs)` | **Fabrique unique des `<text>` de légende** : texte simple, ou un `<tspan>` par `legend_spans` (+ `xml:space="preserve"`, sinon l'espace de tête d'un morceau disparaît). Police = `comp.font_family` ou thème |
| `add_printed_text(dwg, comp, theme, x, y)` | Composant `text` : `<text class="printed-text">`, toujours dessiné (appelé avant tout le reste dans `_draw_components`) |
| `add_control_legend(dwg, comp, theme, cx, cy)` | `frame` : texte `center` ou `bottom_left` (ligne de base alphabétique : milieu des majuscules, `CAP_MIDDLE_EM`=0.36 em, à `font_size` du bas du cadre). `button`/`pad` : priorité **icon_path_d > icon > legend** ; légende bold forcé pour `button` ; `underline` = `Line`. Autres types (encoder…) : **rien** |

### `device/ports.py`
| Symbole | Rôle |
|---|---|
| `UP/DOWN/LEFT/RIGHT`, `Direction` | Directions SVG (y vers le bas) — **source unique**, réutilisée par `scene/cabling/geometry.py` |
| `port_side(port)` | Bord le plus proche de (x, y) normalisés ; égalité : haut > bas > gauche > droite |
| `port_edge_point(port, w, h)` | Port projeté sur la tranche, coordonnées locales |
| `draw_ports(container, layout, theme)` | Mode détail : cercle `class="port"` sur la tranche + `<text class="port-label">` (`port.label`) écrit vers l'intérieur (tourné ±90° sur les bords haut/bas) |

### `renderer/print_check.py`
`analyse_print(svg, print_width_mm) -> PrintReport(print_width_mm, print_height_mm, scale, dpi, pixels, thinnest_line_mm, smallest_text_mm, thin_lines, small_texts)` : parcourt le SVG en cumulant les `scale()` des transforms, mesure `stroke-width` (si `stroke` ≠ none) et `font-size` (text/tspan non vides) à la taille imprimée. Seuils `MIN_LINE_MM=0.5`, `MIN_TEXT_MM=2.1`. `find_thin_areas(svg, print_width_mm, min_mm=0.5, preview_path?)` : rend le SVG **sans textes** à 300 dpi imprimés, ouverture morphologique par un disque de `min_mm` (numpy) → pixels plus fins ; regroupés en zones (cellules 2 mm), zones < `MIN_AREA_PIXELS`=40 ignorées ; aperçu gris/rouge. `find_narrow_gaps(svg, print_width_mm, min_mm=MIN_GAP_MM=0.5, keep_text=False, preview_path?)` : fermeture morphologique (dilatation puis érosion par le disque) → espaces vides qui se bouchent ; aperçu bleu. Briques communes : `_ink_mask`, `_erode`, `_dilate`, `_areas`, `_preview`. `export_print` rapporte : traits, textes, formes fines (alerte), espaces entre formes (alerte), espaces autour des textes (info). CLI : `--print-width <cm>` sur `render` / `render-scene` → `export_print` (PNG à `report.dpi` + rapport traits/textes + zones fines, aperçu `<svg>-controle.png`).

### `renderer/export.py`
`svg_to_png(svg_path, png_path, dpi=300)` : `resvg_py.svg_to_bytes(svg_path=…, dpi=…)` → PNG RGBA transparent ; taille px = mm / 25.4 × dpi.

### `device/icons.py`
| Symbole | Rôle |
|---|---|
| `ICONS: Dict[str, IconDrawer]` | **Registre** nom → `draw_xxx(dwg, center_x, center_y, width, height, color)` |
| `add_control_icon(dwg, icon, cx, cy, w, h, color)` | Cherche dans `ICONS` ; inconnu → `ValueError` |
| `draw_custom_icon(dwg, d (str ou liste : un `<path>` par élément), view_box, cx, cy, w, h, color, fill_rule, mode, stroke_width_view)` | Centre et met à l'échelle (contain) un path SVG. `mode=stroke` : trait = `stroke_width_view` (unités du view_box) ou 6 % de min(w,h) en mm. `Path(debug=False)` : le validateur svgwrite rejette la notation compacte des arcs |
| `draw_device_logo(dwg, logo, cx, cy, color)` | Wrapper → `draw_custom_icon` |
| `draw_perform/save_project/samples/metronome` | Paths importés d'un SVG source, recentrés par `_source_group(source_box, …)` (échelle 55 %) |
| `draw_play/stop` | Paths outline 16×16 / 14×14 via `_draw_transport_path` |
| `draw_record`, `draw_keyboard`, `_arrow(points)` | Formes géométriques (`scale = 0.38·min(w,h)`, trait `0.18·scale`) |

Ajouter une icône : écrire `draw_xxx`, l'enregistrer dans `ICONS`, la lister dans `JSON.md` / `README.md`. Le test `test_every_builtin_icon_draws_something` la couvre automatiquement.

## `renderer/scene/` — Rendu de scène

`__init__.py` réexporte `render_scene_svg`, `validate_scene_connections`.

### `scene/validation.py`
`validate_scene_connections(scene, layouts_by_instance)` : ids d'instance uniques, layout présent, ids de port uniques par appareil, **chaque port utilisé par au plus un câble**, appareils/ports référencés existants, source ∈ {output, bidirectional}, cible ∈ {input, bidirectional}, **même `signal`**. Lève `ValueError` (messages FR).

### `scene/layout.py`
| Symbole | Rôle |
|---|---|
| `Rect` | alias `(x, y, w, h)` en mm, coordonnées de scène |
| `resolve_positions(scene, layouts) -> Dict[id, Rect]` | Absolues puis relatives en cascade (≤ `MAX_RESOLUTION_PASSES`=10 passes) ; aucun progrès → `ValueError` « dépendance circulaire » |
| `check_no_overlap(rects)` | `ValueError` si deux appareils ont une intersection d'aire non nulle (se toucher est permis) |
| `SceneBounds(width_mm, height_mm, offset_x, offset_y)` | NamedTuple |
| `compute_bounds(rects, padding_mm, points=())` | bbox des appareils **et des points des câbles** + marge ; offset = translation scène → SVG |

### `scene/cabling/` — Câblage réaliste

Pipeline (`__init__.route_cables`) : ancrage des ports → contrôle des prises → grille → A* par câble → séparation (nudging) → contrôle anti-traversée. Tout en **coordonnées de scène** (le décalage SVG est appliqué par un `<g translate>` dans `render.py`).

| Fichier / symbole | Rôle |
|---|---|
| `__init__.CableRoute(connection, signal, points)` | Résultat : polyligne orthogonale port source → port cible |
| `__init__.route_cables(scene, layouts, rects, style)` | Pipeline complet. Erreurs : prises à la même position (`_check_distinct_plugs`), port trop près d'un autre appareil (sortie dans une zone interdite), aucun chemin, câble qui traverserait un appareil (`_check_no_device_crossing`, garde-fou) |
| `__init__.draw_cables(container, routes, style)` | Couleur = `style.colors.<signal du port source>` |
| `geometry.py` | `Point`, `Direction` (`UP/DOWN/LEFT/RIGHT`, y vers le bas), `Box` (`from_rect`, `inflate`, `contains_strict`, `overlaps`), `segment_crosses_box`, `simplify` (supprime doublons + points alignés), `EPS` |
| `anchors.port_side` | Réexport de `device.ports.port_side` |
| `anchors.port_anchor(port, box, clearance) -> PortAnchor(point, direction, exit)` | Port projeté sur la tranche ; `exit` = point à `clearance` du bord, départ du routage |
| `grid.RoutingGrid(obstacles, waypoints, frame_margin)` | Lignes = bords des boîtes gonflées de `clearance`, milieux entre lignes d'obstacles (couloirs centrés), points de sortie, cadre extérieur. `is_free(node)`, `step(node, dir)` (None si l'arête entre dans une zone interdite), `blocking_obstacle(point)` ; caches par instance |
| `router.find_route(grid, start, start_dir, goal, goal_dir)` | A* sur états (nœud, direction) ; coût = longueur + `BEND_PENALTY_MM` (12) par coude, pas de demi-tour ; arrivée pénalisée si pas dans l'axe du port |
| `nudging.nudge_routes(routes, boxes, spacing, width)` | Segments colinéaires qui se recouvrent → voies parallèles. Premier/dernier segment (sortie de port) **fixes**. Ordre des voies : `_Ordering.compare` (celui qui quitte le couloir le premier se place du côté où il tourne ; à coude identique, regarde le couloir suivant avec inversion d'ordre pour (lo,-1) et (hi,+1)). Place disponible mesurée jusqu'aux appareils (`_free_space`) ; `_lane_offsets` garde chaque voie à `clearance` des machines (groupe repoussé vers l'extérieur), sinon se contente de ne pas les toucher, et en dernier recours resserre l'espacement. Coudes recalculés par intersection (`_rebuild`) |
| `draw.rounded_path(points, radius)` | Path SVG avec coudes arrondis (`Q`) |
| `draw.draw_cable(container, points, color, signal, style)` | `<g class="cable cable-<signal>">` : tracé + pastille de prise à chaque bout |
| `labels.place_label(points, text, other_routes, device_boxes, style)` | Segments du plus long au plus court, positions du milieu vers les bouts (pas `SLIDE_STEP_MM`=2), côtés -1 puis +1 ; refuse toute boîte de texte qui touche un autre câble ou une machine ; à défaut milieu du plus long segment. Largeur texte estimée `len × taille × 0.6` |
| `labels.draw_cable_label(...)`, `__init__.draw_cable_labels(container, routes, theme, rects)` | Mode détail : `<text class="cable-label">` couleur du câble, `cables.label_font_size_mm` |

### `scene/render.py`
| Symbole | Rôle |
|---|---|
| `SCENE_PADDING_MM = 20` | Marge autour de la scène |
| `load_scene(path)`, `load_scene_layouts(scene, base_dir)` | Chargement JSON ; chemins `device` relatifs à `base_dir` = **dossier du fichier de scène** ; absent → `ValueError` « Layout introuvable » |
| `render_scene_svg(scene_path, output_path, theme, padding_mm=20, show_labels=False)` | load → scène vide = `ValueError` → validate → resolve_positions → check_no_overlap → route_cables → compute_bounds → **aucun fond** (transparent) → `<g translate(offset)>` contenant les appareils (`<g class="device" id="device-<id>">`, ports si détail) puis les câbles puis leurs noms (détail) → `save()` |

`cli.py render-scene` attrape les `ValueError` (dont `ValidationError` pydantic) → message `❌ Scène invalide : …` et code de sortie 1.

## `tests/` — pytest (`./venv/Scripts/python.exe -m pytest`)

Indépendants du design des vrais appareils : pas de comparaison de SVG figés.

| Fichier | Couvre |
|---|---|
| `conftest.py` | `make_device()`, `port()`, `all_components()` (un composant par type + un bouton par icône de `ICONS`), fixtures `full_device`, `theme` (paramétrée sur tous les thèmes), `write_json` |
| `test_models.py` | Défauts, validations, enums fermés ; tous les `devices/` et `themes/` du projet se chargent |
| `test_scene_validation.py` | Connexions valides / invalides, doublons |
| `test_scene_layout.py` | Ancres relatives, cascade, cycles, bbox |
| `test_render.py` | Chaque icône dessine, icône inconnue, rendu complet × thèmes, légendes seulement en `--detail`, vrais appareils rendent sans erreur, scène (taille, 1 câble par connexion, couleurs du thème), scène lancée depuis un autre dossier, fond transparent, layout introuvable, ports en détail, noms de câbles, PNG (taille par dpi, RGBA) |
| `test_cabling.py` | `assert_cabling_is_realistic` (orthogonal, ne traverse aucun appareil, sort perpendiculairement au port, aucun couple de segments parallèles à moins de `spacing_mm`) sur : câbles parallèles, mur à contourner, ports sur les 4 côtés, scène `nays_2026`. Erreurs : chevauchement, port utilisé 2×, prises à la même position, port bloqué. Thème `cables` |
| `test_cli.py` | `slugify`, `select_theme`, `default_output_path` (suffixe `-detail`) |

## Données

- **Appareils** : voir `JSON.md`. Ids de ports utilisés dans la scène : digitakt `midi-out`, `audio-out-l/r` ; octatrack `midi-in`, `midi-thru`, `audio-in-a..d` ; jx08 `midi-in/out`, `audio-out` ; tb3 `midi-in`, `audio-out`.
- **Thèmes** : clés `components` = `frame, screen, encoder, button, pad, led, screw`. `outlined_*` n'ont pas de `labels.fill` → couleur dérivée du `background.stroke`. ⚠ `flat.json` a pour nom "Elektron Dark Pro".
- **Scènes** : `position: {type, …}` (voir `JSON.md`).
