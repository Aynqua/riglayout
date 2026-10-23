"""Export PNG d'un SVG généré : fond transparent, résolution en DPI (impression textile : 300 dpi)."""
from pathlib import Path
from typing import Union

import resvg_py

DEFAULT_DPI = 300


def svg_to_png(svg_path: Union[str, Path], png_path: Union[str, Path], dpi: float = DEFAULT_DPI) -> Path:
    """Rasterise `svg_path` en PNG RGBA transparent. Les tailles en mm du SVG sont converties à `dpi`."""
    if dpi <= 0:
        raise ValueError("dpi doit être positif")
    png_bytes = bytes(resvg_py.svg_to_bytes(svg_path=str(svg_path), dpi=dpi))
    png_path = Path(png_path)
    png_path.parent.mkdir(parents=True, exist_ok=True)
    png_path.write_bytes(png_bytes)
    return png_path
