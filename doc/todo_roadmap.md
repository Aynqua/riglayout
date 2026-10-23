# État & roadmap — riglayout

> Màj : 2026-10-23. Cocher / déplacer les items au fil des sessions.

## État actuel

**Fait** :
- modèle appareil + thèmes, rendu SVG d'un appareil, Digitakt II détaillé, Octatrack (`octatrack2.json`), légendes/icônes (designs en **v0**, à peaufiner en fin de projet) ;
- `renderer/` découpé en `models/`, `device/`, `scene/` (une responsabilité par fichier), icônes en registre `ICONS` ;
- **scène** : positions `absolute` / `relative` en cascade, erreur si chevauchement, taille auto (appareils + câbles), `--detail` ;
- **câblage réaliste** (`scene/cabling/`, réécrit de zéro) : sortie perpendiculaire à la tranche, contournement des machines à `clearance_mm`, A* longueur + coudes, câbles parallèles côte à côte, ordre des voies anti-croisement, coudes arrondis, pastilles de prise, couleurs par signal dans le thème (`cables`) ;
- validations réalistes : un câble par port, pas deux prises au même endroit, port trop près d'une autre machine ;
- maquettes simplifiées Roland JX-08 et TB-3 (**en standby**) ; scène `nays_2026.json` (4 appareils, 3 câbles MIDI + 4 audio) ;
- hygiène : `.gitignore`, `requirements*.txt`, pytest (≈120 tests indépendants du design).

## Bugs / limites connus

1. Fond de scène codé en dur `SCENE_BACKGROUND = #111111` (ignore le thème ; illisible avec `outlined_light`).
2. Chemins `device` d'une scène résolus depuis le CWD, pas depuis le fichier scène.
3. Légendes sur `encoder`/`screen` ignorées au rendu (JX-08/TB-3 en déclarent).
4. Emoji ✅/❌ dans `typer.echo` → `UnicodeEncodeError` sur console non UTF-8.
5. `output/elektron-octatrack-elektron-dark-pro copy.svg` : doublon ; SVG de `output/` pas tous régénérés.
6. Taille de légende spécifique Octatrack supprimée au refactor (`git show cb5530a:renderer/svg.py` l.336-363) : vérifier `legend_font_size_mm` dans `octatrack2.json`.
7. Câblage : quelques croisements restent quand la position des ports les rend inévitables ; un segment de sortie de port (fixe) peut côtoyer une voie décalée d'un autre câble ; si un couloir est trop étroit pour tous ses câbles, l'espacement est compressé (sous `spacing_mm`).
8. Positions des ports de l'Octatrack (main/cue/inputs) corrigées le 2026-10-23 car empilées 2 par 2 : espacement 0.03 (≈10 mm), à valider contre la vraie face arrière.

## Prochaines étapes logiques

### Scènes / câblage
- [ ] Fond de scène pris dans le thème (bug 1).
- [ ] Dessiner les ports non connectés (pastille + nom) et `connection.label`.
- [ ] Résoudre les chemins `device` relativement au fichier scène (bug 2).
- [ ] Option par connexion : couleur forcée, câble prioritaire, passage par un point.
- [ ] Minimiser les croisements entre câbles (pénalité dans l'A* / ordre de routage).
- [ ] Contrôle d'échelle / taille de sortie (page A4, px…).

### Appareils & rendu (en fin de projet)
- [ ] Peaufiner Digitakt II / Octatrack ; JX-08 et TB-3 (layouts réels, logos) — **standby**.
- [ ] Rendre les légendes d'encodeurs ; exploiter `variant`, `shape`, `indicator_color` ou les supprimer.
- [ ] Vue arrière / panneau de connectique.

### Qualité
- [ ] Snapshots SVG des vrais appareils **seulement quand leur design sera finalisé**.
- [ ] Commande `validate` (valider un JSON sans rendre).
- [ ] Migration éventuelle pydantic v2 (impacte `root_validator` et l'instanciation).
