# Codebase map — riglayout

> Référence fonction par fonction. Lire avant de modifier un module. Màj : 2026-10-23.

## `cli.py` — CLI Typer

| Symbole | Rôle |
|---|---|
| `app = typer.Typer()` | 2 commandes → il faut **toujours** nommer la commande (`render …`), `python cli.py device.json` ne marche plus |
| `THEMES_DIR` | `<racine>/themes` (absolu, basé sur `__file__`) |
| `available_themes()` | `[(Path, name)]` triés, `name` lu dans le JSON (fallback `stem`) |
| `select_theme(opt)` | `opt` = chemin existant → ce chemin ; sinon match insensible à la casse sur `stem`, `name` de fichier ou `name` du thème ; `None` → prompt interactif numéroté. Erreurs → `typer.BadParameter` |
| `slugify(s)` | ASCII, minuscules, `-` — sert aux noms de sortie auto |
| `render(device_path, --theme/-t, --output/-o, --labels/--no-labels, --detail)` | Sortie défaut : `output/<slug(manufacturer-model)>-<slug(theme.name)>.svg` |
| `render_scene(scene_path, --theme/-t, --output/-o, --labels, --detail)` | Sortie défaut : `output/scene-<slug(stem)>.svg`. `show_labels = labels or detail` |

## `renderer/models.py` — Modèle appareil (pydantic v1)

- `PhysicalDimensions` : `width_mm`, `height_mm` (>0, requis), `depth_mm` (opt).
- `BaseComponent` (commun) : `x`, `y` ∈ [0,1] ; `label`, `legend`, `icon`, `icon_path_d`, `icon_view_box (x,y,w,h)`, `icon_fill_rule` (`nonzero|evenodd`), `icon_mode` (`fill|stroke`), `fill`, `stroke`, `legend_color`, `legend_position` (`center|bottom_left`), `legend_bold`, `legend_font_size_mm`, `underline`.
  - `root_validator validate_custom_icon` : `icon_path_d` et `icon_view_box` ensemble ; viewBox w/h > 0.
- Sous-types (champ `type` Literal) :
  - `EncoderComponent` (`diameter_mm`, `variant` inutilisé), `LEDComponent`, `ScrewComponent` → `diameter_mm`
  - `ButtonComponent` (`width_mm`, `height_mm`, `shape` inutilisé), `ScreenComponent`, `PadComponent`, `FrameComponent` → `width_mm`, `height_mm`
  - `LogoComponent` → `width_mm`, `height_mm` + validator : `icon_path_d`/`icon_view_box` obligatoires.
- `DevicePort` : `id`, `label`, `direction` (`input|output|bidirectional`), `signal` (`audio|midi|usb|power`), `connector`, `channels`, `balanced`, `voltage_v`, `current_a`, `capabilities: List[str]`, `x` (déf. 0.5), `y` (déf. 1.0). ⚠ `connector` déclaré deux fois (inoffensif).
- `Component = Union[...]`, `DeviceLayout` : `manufacturer`, `model`, `physical`, `components=[]`, `ports=[]`.

## `renderer/themes.py` — Modèle thème

- `ComponentStyle` : `fill` (requis), `stroke="none"`, `stroke_width=0`, `rx=0`, `indicator_color` (inutilisé).
- `LabelStyle` : `fill=None` (→ couleur auto), `font_family="sans-serif"`, `font_size_mm=2.5`.
- `Theme` : `name`, `background: Dict[str, Any]` (clés lues : `fill`, `stroke`, `stroke_width`, `rx`), `components: Dict[type, ComponentStyle]`, `labels`.

## `renderer/svg.py` — Moteur appareil

| Fonction | Rôle |
|---|---|
| `label_color(theme)` | `labels.fill` sinon : fond `none` → `background.stroke` ; sinon luminance du fond → `#111111` ou `#ffffff` |
| `default_control_font_size(comp, theme)` | `legend_font_size_mm` sinon min(thème, taille qui tient en largeur ≈ `0.62·len` et 55 % de la hauteur) |
| `add_control_legend(dwg, comp, theme, cx, cy)` | `frame` : texte `center` ou `bottom_left`. `button`/`pad` : priorité **icon_path_d > icon > legend** ; légende bold forcé pour `button` ; `underline` = `Line`. Autres types (encoder…) : **rien** |
| `draw_device_to_group(container, layout, theme, show_labels)` | **Moteur partagé** appareil/scène. Coordonnées locales en mm (0,0 = coin haut-gauche appareil). `logo` toujours dessiné (couleur `fill` ou `label_color`). Type sans style thème → ignoré. `screen/button/pad/frame` → `Rect` centré ; `encoder/led/screw` → `Circle` |
| `render_svg(device, theme, path, show_labels)` | SVG d'un appareil : fond (`background`, rx défaut 0) + `draw_device_to_group` + `save()` |

## `renderer/icons.py` — Pictogrammes

| Fonction | Rôle |
|---|---|
| `draw_device_logo(dwg, logo, cx, cy, color)` | Wrapper → `draw_custom_icon` |
| `draw_custom_icon(dwg, d, view_box, cx, cy, w, h, color, fill_rule, mode)` | Centre et met à l'échelle (contain) un path SVG ; `mode=stroke` → trait = 6 % de min(w,h) |
| `add_control_icon(dwg, icon, cx, cy, w, h, color)` | Icônes intégrées : `perform`, `save_project`, `samples`, `metronome` (paths importés d'un SVG source, coordonnées d'origine dans `source_icons`), `play` / `stop` (paths outline 16×16 / 14×14), `record` (cercle), `keyboard` (rect plein + touches noires `#202020`), `arrow_up/down/left/right` (polyline). **Nom inconnu → `ValueError`** |

Ajouter une icône intégrée : nouvelle branche dans `add_control_icon` avant le bloc `points_by_icon`, puis la lister dans `JSON.md` et `README.md`.

## `renderer/scenes.py` — Scènes

- Modèles : `AbsolutePosition(type="absolute", x, y)` (mm), `RelativePosition(type="relative", anchor right|left|top|bottom, target, spacing_mm=15)`, `SceneDevice(id, device: chemin, position)`, `PortEndpoint(device_id, port_id)`, `SceneConnection(source, target, label?)`, `Scene(name, devices, connections)`.
- `validate_scene_connections(scene, layouts_by_instance)` : ids d'instance uniques, layout présent, ids de port uniques par appareil, appareils/ports référencés existants, source ∈ {output, bidirectional}, cible ∈ {input, bidirectional}, **même `signal`**. Lève `ValueError` (messages FR).
- `render_scene_svg(scene_path, output_path, theme, padding_mm=80, show_labels=False)` :
  1. charge scène + layouts (chemins relatifs au **CWD**) ; scène vide → `ValueError`
  2. valide les connexions
  3. résout les positions (boucle ≤10 passes ; pas de progrès → `ValueError` dépendance circulaire)
  4. bbox + padding → taille SVG ; offset pour recaler les coords négatives
  5. fond de scène **codé en dur `#111111`** ; chaque appareil = `<g translate>` + rect fond (`background`, rx défaut 6) + `draw_device_to_group`
  6. `port_coordinates[(instance, port)]` = position absolue
  7. câbles : `M port1 → monte → y = top_source − 12 − i·3.5 → horizontal → descend → port2` ; couleur `#e67e22` si `"midi"` dans **l'id du port source**, sinon `#3498db` ; `connection.label` non rendu ; ports non dessinés
  8. `print(...)` de la taille finale

## Données

- **Appareils** : voir `JSON.md` (schéma composants/ports à jour). Ids de ports utilisés dans la scène : digitakt `midi-out`, `audio-out-l/r` ; octatrack `midi-in`, `midi-thru`, `audio-in-a..d` ; jx08 `midi-in/out`, `audio-out` ; tb3 `midi-in`, `audio-out`.
- **Thèmes** : clés `components` = `frame, screen, encoder, button, pad, led, screw`. `outlined_*` n'ont pas de `labels.fill` → couleur dérivée du `background.stroke`. ⚠ `flat.json` a pour nom "Elektron Dark Pro" (d'où les SVG `…-elektron-dark-pro.svg`).
- **Scènes** : format **positions objets** (`position: {type, …}`) — l'ancien format `x`/`y` normalisés de README/JSON.md n'est plus valide.
