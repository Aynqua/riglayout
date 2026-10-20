from typing import List, Literal, Optional, Union
from pydantic import BaseModel, Field

class PhysicalDimensions(BaseModel):
    width_mm: float = Field(..., gt=0, description="Largeur totale en mm")
    height_mm: float = Field(..., gt=0, description="Hauteur totale en mm")
    depth_mm: Optional[float] = Field(None, gt=0, description="Profondeur en mm")

class BaseComponent(BaseModel):
    x: float = Field(..., ge=0.0, le=1.0, description="Position X normalisée (centre)")
    y: float = Field(..., ge=0.0, le=1.0, description="Position Y normalisée (centre)")
    label: Optional[str] = None
    legend: Optional[str] = None
    icon: Optional[Literal["play", "record", "stop", "keyboard", "perform", "save_project", "samples", "metronome", "elektron", "arrow_up", "arrow_down", "arrow_left", "arrow_right"]] = None
    fill: Optional[str] = None
    stroke: Optional[str] = None
    legend_color: Optional[str] = None
    legend_position: Literal["center", "bottom_left"] = "center"
    legend_bold: bool = False
    legend_font_size_mm: Optional[float] = Field(None, gt=0)
    underline: bool = False

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
    icon: Literal["elektron"]
    width_mm: float = Field(..., gt=0)
    height_mm: float = Field(..., gt=0)

class DevicePort(BaseModel):
    id: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    direction: Literal["input", "output"]
    signal: Literal["audio", "midi"]

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