import json
import re
import unicodedata
import typer
from pathlib import Path
from typing import Optional
from renderer.models import DeviceLayout
from renderer.themes import Theme
from renderer.svg import render_svg

app = typer.Typer()
THEMES_DIR = Path(__file__).resolve().parent / "themes"


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

@app.command()
def render(
    device_path: Path = typer.Argument(..., help="Chemin du fichier JSON du device"),
    theme_option: Optional[str] = typer.Option(None, "--theme", "-t", help="Nom du thème ou chemin vers son fichier JSON"),
    output_path: Optional[Path] = typer.Option(None, "--output", "-o", help="Chemin du fichier SVG généré (par défaut : nom automatique)"),
    show_labels: bool = typer.Option(False, "--labels/--no-labels", help="Afficher les détails des commandes"),
    show_details: bool = typer.Option(False, "--detail", help="Afficher les légendes et symboles imprimés sur les commandes")
):
    typer.echo(f"Chargement du device : {device_path}")
    with open(device_path, "r", encoding="utf-8") as f:
        device_data = json.load(f)
    device = DeviceLayout(**device_data)

    theme_path = select_theme(theme_option)
    typer.echo(f"Chargement du thème : {theme_path}")
    with open(theme_path, "r", encoding="utf-8") as f:
        theme_data = json.load(f)
    theme = Theme(**theme_data)

    if output_path is None:
        device_name = slugify(f"{device.manufacturer}-{device.model}")
        theme_name = slugify(theme.name)
        output_path = Path("output") / f"{device_name}-{theme_name}.svg"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    render_svg(device, theme, str(output_path), show_labels=show_labels or show_details)
    typer.echo(f"✅ Fichier SVG généré avec succès : {output_path}")

if __name__ == "__main__":
    app()