# Guidelines — riglayout

> Règles déduites du code existant. À respecter pour toute modification. Màj : 2026-10-23.

## Langue

- **Français** pour : messages d'erreur (`ValueError`, `typer.BadParameter`), aides CLI (`help=`), docstrings, commentaires, docs (`README.md`, `JSON.md`, `doc/`). Accents corrects (UTF-8).
- **Anglais** pour : identifiants Python, clés JSON, ids de ports/composants, valeurs d'enum (`input`, `audio`, `bottom_left`…).

## Style Python

- Python 3.13, indentation 4 espaces, `snake_case` fonctions/variables, `PascalCase` classes, `UPPER_CASE` constantes module (`THEMES_DIR`).
- Annotations de type sur les signatures (`typing.Optional/List/Tuple/Literal/Union/Mapping`, pas la syntaxe `X | None`).
- Imports explicites des formes svgwrite (`from svgwrite.shapes import Rect, Circle`) plutôt que `dwg.rect(...)` (convention du code actuel).
- Fonctions de dessin : signature `(dwg_ou_groupe, objet, …, center_x, center_y, …, color)` ; elles **ajoutent** au conteneur passé, ne retournent rien.
- Pas de formatter/linter configuré ; garder des lignes lisibles, découper les longs appels sur plusieurs lignes.
- Pas de logs : `typer.echo` dans la CLI, `print` toléré dans `scenes.py`.

## Modèles & validation (pydantic **v1**)

- Toute nouvelle donnée JSON passe par un modèle pydantic dans `renderer/models.py`, `themes.py` ou `scenes.py`.
- Contraintes via `Field(..., gt=0)`, `ge/le` pour les coordonnées normalisées, `min_length=1` pour les ids.
- Énumérations fermées → `Literal[...]` ; listes ouvertes → `List[str]` (ex. `capabilities`).
- Règles inter-champs → `@root_validator(skip_on_failure=True)` qui `raise ValueError("message FR")` et `return values`.
- Nouveaux champs **optionnels avec défaut** pour garder les anciens JSON valides (principe de rétrocompatibilité appliqué partout : `components`/`ports` par défaut `[]`, `labels` par défaut).
- Nouveau type de composant : classe `XxxComponent(BaseComponent)` avec `type: Literal["xxx"]`, l'ajouter à l'`Union Component`, gérer son dessin dans `renderer/device/draw.py` (`draw_device_to_group`), l'ajouter à `all_components()` dans `tests/conftest.py`, ajouter son style dans **les 4 thèmes**, documenter dans `JSON.md`.

## Organisation des modules

- Un fichier = une responsabilité (voir le tableau « Où travailler » dans `codebase_map.md`). Une feature nouvelle et distincte (ex. dessin des ports) → nouveau module dans le paquet concerné plutôt que grossir `render.py`.
- Dépendances à sens unique `models` ← `device` ← `scene` ← `cli`. Les modèles ne connaissent pas svgwrite.
- Imports absolus depuis le module précis (`from renderer.scene.layout import resolve_positions`) à l'intérieur de `renderer/` ; les `__init__.py` ne réexportent que l'API publique utilisée par `cli.py`.
- Valeurs magiques de rendu (dimensions, couleurs par défaut) → constantes `UPPER_CASE` en tête de module.
- Icônes : une fonction `draw_xxx(dwg, center_x, center_y, width, height, color)` enregistrée dans `ICONS`, jamais de chaîne de `if`.

## Tests

- Lancer : `./venv/Scripts/python.exe -m pytest` (installer avec `pip install -r requirements-dev.txt`).
- **Ne pas figer le design** : pas de comparaison avec les SVG réels du Digitakt / Octatrack / Roland (designs en v0, retouchés à la fin). Tester la logique (modèles, validation, positions, câbles) et la bonne formation du SVG sur des données de test construites dans `tests/conftest.py`.
- Chaque nouvelle logique (règle de validation, ancre, routage…) arrive avec son test.
- Refactor sans changement de rendu attendu : capturer les SVG avant (tous appareils × thèmes × `--detail`, + scène) dans le scratchpad et comparer après (`diff -rq`), sans les commiter.

## Gestion des erreurs

- Données invalides → laisser remonter `pydantic.ValidationError` / `ValueError` avec message FR explicite (pas de `try/except` silencieux).
- Erreurs d'argument CLI → `typer.BadParameter`.
- Fallbacks visuels tolérés uniquement pour le style (`theme.background.get("rx", 6)`, `label_color` → `#ffffff` sur couleur illisible).

## Unités & géométrie

- Tout en **mm**. Positions de composants/ports normalisées `[0,1]`, **centre** du composant. Convertir via `comp.x * layout.physical.width_mm`.
- `draw_device_to_group` travaille en coordonnées **locales** à l'appareil ; le placement en scène se fait par `transform="translate(...)"` sur un groupe. Ne pas dupliquer la logique de dessin entre `render_svg` et la scène.

## Données JSON

- Fichiers UTF-8, indentation 2 espaces (appareils, thèmes) ; scènes en 4 espaces (existant).
- Un appareil par fichier sous `devices/<marque>/<modele>.json` (minuscules, `-` ou chiffres).
- `label` = description (jamais rendue), `legend` = texte réellement imprimé. Exceptions de couleur matérielle (ex. FUNC orange) via `fill`/`stroke`/`legend_color` au niveau composant, pas dans le thème.
- Ids de ports en kebab-case (`audio-out-l`, `midi-thru`), uniques par appareil.
- Logos/pictos spécifiques à un appareil → `icon_path_d` + `icon_view_box` dans le JSON, pas de code.

## Workflow

- Dépendances : ajouter toute nouvelle lib à `requirements.txt` (ou `requirements-dev.txt` si outil de dev) avec version épinglée. Ne jamais versionner `venv/` ni `__pycache__/`.
- Avant de commiter : `pytest` vert.
- Vérifier un changement en régénérant : `PYTHONIOENCODING=utf-8 ./venv/Scripts/python.exe cli.py render devices/elektron/digitakt2.json -t flat --detail` et `… render-scene scenes/nays_2026.json -t flat`.
- **Mettre à jour `doc/`** (et `JSON.md` si le schéma change) à chaque évolution d'architecture, ajout de fonction majeure ou changement de règle. Mettre à jour la date « Màj » en tête de fichier.
