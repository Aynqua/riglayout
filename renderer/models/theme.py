from pydantic import BaseModel, Field
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

class Theme(BaseModel):
    name: str
    background: Dict[str, Any]
    components: Dict[str, ComponentStyle]
    labels: LabelStyle = Field(default_factory=LabelStyle)