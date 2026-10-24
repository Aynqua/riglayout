import json
import re
import unicodedata
import typer
from pathlib import Path
from typing import Optional
from renderer.models import DeviceLayout, Theme
from renderer.device import render_svg
from renderer.scene import render_scene_svg
from renderer.models.text import TextBlock
from renderer.text import render_text_svg
from renderer.export import DEFAULT_DPI, svg_to_png
from renderer.print_check import MIN_GAP_MM, MIN_LINE_MM, MIN_TEXT_MM, analyse_print, find_narrow_gaps, find_thin_areas

app = typer.Typer()
ROOT_DIR = Path(__file__).resolve().parent
THEMES_DIR = ROOT_DIR / "themes"
DEVICES_DIR = ROOT_DIR / "devices"
SCENES_DIR = ROOT_DIR / "scenes"
TEXTS_DIR = ROOT_DIR / "texts"
OUTPUT_DIR = Path("output")  # relatif au dossier courant

PNG_OPTION = typer.Option(False, "--png", help="Exporter aussi un PNG transparent à côté du SVG")
DPI_OPTION = typer.Option(DEFAULT_DPI, "--dpi", help="Résolution du PNG (points par pouce)")
PRINT_OPTION = typer.Option(
    None, "--print-width", help="Mode impression : largeur imprimée en cm. Produit le PNG à cette taille (300 dpi) "
                                "et vérifie que traits et textes restent assez épais"
)


def export_print(svg_path: Path, print_width_cm: float):
    """PNG à la taille d'impression exacte + contrôle des traits et textes trop fins."""
    report = analyse_print(svg_path, print_width_cm * 10)
    png_path = svg_to_png(svg_path, svg_path.with_suffix(".png"), dpi=report.dpi)
    typer.echo(
        f"🖨️  Impression : {report.print_width_mm / 10:.1f} × {report.print_height_mm / 10:.1f} cm "
        f"(échelle {report.scale:.0%}), PNG {report.pixels[0]} × {report.pixels[1]} px à {DEFAULT_DPI} dpi : {png_path}"
    )
    for label, value, minimum, count, unit in (
        ("Trait le plus fin", report.thinnest_line_mm, MIN_LINE_MM, report.thin_lines, "traits"),
        ("Plus petit texte", report.smallest_text_mm, MIN_TEXT_MM, report.small_texts, "textes"),
    ):
        if not value:
            continue
        if count:
            typer.secho(f"   ⚠️  {label} : {value:.2f} mm (minimum conseillé {minimum} mm) — {count} {unit} en dessous",
                        fg=typer.colors.YELLOW)
        else:
            typer.echo(f"   ✅ {label} : {value:.2f} mm (minimum conseillé {minimum} mm)")

    def report_areas(report, ok_message, warning_message, color_name, warn=True):
        if not report.areas:
            typer.echo(f"   ✅ {ok_message}")
            return
        style = typer.colors.YELLOW if warn else None
        typer.secho(f"   {'⚠️ ' if warn else 'ℹ️ '} {warning_message.format(n=len(report.areas))} "
                    f"(en {color_name} dans {report.preview_path}) :", fg=style)
        for area in report.areas[:5]:
            typer.secho(f"      - à {area.x_cm:.1f} cm du bord gauche, {area.y_cm:.1f} cm du haut "
                        f"({area.width_mm:.0f} × {area.height_mm:.0f} mm)", fg=style)

    width_mm = print_width_cm * 10
    for suffix in ("-controle", "-espaces", "-espaces-textes"):
        svg_path.with_name(svg_path.stem + suffix + ".png").unlink(missing_ok=True)
    report_areas(find_thin_areas(svg_path, width_mm, preview_path=svg_path.with_name(svg_path.stem + "-controle.png")),
                 f"Formes pleines (logos, pictos) : rien sous {MIN_LINE_MM} mm",
                 f"Formes pleines : {{n}} zone(s) plus fine(s) que {MIN_LINE_MM} mm", "rouge")
    report_areas(find_narrow_gaps(svg_path, width_mm, preview_path=svg_path.with_name(svg_path.stem + "-espaces.png")),
                 f"Espaces entre traits : aucun sous {MIN_GAP_MM} mm (rien ne risque de se boucher)",
                 f"Espaces entre traits : {{n}} zone(s) sous {MIN_GAP_MM} mm, risque de se boucher", "bleu")
    shapes_only = {(a.x_cm, a.y_cm) for a in find_narrow_gaps(svg_path, width_mm).areas}
    with_text = find_narrow_gaps(svg_path, width_mm, keep_text=True,
                                 preview_path=svg_path.with_name(svg_path.stem + "-espaces-textes.png"))
    text_only = with_text._replace(areas=[a for a in with_text.areas if (a.x_cm, a.y_cm) not in shapes_only])
    report_areas(text_only, "Espaces autour des textes : rien sous " f"{MIN_GAP_MM} mm",
                 "Textes : {n} zone(s) serrée(s), souvent l'intérieur des lettres (sans risque si la taille de texte est OK) "
                 "— à vérifier", "bleu", warn=False)


def export_png(svg_path: Path, dpi: float):
    png_path = svg_to_png(svg_path, svg_path.with_suffix(".png"), dpi=dpi)
    typer.echo(f"✅ PNG transparent ({dpi:g} dpi) : {png_path}")


def available_themes():
    theme_paths = sorted(THEMES_DIR.glob("*.json"))
    return [
        (path, json.loads(path.read_text(encoding="utf-8")).get("name", path.stem))
        for path in theme_paths
    ]


def select_theme(theme_option: Optional[str]) -> Path:
    themes = available_themes()
    if not themes:
        raise typer.BadParameter(f"Aucun thème trouvé dans {THEMES_DIR}")

    if theme_option:
        requested_path = Path(theme_option)
        if requested_path.is_file():
            return requested_path

        normalized_option = theme_option.casefold()
        for path, name in themes:
            if normalized_option in (path.stem.casefold(), path.name.casefold(), name.casefold()):
                return path
        choices = ", ".join(path.stem for path, _ in themes)
        raise typer.BadParameter(f"Thème inconnu : {theme_option}. Choix disponibles : {choices}")

    typer.echo("Thèmes disponibles :")
    for index, (path, name) in enumerate(themes, start=1):
        typer.echo(f"  {index}. {name} ({path.stem})")

    selection = typer.prompt("Choisissez un thème", type=int)
    if selection < 1 or selection > len(themes):
        raise typer.BadParameter(f"Choisissez un nombre entre 1 et {len(themes)}")
    return themes[selection - 1][0]


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", normalized.lower())).strip("-")


def default_output_path(name: str, theme: Theme, detail: bool, folder: Path) -> Path:
    """<folder>/<name>-<thème>[-detail].svg : un fichier distinct par thème et par mode."""
    suffix = "-detail" if detail else ""
    return folder / f"{slugify(name)}-{slugify(theme.name)}{suffix}.svg"


def device_output_folder(device: DeviceLayout) -> Path:
    """output/<fabricant>-<modèle>/"""
    return OUTPUT_DIR / slugify(f"{device.manufacturer}-{device.model}")


def scene_output_folder(scene_path: Path) -> Path:
    """output/scenes/<nom du fichier de scène>/"""
    return OUTPUT_DIR / "scenes" / slugify(scene_path.stem)


def load_theme(theme_path: Path) -> Theme:
    with open(theme_path, "r", encoding="utf-8") as f:
        return Theme(**json.load(f))


def render_device_file(device_path: Path, theme: Theme, detail: bool, output_path: Optional[Path] = None) -> Path:
    """Rend une machine en SVG et renvoie le chemin écrit."""
    with open(device_path, "r", encoding="utf-8") as f:
        device = DeviceLayout(**json.load(f))
    if output_path is None:
        output_path = default_output_path(f"{device.manufacturer}-{device.model}", theme, detail, device_output_folder(device))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    render_svg(device, theme, str(output_path), show_labels=detail)
    return output_path


def render_scene_file(scene_path: Path, theme: Theme, detail: bool, output_path: Optional[Path] = None) -> Path:
    """Rend une scène en SVG et renvoie le chemin écrit. Lève ValueError si la scène est invalide."""
    if output_path is None:
        output_path = default_output_path(f"scene-{scene_path.stem}", theme, detail, scene_output_folder(scene_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    render_scene_svg(scene_path=str(scene_path), output_path=str(output_path), theme=theme, show_labels=detail)
    return output_path


def text_output_folder(name: str) -> Path:
    """output/texts/<nom>/"""
    return OUTPUT_DIR / "texts" / slugify(name)


def render_text_file(text_path: Path, theme: Theme, detail: bool = False, output_path: Optional[Path] = None) -> Path:
    """Rend un bloc de texte décrit en JSON (`texts/*.json`) en SVG recadré. `detail` est sans effet."""
    with open(text_path, "r", encoding="utf-8") as f:
        block = TextBlock(**json.load(f))
    if output_path is None:
        output_path = default_output_path(text_path.stem, theme, False, text_output_folder(text_path.stem))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return render_text_svg(block, output_path, theme)


@app.command()
def render(
    device_path: Path = typer.Argument(..., help="Chemin du fichier JSON du device"),
    theme_option: Optional[str] = typer.Option(None, "--theme", "-t", help="Nom du thème ou chemin vers son fichier JSON"),
    output_path: Optional[Path] = typer.Option(None, "--output", "-o", help="Chemin du fichier SVG généré (par défaut : nom automatique)"),
    show_labels: bool = typer.Option(False, "--labels/--no-labels", help="Afficher les détails des commandes"),
    show_details: bool = typer.Option(False, "--detail", help="Afficher les légendes et symboles imprimés sur les commandes"),
    png: bool = PNG_OPTION,
    dpi: float = DPI_OPTION,
    print_width: Optional[float] = PRINT_OPTION,
):
    """Rendu d'un appareil unique au format SVG."""
    typer.echo(f"Chargement du device : {device_path}")
    theme_path = select_theme(theme_option)
    typer.echo(f"Chargement du thème : {theme_path}")
    output_path = render_device_file(device_path, load_theme(theme_path), show_labels or show_details, output_path)
    typer.echo(f"✅ Fichier SVG généré avec succès : {output_path}")
    if print_width:
        export_print(output_path, print_width)
    elif png:
        export_png(output_path, dpi)


@app.command(name="render-scene")
def render_scene(
    scene_path: Path = typer.Argument(..., help="Chemin du fichier JSON de la scène"),
    theme_option: Optional[str] = typer.Option(None, "--theme", "-t", help="Nom du thème ou chemin vers son fichier JSON"),
    output_path: Optional[Path] = typer.Option(None, "--output", "-o", help="Chemin du fichier SVG de la scène généré"),
    show_labels: bool = typer.Option(False, "--labels/--no-labels", help="Afficher les détails des commandes"),
    show_details: bool = typer.Option(False, "--detail", help="Afficher les légendes, symboles, ports et noms des câbles"),
    png: bool = PNG_OPTION,
    dpi: float = DPI_OPTION,
    print_width: Optional[float] = PRINT_OPTION,
):
    """Rendu d'une scène complète avec plusieurs appareils et câblage."""
    typer.echo(f"Chargement de la scène : {scene_path}")
    theme_path = select_theme(theme_option)
    typer.echo(f"Chargement du thème : {theme_path}")
    try:
        output_path = render_scene_file(scene_path, load_theme(theme_path), show_labels or show_details, output_path)
    except ValueError as error:  # inclut les ValidationError pydantic
        typer.secho(f"❌ Scène invalide : {error}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    typer.echo(f"✅ Scène SVG générée avec succès : {output_path}")
    if print_width:
        export_print(output_path, print_width)
    elif png:
        export_png(output_path, dpi)


@app.command(name="render-text")
def render_text(
    text_path: Optional[Path] = typer.Argument(None, help="Fichier JSON du texte (dossier texts/)"),
    text: Optional[str] = typer.Option(None, "--text", help="Texte direct : **gras**, le reste en fin ; lignes séparées par |"),
    font: Optional[str] = typer.Option(None, "--font", help="Police (liste CSS, ex. \"Helvetica Neue, Arial\")"),
    size: Optional[float] = typer.Option(None, "--size", help="Taille de police en mm"),
    spacing: Optional[float] = typer.Option(None, "--spacing", help="Espacement des lettres en em (ex. 0.15)"),
    theme_option: Optional[str] = typer.Option(None, "--theme", "-t", help="Nom du thème ou chemin vers son fichier JSON"),
    output_path: Optional[Path] = typer.Option(None, "--output", "-o", help="Chemin du SVG généré"),
    png: bool = PNG_OPTION,
    dpi: float = DPI_OPTION,
    print_width: Optional[float] = PRINT_OPTION,
):
    """Rendu d'un texte seul (titre) en SVG recadré, avec gras et fin dans une même ligne."""
    if (text_path is None) == (text is None):
        raise typer.BadParameter("Donne soit un fichier JSON, soit --text")
    if text_path is not None:
        with open(text_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        name = text_path.stem
    else:
        data = {"lines": [line.strip() for line in text.split("|") if line.strip()]}
        name = slugify(text.replace("*", ""))[:40] or "texte"
    overrides = {"font_family": font, "size_mm": size, "letter_spacing_em": spacing}
    data.update({key: value for key, value in overrides.items() if value is not None})
    theme = load_theme(select_theme(theme_option))
    if output_path is None:
        output_path = default_output_path(name, theme, False, text_output_folder(name))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        output_path = render_text_svg(TextBlock(**data), output_path, theme)
    except ValueError as error:
        typer.secho(f"❌ Texte invalide : {error}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    typer.echo(f"✅ Texte SVG généré : {output_path}")
    if print_width:
        export_print(output_path, print_width)
    elif png:
        export_png(output_path, dpi)


@app.command(name="render-all")
def render_all(
    theme_option: Optional[str] = typer.Option(None, "--theme", "-t", help="Limiter à un thème (par défaut : tous)"),
    png: bool = PNG_OPTION,
    dpi: float = DPI_OPTION,
):
    """Génère tout : machines (devices/) et scènes (scenes/) avec et sans --detail, et textes (texts/), dans chaque thème."""
    themes = [select_theme(theme_option)] if theme_option else [path for path, _ in available_themes()]
    devices = sorted(DEVICES_DIR.glob("*/*.json"))
    scenes = sorted(SCENES_DIR.glob("*.json"))
    texts = sorted(TEXTS_DIR.glob("*.json"))
    jobs = ([(render_device_file, path, mode) for path in devices for mode in (False, True)]
            + [(render_scene_file, path, mode) for path in scenes for mode in (False, True)]
            + [(render_text_file, path, False) for path in texts])          # un texte n'a pas de mode détail
    total = len(jobs) * len(themes)
    typer.echo(f"{len(devices)} machines, {len(scenes)} scènes, {len(texts)} textes, {len(themes)} thèmes : {total} rendus")

    failures, done = [], 0
    for theme_path in themes:
        theme = load_theme(theme_path)
        for renderer_function, source, detail in jobs:
            done += 1
            label = f"{source.relative_to(ROOT_DIR).as_posix()} · {theme_path.stem}{' · détail' if detail else ''}"
            try:
                svg_path = renderer_function(source, theme, detail)
                if png:
                    svg_to_png(svg_path, svg_path.with_suffix(".png"), dpi=dpi)
                typer.echo(f"[{done}/{total}] ✅ {svg_path.as_posix()}")
            except Exception as error:  # un rendu raté ne bloque pas les autres
                failures.append((label, error))
                typer.secho(f"[{done}/{total}] ❌ {label} : {error}", fg=typer.colors.RED, err=True)

    if failures:
        typer.secho(f"{total - len(failures)}/{total} rendus réussis, {len(failures)} en échec :", fg=typer.colors.RED, err=True)
        for label, error in failures:
            typer.secho(f"  - {label} : {error}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    typer.echo(f"✅ {total} rendus générés{' (SVG + PNG)' if png else ''}")


if __name__ == "__main__":
    app()
