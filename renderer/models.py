from typing import List, Literal, Optional, Tuple, Union
from pydantic import BaseModel, Field, root_validator

class PhysicalDimensions(BaseModel):
    width_mm: float = Field(..., gt=0, description="Largeur totale en mm")
    height_mm: float = Field(..., gt=0, description="Hauteur totale en mm")
    depth_mm: Optional[float] = Field(None, gt=0, description="Profondeur en mm")

class BaseComponent(BaseModel):
    x: float = Field(..., ge=0.0, le=1.0, description="Position X normalisée (centre)")
    y: float = Field(..., ge=0.0, le=1.0, description="Position Y normalisée (centre)")
    label: Optional[str] = None
    legend: Optional[str] = None
    icon: Optional[str] = None
    icon_path_d: Optional[str] = None
    icon_view_box: Optional[Tuple[float, float, float, float]] = None
    icon_fill_rule: Literal["nonzero", "evenodd"] = "nonzero"
    icon_mode: Literal["fill", "stroke"] = "fill"
    fill: Optional[str] = None
    stroke: Optional[str] = None
    legend_color: Optional[str] = None
    legend_position: Literal["center", "bottom_left"] = "center"
    legend_bold: bool = False
    legend_font_size_mm: Optional[float] = Field(None, gt=0)
    underline: bool = False

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

Component = Union[
    EncoderComponent,
    ButtonComponent,
    ScreenComponent,
    PadComponent,
    LEDComponent,
    ScrewComponent,
    FrameComponent,
    LogoComponent,
]

class DeviceLayout(BaseModel):
    manufacturer: str
    model: str
    physical: PhysicalDimensions
    components: List[Component] = Field(default_factory=list)
    ports: List[DevicePort] = Field(default_factory=list)