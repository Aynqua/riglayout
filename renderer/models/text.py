"""Blocs de texte typographiques (titres) : lignes en balisage léger, gras et fin dans une même ligne."""
import re
from typing import List, Literal, NamedTuple, Optional, Union

from pydantic import BaseModel, Field, validator

_BOLD = re.compile(r"\*\*(.+?)\*\*")


class Run(NamedTuple):
    text: str
    bold: bool


def parse_markup(markup: str) -> List[Run]:
    """« **NAYS** LIVE SETUP » → [Run('NAYS', gras), Run(' LIVE SETUP', fin)]. Les espaces sont conservés."""
    runs: List[Run] = []
    position = 0
    for match in _BOLD.finditer(markup):
        if match.start() > position:
            runs.append(Run(markup[position:match.start()], False))
        runs.append(Run(match.group(1), True))
        position = match.end()
    if position < len(markup):
        runs.append(Run(markup[position:], False))
    return [run for run in runs if run.text]


class TextLine(BaseModel):
    text: str = Field(..., min_length=1, description="Balisage : **gras**, le reste dans la graisse fine")
    size_mm: Optional[float] = Field(None, gt=0, description="Taille de police ; défaut : celle du bloc")
    letter_spacing_em: Optional[float] = Field(None, description="Espacement des lettres en em ; défaut : celui du bloc")
    bold_weight: Optional[int] = Field(None, ge=100, le=900)
    regular_weight: Optional[int] = Field(None, ge=100, le=900)
    font_family: Optional[str] = None
    color: Optional[str] = None


class TextBlock(BaseModel):
    lines: List[Union[TextLine, str]] = Field(..., min_items=1)
    font_family: str = "Helvetica Neue, Arial, sans-serif"
    color: Optional[str] = None                     # None → couleur des légendes du thème
    size_mm: float = Field(12.0, gt=0)
    letter_spacing_em: float = 0.08
    bold_weight: int = Field(700, ge=100, le=900)
    regular_weight: int = Field(200, ge=100, le=900)
    line_gap_em: float = Field(0.45, ge=0, description="Espace entre deux lignes, en em de la ligne suivante")
    align: Literal["left", "center", "right"] = "center"
    uppercase: bool = False

    @validator("lines", pre=True, each_item=True)
    def line_from_string(cls, value):
        return {"text": value} if isinstance(value, str) else value
