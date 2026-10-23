import json
import re
import unicodedata
import typer
from pathlib import Path
from typing import Optional
from renderer.models import DeviceLayout, Theme
from renderer.device import render_svg
from renderer.scene import render_scene_svg
from renderer.export import DEFAULT_DPI, svg_to_png

app = typer.Typer()
ROOT_DIR = Path(__file__).resolve().parent
THEMES_DIR = ROOT_DIR / "themes"
DEVICES_DIR = ROOT_DIR / "devices"
SCENES_DIR = ROOT_DIR / "scenes"
OUTPUT_DIR = Path("output")  # relatif au dossier courant

PNG_OPTION = typer.Option(False, "--png", help="Exporter aussi un PNG transparent à côté du SVG")
DPI_OPTION = typer.Option(DEFAULT_DPI, "--dpi", help="Résolution du PNG (points par pouce)")


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


@app.command()
def render(
    device_path: Path = typer.Argument(..., help="Chemin du fichier JSON du device"),
    theme_option: Optional[str] = typer.Option(None, "--theme", "-t", help="Nom du thème ou chemin vers son fichier JSON"),
    output_path: Optional[Path] = typer.Option(None, "--output", "-o", help="Chemin du fichier SVG généré (par défaut : nom automatique)"),
    show_labels: bool = typer.Option(False, "--labels/--no-labels", help="Afficher les détails des commandes"),
    show_details: bool = typer.Option(False, "--detail", help="Afficher les légendes et symboles imprimés sur les commandes"),
    png: bool = PNG_OPTION,
    dpi: float = DPI_OPTION,
):
    """Rendu d'un appareil unique au format SVG."""
    typer.echo(f"Chargement du device : {device_path}")
    theme_path = select_theme(theme_option)
    typer.echo(f"Chargement du thème : {theme_path}")
    output_path = render_device_file(device_path, load_theme(theme_path), show_labels or show_details, output_path)
    typer.echo(f"✅ Fichier SVG généré avec succès : {output_path}")
    if png:
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
    if png:
        export_png(output_path, dpi)


@app.command(name="render-all")
def render_all(
    theme_option: Optional[str] = typer.Option(None, "--theme", "-t", help="Limiter à un thème (par défaut : tous)"),
    png: bool = PNG_OPTION,
    dpi: float = DPI_OPTION,
):
    """Génère tout : chaque machine de devices/ et chaque scène de scenes/, dans chaque thème, avec et sans --detail."""
    themes = [select_theme(theme_option)] if theme_option else [path for path, _ in available_themes()]
    devices = sorted(DEVICES_DIR.glob("*/*.json"))
    scenes = sorted(SCENES_DIR.glob("*.json"))
    jobs = [(render_device_file, path) for path in devices] + [(render_scene_file, path) for path in scenes]
    total = len(jobs) * len(themes) * 2
    typer.echo(f"{len(devices)} machines, {len(scenes)} scènes, {len(themes)} thèmes, avec et sans détail : {total} rendus")

    failures, done = [], 0
    for theme_path in themes:
        theme = load_theme(theme_path)
        for renderer_function, source in jobs:
            for detail in (False, True):
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
