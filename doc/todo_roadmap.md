# État & roadmap — riglayout

> Màj : 2026-10-23. Cocher / déplacer les items au fil des sessions.

## État actuel

**Fait** :
- impression t-shirt : thème `tshirt_dark` (traits ≥ 0,7 mm imprimés à 28 cm, LED rouges pleines, sans vis, câbles opaques, `min_font_weight` 500) et mode `--print-width` (PNG à la taille d'impression + contrôle traits/textes) ;
- variantes de mise en page `scenes/nays_2026_{bloc,carre,portrait,bandeau,colonne}.json`, choisies en explorant toutes les permutations par famille (score = 300 × croisements + longueur de câble) ; les tests de câblage tournent sur toutes les scènes du dossier ;
- logos Roland : emblème (tracé fourni par l'utilisateur, plein) + mot officiel (Wikimedia, liste de paths) ; textes trop petits en `detail_only` (« POLYPHONIC SYNTHESIZER », « TOUCH BASSLINE ») ;
- scène `nays_2026` : rangée du haut alignée (TB-3 `relative` à droite du JX-08, 30 mm au-dessus de la rangée du bas) ;
- modèle appareil + thèmes, rendu SVG d'un appareil, Digitakt II détaillé, Octatrack (`octatrack2.json`), légendes/icônes (designs en **v0**, à peaufiner en fin de projet) ;
- `renderer/` découpé en `models/`, `device/`, `scene/` (une responsabilité par fichier), icônes en registre `ICONS` ;
- **scène** : positions `absolute` / `relative` en cascade, erreur si chevauchement, taille auto (appareils + câbles), `--detail` ;
- **câblage réaliste** (`scene/cabling/`, réécrit de zéro) : sortie perpendiculaire à la tranche, contournement des machines à `clearance_mm`, A* longueur + coudes, câbles parallèles côte à côte, ordre des voies anti-croisement, coudes arrondis, pastilles de prise, couleurs par signal dans le thème (`cables`) ;
- validations réalistes : un câble par port, pas deux prises au même endroit, port trop près d'une autre machine ; erreur « port inconnu » qui liste les ports disponibles ;
- **sorties pour impression textile** : aucun fond de scène (transparent), export PNG RGBA `--png` / `--dpi` (300 par défaut, resvg-py) ;
- **mode détail** : ports dessinés (cercle sur la tranche + nom) en appareil seul comme en scène ; nom des câbles (`label`) placé là où il ne recouvre rien ;
- chemins `device` relatifs au fichier de scène ; noms de sortie `<nom>-<thème>[-detail]` (plus d'écrasement) ;
- inscriptions imprimées : composant `text` (toujours visible), `legend_always` (nom sous l'écran Digitakt/Octatrack), logos Roland (emblème en path stroke + texte) et noms de modèle sur TB-3 et JX-08 ;
- câbles d'un même couloir repoussés pour rester à `clearance_mm` des machines ;
- venv sur Python 3.13 officiel (l'ancien Python MSYS2 n'avait pas de wheels binaires) ;
- maquettes Roland JX-08 et TB-3 (**en standby**, TB-3 en cours de refonte par l'utilisateur : ports renommés `out-l`/`out-r`, la scène utilise `out-l`) ; scène `nays_2026.json` (4 appareils, 3 câbles MIDI + 4 audio) ;
- hygiène : `.gitignore`, `requirements*.txt`, pytest (≈140 tests indépendants du design).

## Bugs / limites connus

0. Octatrack : LED « Voyant Card » (x=0.649, y=0.1) isolée en haut du panneau — conservée car déclarée exprès ; à retirer si elle n'existe pas sur la vraie machine.

1. Noms de ports : ils peuvent recouvrir des composants proches de la tranche (ex. « Headphones » sur une vis du Digitakt) — à régler avec le design des appareils.
2. Les anciennes sorties `output/scene-nays-2026.svg` et `output/*-<thème>.svg` en mode détail datent de l'ancien nommage.
3. Légendes sur `encoder`/`screen` ignorées au rendu (JX-08/TB-3 en déclarent).
4. Emoji ✅/❌ dans `typer.echo` → `UnicodeEncodeError` sur console non UTF-8.
5. `output/elektron-octatrack-elektron-dark-pro copy.svg` : doublon ; SVG de `output/` pas tous régénérés.
6. Taille de légende spécifique Octatrack supprimée au refactor (`git show cb5530a:renderer/svg.py` l.336-363) : vérifier `legend_font_size_mm` dans `octatrack2.json`.
7. Câblage : quelques croisements restent quand la position des ports les rend inévitables ; un segment de sortie de port (fixe) peut côtoyer une voie décalée d'un autre câble ; si un couloir est trop étroit pour tous ses câbles, l'espacement est compressé (sous `spacing_mm`).
8. Positions des ports de l'Octatrack (main/cue/inputs) corrigées le 2026-10-23 car empilées 2 par 2 : espacement 0.03 (≈10 mm), à valider contre la vraie face arrière.

## Prochaines étapes logiques

### Scènes / câblage
- [ ] Ports en façade (ex. EXT CLK IN du JX-08, sur le panneau) : aujourd'hui ramenés au bord le plus proche.
- [ ] Titre de scène (`name`) et légende des couleurs, en option, pour les visuels imprimés.
- [ ] Tailles de texte « impression » : noms de ports ≥ 2,2 mm, noms de câbles ≥ 2,5 mm.
- [x] Scène transparente + export PNG.
- [x] Ports (prise + nom) et `connection.label` en mode détail.
- [x] Chemins `device` relatifs au fichier de scène.
- [x] Noms de sortie distincts par thème et mode détail.
- [ ] Option par connexion : couleur forcée, câble prioritaire, passage par un point.
- [ ] Croisements : analysés le 2026-10-23 sur `nays_2026` — les 9 croisements sont imposés par la position des prises (prises alignées sur une tranche dont les intervalles s'entrelacent). Une pénalité de croisement dans l'A* (2 passes) et une recherche exhaustive de l'ordre des voies ont été essayées : 0 gain, +58 mm de câble → retirées. À reconsidérer seulement avec un cas où un détour évite un croisement.
- [ ] Contrôle d'échelle / taille de sortie (page A4, px…).

### Appareils & rendu (en fin de projet)
- [ ] ~~Couleur de boîtier propre à chaque machine~~ — écarté le 2026-10-23 : l'utilisateur préfère la couleur uniforme du thème.
- [ ] JX-08 : titres de sections sérigraphiés (LFO, DCO-1, MIXER, VCF…) avec des composants `text`.
- [ ] TB-3 : LED de pas en rectangles verts, afficheur 7 segments rouge.
- [ ] Peaufiner Digitakt II / Octatrack ; JX-08 et TB-3 (layouts réels, logos) — **standby**.
- [ ] Rendre les légendes d'encodeurs ; exploiter `variant`, `shape`, `indicator_color` ou les supprimer.
- [ ] Vue arrière / panneau de connectique.

### Qualité
- [ ] Snapshots SVG des vrais appareils **seulement quand leur design sera finalisé**.
- [ ] Commande `validate` (valider un JSON sans rendre).
- [ ] Migration éventuelle pydantic v2 (impacte `root_validator` et l'instanciation).
