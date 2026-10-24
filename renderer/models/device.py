from typing import Any, Dict, List, Literal, Optional, Tuple, Union
from pydantic import BaseModel, Field, root_validator

class PhysicalDimensions(BaseModel):
    width_mm: float = Field(..., gt=0, description="Largeur totale en mm")
    height_mm: float = Field(..., gt=0, description="Hauteur totale en mm")
    depth_mm: Optional[float] = Field(None, gt=0, description="Profondeur en mm")

class TextSpan(BaseModel):
    """Morceau d'une légende avec son propre style (ex. « Digitakt » gras + « II » fin)."""
    text: str = Field(..., min_length=1)
    weight: Optional[int] = Field(None, ge=100, le=900, description="Graisse CSS : 100 (très fin) à 900 (très gras)")
    font_family: Optional[str] = None
    color: Optional[str] = None
    font_size_mm: Optional[float] = Field(None, gt=0)

class BaseComponent(BaseModel):
    x: float = Field(..., ge=0.0, le=1.0, description="Position X normalisée (centre)")
    y: float = Field(..., ge=0.0, le=1.0, description="Position Y normalisée (centre)")
    label: Optional[str] = None
    legend: Optional[str] = None
    icon: Optional[str] = None
    icon_path_d: Optional[Union[str, List[str]]] = None  # un path SVG, ou une liste de paths copiés tels quels
    icon_view_box: Optional[Tuple[float, float, float, float]] = None
    icon_fill_rule: Literal["nonzero", "evenodd"] = "nonzero"
    icon_mode: Literal["fill", "stroke"] = "fill"
    icon_linecap: Literal["round", "butt", "square"] = "round"  # extrémités des traits (mode stroke)
    icon_stroke_width: Optional[float] = Field(None, gt=0, description="Épaisseur du trait en unités du icon_view_box (mode stroke)")
    fill: Optional[str] = None
    stroke: Optional[str] = None
    legend_color: Optional[str] = None
    legend_position: Literal["center", "bottom_left"] = "center"
    legend_bold: bool = False
    legend_font_size_mm: Optional[float] = Field(None, gt=0)
    legend_letter_spacing_em: float = 0.0  # espacement des lettres de la légende, en fraction de sa taille
    legend_always: bool = False  # légende imprimée sur la machine (nom, marque) : visible même sans --detail
    legend_spans: Optional[List[TextSpan]] = None  # légende en plusieurs styles ; `legend` devient leur concaténation
    font_family: Optional[str] = None  # police de la légende ; None → police des légendes du thème
    underline: bool = False
    # Champs redéfinis selon la variante du thème (ex. {"print": {"hidden": true}} pour le t-shirt).
    variants: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    @root_validator(pre=True)
    def legend_from_spans(cls, values):
        spans = values.get("legend_spans")
        if spans and not values.get("legend"):
            values["legend"] = "".join(span["text"] if isinstance(span, dict) else span.text for span in spans)
        return values

    @root_validator(skip_on_failure=True)
    def validate_custom_icon(cls, values):
        path = values.get("icon_path_d")
        view_box = values.get("icon_view_box")
        if bool(path) != bool(view_box):
            raise ValueError("icon_path_d et icon_view_box doivent être renseignés ensemble")
        if view_box and (view_box[2] <= 0 or view_box[3] <= 0):
            raise ValueError("La largeur et la hauteur de icon_view_box doivent être positives")
        return values

class EncoderComponent(BaseComponent):
    type: Literal["encoder"]
    diameter_mm: float = Field(..., gt=0)
    variant: Optional[str] = "standard"  # ex: standard, large

class ButtonComponent(BaseComponent):
    type: Literal["button"]
    width_mm: float = Field(..., gt=0)
    height_mm: float = Field(..., gt=0)
    shape: Optional[str] = "rect"  # ex: rect, circle, square

class ScreenComponent(BaseComponent):
    type: Literal["screen"]
    width_mm: float = Field(..., gt=0)
    height_mm: float = Field(..., gt=0)

class PadComponent(BaseComponent):
    type: Literal["pad"]
    width_mm: float = Field(..., gt=0)
    height_mm: float = Field(..., gt=0)

class LEDComponent(BaseComponent):
    type: Literal["led"]
    diameter_mm: float = Field(..., gt=0)

class ScrewComponent(BaseComponent):
    type: Literal["screw"]
    diameter_mm: float = Field(..., gt=0)

class FrameComponent(BaseComponent):
    type: Literal["frame"]
    width_mm: float = Field(..., gt=0)
    height_mm: float = Field(..., gt=0)

class LogoComponent(BaseComponent):
    type: Literal["logo"]
    width_mm: float = Field(..., gt=0)
    height_mm: float = Field(..., gt=0)

    @root_validator(skip_on_failure=True)
    def validate_logo_source(cls, values):
        if not values.get("icon_path_d") or not values.get("icon_view_box"):
            raise ValueError("Un logo doit définir icon_path_d et icon_view_box")
        return values

class TextComponent(BaseComponent):
    """Inscription imprimée sur la machine (marque, modèle, titre de section) : toujours visible.
    Le texte est dans `legend` ; `x`/`y` désignent le point d'ancrage (`text_anchor`) sur la ligne médiane du texte."""
    type: Literal["text"]
    legend: str = Field(..., min_length=1)
    text_anchor: Literal["start", "middle", "end"] = "middle"
    width_mm: Optional[float] = Field(None, gt=0, description="Étire ou resserre le texte à cette largeur exacte")
    detail_only: bool = False  # inscription trop petite pour la vue d'ensemble : seulement avec --detail

class DevicePort(BaseModel):
    id: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    direction: Literal["input", "output", "bidirectional"]
    signal: Literal["audio", "midi", "usb", "power"]
    connector: Optional[str] = None
    channels: Optional[int] = Field(None, gt=0)
    balanced: Optional[bool] = None
    voltage_v: Optional[float] = Field(None, gt=0)
    current_a: Optional[float] = Field(None, gt=0)
    capabilities: List[str] = Field(default_factory=list)
    x: float = Field(0.5, ge=0.0, le=1.0, description="Position X relative sur l'appareil")
    y: float = Field(1.0, ge=0.0, le=1.0, description="Position Y relative (ex: 1.0 = bord inférieur)")

Component = Union[
    EncoderComponent,
    ButtonComponent,
    ScreenComponent,
    PadComponent,
    LEDComponent,
    ScrewComponent,
    FrameComponent,
    LogoComponent,
    TextComponent,
]

class DeviceLayout(BaseModel):
    manufacturer: str
    model: str
    physical: PhysicalDimensions
    components: List[Component] = Field(default_factory=list)
    ports: List[DevicePort] = Field(default_factory=list)