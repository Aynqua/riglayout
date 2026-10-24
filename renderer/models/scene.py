from typing import List, Literal, Optional, Union
from pydantic import BaseModel, Field

from renderer.models.text import TextBlock


class AbsolutePosition(BaseModel):
    type: Literal["absolute"] = "absolute"
    x: float
    y: float


class RelativePosition(BaseModel):
    type: Literal["relative"] = "relative"
    anchor: Literal["right", "left", "top", "bottom"] = "right"
    target: str = Field(..., min_length=1)
    spacing_mm: float = 15.0


class SceneDevice(BaseModel):
    id: str = Field(..., min_length=1)
    device: str = Field(..., min_length=1)
    position: Union[AbsolutePosition, RelativePosition]


class PortEndpoint(BaseModel):
    device_id: str = Field(..., min_length=1)
    port_id: str = Field(..., min_length=1)


class SceneConnection(BaseModel):
    source: PortEndpoint
    target: PortEndpoint
    label: Optional[str] = None


class Scene(BaseModel):
    name: str = Field(..., min_length=1)
    devices: List[SceneDevice] = Field(default_factory=list)
    connections: List[SceneConnection] = Field(default_factory=list)
    title: Optional[TextBlock] = None          # texte centré au-dessus de la scène
    title_gap_mm: float = Field(20.0, ge=0, description="Espace entre le titre et la scène")
