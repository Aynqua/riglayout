import json
import os
import svgwrite
from typing import List, Mapping, Optional
from pydantic import BaseModel, Field

from renderer.models import DeviceLayout
from renderer.svg import render_svg

class SceneDevice(BaseModel):
    id: str = Field(..., min_length=1)
    device: str = Field(..., min_length=1)
    x: float = Field(..., ge=0.0, le=1.0)
    y: float = Field(..., ge=0.0, le=1.0)


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


def validate_scene_connections(
    scene: Scene,
    layouts_by_instance: Mapping[str, DeviceLayout]
) -> None:
    instance_ids = [device.id for device in scene.devices]
    if len(instance_ids) != len(set(instance_ids)):
        raise ValueError("Les identifiants des appareils de la scène doivent être uniques")

    for instance_id in instance_ids:
        if instance_id not in layouts_by_instance:
            raise ValueError(f"Layout manquant pour l'appareil de scène '{instance_id}'")
        port_ids = [port.id for port in layouts_by_instance[instance_id].ports]
        if len(port_ids) != len(set(port_ids)):
            raise ValueError(f"Les identifiants de ports doivent être uniques pour '{instance_id}'")

    for connection in scene.connections:
        if (
            connection.source.device_id not in instance_ids
            or connection.target.device_id not in instance_ids
        ):
            raise ValueError("Une connexion référence un appareil absent de la scène")

        source_layout = layouts_by_instance.get(connection.source.device_id)
        target_layout = layouts_by_instance.get(connection.target.device_id)
        if source_layout is None or target_layout is None:
            raise ValueError("Une connexion référence un appareil absent de la scène")

        source_port = next(
            (port for port in source_layout.ports if port.id == connection.source.port_id),
            None
        )
        target_port = next(
            (port for port in target_layout.ports if port.id == connection.target.port_id),
            None
        )
        if source_port is None or target_port is None:
            raise ValueError("Une connexion référence un port inconnu")
        if source_port.direction not in ("output", "bidirectional"):
            raise ValueError(f"Le port source '{source_port.id}' doit être une sortie")
        if target_port.direction not in ("input", "bidirectional"):
            raise ValueError(f"Le port cible '{target_port.id}' doit être une entrée")
        if source_port.signal != target_port.signal:
            raise ValueError(
                f"Types de signal incompatibles : {source_port.signal} vers {target_port.signal}"
            )


def render_scene_svg(scene_path: str, output_path: str, theme, scene_width_mm: float = 1200.0, scene_height_mm: float = 800.0):
    # 1. Charger le fichier de scène JSON
    with open(scene_path, 'r', encoding='utf-8') as f:
        scene_data = json.load(f)
    scene = Scene(**scene_data)

    # 2. Charger les layouts de chaque appareil référencé
    layouts_by_instance = {}
    
    for dev_ref in scene.devices:
        with open(dev_ref.device, 'r', encoding='utf-8') as f:
            dev_json = json.load(f)
        layout = DeviceLayout(**dev_json)
        layouts_by_instance[dev_ref.id] = layout

    # 3. Valider la cohérence des connexions
    validate_scene_connections(scene, layouts_by_instance)

    # 4. Initialiser le dessin SVG global de la scène
    dwg = svgwrite.Drawing(
        output_path,
        size=(f"{scene_width_mm}mm", f"{scene_height_mm}mm"),
        viewBox=f"0 0 {scene_width_mm} {scene_height_mm}"
    )

    # Fond de scène
    dwg.add(dwg.rect(insert=(0, 0), size=(scene_width_mm, scene_height_mm), fill="#111111"))

    port_coordinates = {}

    # 5. Dessiner chaque appareil sur la scène
    # 5. Dessiner chaque appareil sur la scène avec tous ses détails
    for dev_ref in scene.devices:
        layout = layouts_by_instance[dev_ref.id]
        
        dev_w = layout.physical.width_mm
        dev_h = layout.physical.height_mm
        
        center_x = dev_ref.x * scene_width_mm
        center_y = dev_ref.y * scene_height_mm
        top_left_x = center_x - (dev_w / 2)
        top_left_y = center_y - (dev_h / 2)

        # Groupe principal pour l'appareil, positionné aux coordonnées de la scène
        device_group = dwg.g(transform=f"translate({top_left_x} {top_left_y})")

        # Fond de l'appareil (basé sur le thème)
        bg_style = theme.background
        device_group.add(dwg.rect(
            insert=(0, 0),
            size=(dev_w, dev_h),
            rx=bg_style.get("rx", 6),
            fill=bg_style.get("fill", "#222222"),
            stroke=bg_style.get("stroke", "#444444"),
            stroke_width=bg_style.get("stroke_width", 1.5)
        ))

        # Dessin des composants de la machine (encodeurs, pads, écran, etc.)
        for comp in layout.components:
            cx = comp.x * dev_w
            cy = comp.y * dev_h

            if comp.type == "logo":
                # Optionnel : appel à ton rendu de logo si besoin
                continue

            style = theme.components.get(comp.type)
            if not style:
                continue

            if comp.type == "screen":
                x = cx - (comp.width_mm / 2)
                y = cy - (comp.height_mm / 2)
                device_group.add(dwg.rect(
                    insert=(x, y),
                    size=(comp.width_mm, comp.height_mm),
                    rx=style.rx,
                    fill=comp.fill or style.fill,
                    stroke=comp.stroke or style.stroke,
                    stroke_width=style.stroke_width
                ))
            elif comp.type in ("encoder", "led", "screw"):
                r = comp.diameter_mm / 2
                device_group.add(dwg.circle(
                    center=(cx, cy),
                    r=r,
                    fill=comp.fill or style.fill,
                    stroke=comp.stroke or style.stroke,
                    stroke_width=style.stroke_width
                ))
            elif comp.type in ("button", "pad", "frame", "logo"):
                x = cx - (comp.width_mm / 2)
                y = cy - (comp.height_mm / 2)
                device_group.add(dwg.rect(
                    insert=(x, y),
                    size=(comp.width_mm, comp.height_mm),
                    rx=style.rx,
                    fill=comp.fill or style.fill,
                    stroke=comp.stroke or style.stroke,
                    stroke_width=style.stroke_width
                ))

        dwg.add(device_group)

        # Enregistrer les coordonnées absolues des ports pour les câbles
        for port in layout.ports:
            p_abs_x = top_left_x + (port.x * dev_w)
            p_abs_y = top_left_y + (port.y * dev_h)
            port_coordinates[(dev_ref.id, port.id)] = (p_abs_x, p_abs_y)

    # 6. Dessiner les connexions (câbles orthogonaux)
    for conn in scene.connections:
        source_key = (conn.source.device_id, conn.source.port_id)
        target_key = (conn.target.device_id, conn.target.port_id)

        if source_key in port_coordinates and target_key in port_coordinates:
            x1, y1 = port_coordinates[source_key]
            x2, y2 = port_coordinates[target_key]

            offset_y = -35.0
            mid_y = min(y1, y2) + offset_y

            path_d = f"M {x1} {y1} L {x1} {mid_y} L {x2} {mid_y} L {x2} {y2}"
            cable_color = "#e67e22" if "midi" in conn.source.port_id else "#3498db"

            dwg.add(dwg.path(
                d=path_d,
                fill="none",
                stroke=cable_color,
                stroke_width=3.0,
                stroke_linecap="round",
                stroke_linejoin="round",
                opacity=0.85
            ))

    dwg.save()
    print(f"Scène rendue avec succès dans : {output_path}")