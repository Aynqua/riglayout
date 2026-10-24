from pydantic import BaseModel, Field, root_validator
from typing import Dict, Any, Optional

class ComponentStyle(BaseModel):
    fill: str
    stroke: str = "none"
    stroke_width: float = 0.0
    rx: float = 0.0
    indicator_color: str = "#ffffff"

class LabelStyle(BaseModel):
    fill: Optional[str] = None
    font_family: str = "sans-serif"
    font_size_mm: float = Field(2.5, gt=0)
    min_font_weight: Optional[int] = Field(
        None, ge=100, le=900,
        description="Graisse minimale des textes (ex. 400 pour l'impression : remplace les graisses trop fines)",
    )

class CableColors(BaseModel):
    """Couleur d'un câble selon le type de signal de ses ports."""
    audio: str = "#3b82f6"
    midi: str = "#ef4444"
    usb: str = "#a855f7"
    power: str = "#facc15"

class CableStyle(BaseModel):
    width_mm: float = Field(1.2, gt=0, description="Épaisseur d'un câble")
    spacing_mm: float = Field(2.2, gt=0, description="Distance entre deux câbles parallèles (axe à axe)")
    clearance_mm: float = Field(6.0, gt=0, description="Distance minimale entre un câble et une machine")
    corner_radius_mm: float = Field(1.5, ge=0, description="Rayon des coudes")
    opacity: float = Field(0.95, gt=0, le=1)
    label_font_size_mm: float = Field(2.0, gt=0, description="Taille du nom d'un câble (mode détail)")
    colors: CableColors = Field(default_factory=CableColors)

    @root_validator(skip_on_failure=True)
    def validate_spacing(cls, values):
        if values["spacing_mm"] < values["width_mm"]:
            raise ValueError("cables.spacing_mm doit être supérieur ou égal à cables.width_mm, sinon les câbles se chevauchent")
        return values

class PortStyle(BaseModel):
    """Prises et noms des ports, dessinés en mode détail."""
    fill: Optional[str] = None  # None → même couleur que les légendes
    marker_radius_mm: float = Field(1.0, gt=0)
    stroke_width_mm: float = Field(0.3, gt=0)
    font_size_mm: float = Field(1.6, gt=0)
    label_gap_mm: float = Field(0.8, ge=0, description="Espace entre la prise et le début du nom")

class Theme(BaseModel):
    name: str
    variant: str = Field("screen", description="Variante appliquée aux composants qui en définissent une (ex. print)")
    background: Dict[str, Any]
    components: Dict[str, ComponentStyle]
    labels: LabelStyle = Field(default_factory=LabelStyle)
    ports: PortStyle = Field(default_factory=PortStyle)
    cables: CableStyle = Field(default_factory=CableStyle)
