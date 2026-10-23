# État & roadmap — riglayout

> Màj : 2026-10-23. Cocher / déplacer les items au fil des sessions.

## État actuel

**Fait** :
- modèle appareil + thèmes, rendu SVG d'un appareil, Digitakt II détaillé, Octatrack (`octatrack2.json`), légendes/icônes ;
- pictogrammes isolés dans `renderer/icons.py` ; `draw_device_to_group` partagé entre appareil et scène ;
- scène : positions `absolute` / `relative` en cascade, taille auto (bbox + padding), câbles orthogonaux « goulotte » ;
- maquettes simplifiées Roland JX-08 et TB-3 ; scène `nays_2026.json` (4 appareils, 3 câbles MIDI + 4 audio) ;
- hygiène : `.gitignore`, `requirements.txt`, `venv/` et `*.pyc` retirés du suivi git, README / JSON.md à jour, icônes `keyboard` / `arrow_*` / `play` / `stop` restaurées (rendu Digitakt II géométriquement identique à `cb5530a`).

## Bugs / limites connus

1. Couleur des câbles déduite de `"midi" in port_id` au lieu de `port.signal`.
2. Fond de scène codé en dur `#111111` (ignore le thème ; incohérent avec `outlined_light`).
3. Chemins `device` d'une scène résolus depuis le CWD, pas depuis le fichier scène.
4. `DevicePort.connector` déclaré deux fois dans `models.py`.
5. Légendes sur `encoder`/`screen` ignorées au rendu (JX-08/TB-3 en déclarent).
6. Emoji ✅ dans `typer.echo` → `UnicodeEncodeError` sur console non UTF-8.
7. `output/elektron-octatrack-elektron-dark-pro copy.svg` : doublon ; SVG de `output/` pas tous régénérés.
8. Le refactor a supprimé la taille de légende spécifique à l'Octatrack (`default_control_font_size(…, device_model)`, voir `git show cb5530a:renderer/svg.py` l.336-363). À vérifier que `octatrack2.json` fixe `legend_font_size_mm` partout où nécessaire.

## Prochaines étapes logiques

### Court terme (hygiène)
- [x] Restaurer les icônes perdues.
- [x] `.gitignore` + `requirements.txt`, `venv/` et `*.pyc` retirés du suivi.
- [x] README / JSON.md à jour.
- [x] Commit du travail en cours.

### Scènes
- [ ] Couleur de câble par `signal` (audio / midi / usb / power), idéalement définie dans le thème.
- [ ] Fond de scène pris dans le thème (nouvelle clé optionnelle, ex. `scene_background`).
- [ ] Dessiner les ports (pastille + label) et `connection.label`.
- [ ] Résoudre les chemins `device` relativement au fichier scène.
- [ ] Routage : éviter les chevauchements entre appareils, bundle par paire d'appareils, gérer les ports sur les autres bords (y≠0).
- [ ] Contrôle d'échelle / taille de sortie (page A4, px…).

### Appareils & rendu
- [ ] Compléter JX-08 et TB-3 (layouts réels, logos).
- [ ] Rendre les légendes d'encodeurs (sous le bouton) ; exploiter `variant`, `shape`, `indicator_color` ou les supprimer.
- [ ] Vue arrière / panneau de connectique.

### Qualité
- [ ] Tests pytest : validation modèles, `validate_scene_connections`, résolution de positions, snapshot SVG.
- [ ] Commande `validate` (valider un JSON sans rendre).
- [ ] Migration éventuelle pydantic v2 (impacte `root_validator` et l'instanciation).
