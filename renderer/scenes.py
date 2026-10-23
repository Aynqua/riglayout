import json
import os
import svgwrite
from typing import List, Mapping, Optional, Union, Literal
from pydantic import BaseModel, Field

from renderer.models import DeviceLayout
from renderer.themes import Theme
from renderer.svg import draw_device_to_group
from svgwrite.shapes import Rect
from svgwrite.path import Path

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


def render_scene_svg(
    scene_path: str,
    output_path: str,
    theme: Theme,
    padding_mm: float = 80.0,
    show_labels: bool = False
):
    # 1. Charger le fichier de scène JSON
    with open(scene_path, 'r', encoding='utf-8') as f:
        scene_data = json.load(f)
    scene = Scene(**scene_data)

    if not scene.devices:
        raise ValueError("La scène ne contient aucun appareil à rendre.")

    # 2. Charger les layouts de chaque appareil référencé
    layouts_by_instance = {}
    for dev_ref in scene.devices:
        with open(dev_ref.device, 'r', encoding='utf-8') as f:
            dev_json = json.load(f)
        layout = DeviceLayout(**dev_json)
        layouts_by_instance[dev_ref.id] = layout

    # 3. Valider la cohérence des connexions
    validate_scene_connections(scene, layouts_by_instance)

    # 4. Résolution intelligente des positions (Absolues et Relatives en cascade)
    resolved_rects = {}  # id -> (top_left_x, top_left_y, width, height)
    unresolved = list(scene.devices)
    iterations = 0

    while unresolved and iterations < 10:
        next_unresolved = []
        for dev_ref in unresolved:
            layout = layouts_by_instance[dev_ref.id]
            dev_w = layout.physical.width_mm
            dev_h = layout.physical.height_mm
            pos = dev_ref.position

            if pos.type == "absolute":
                resolved_rects[dev_ref.id] = (pos.x, pos.y, dev_w, dev_h)
            elif pos.type == "relative":
                target_id = pos.target
                if target_id in resolved_rects:
                    t_x, t_y, t_w, t_h = resolved_rects[target_id]
                    spacing = pos.spacing_mm

                    if pos.anchor == "right":
                        x = t_x + t_w + spacing
                        y = t_y
                    elif pos.anchor == "left":
                        x = t_x - dev_w - spacing
                        y = t_y
                    elif pos.anchor == "bottom":
                        x = t_x
                        y = t_y + t_h + spacing
                    elif pos.anchor == "top":
                        x = t_x
                        y = t_y - dev_h - spacing
                    else:
                        x, y = t_x + t_w + spacing, t_y

                    resolved_rects[dev_ref.id] = (x, y, dev_w, dev_h)
                else:
                    next_unresolved.append(dev_ref)

        if len(unresolved) == len(next_unresolved):
            raise ValueError("Erreur de dépendance circulaire ou cible introuvable dans les positions relatives.")
        unresolved = next_unresolved
        iterations += 1

    # 5. Calcul automatique des dimensions globales de la scène
    min_x, max_x = float('inf'), float('-inf')
    min_y, max_y = float('inf'), float('-inf')

    for x, y, w, h in resolved_rects.values():
        min_x = min(min_x, x)
        max_x = max(max_x, x + w)
        min_y = min(min_y, y)
        max_y = max(max_y, y + h)

    scene_width_mm = (max_x - min_x) + (padding_mm * 2)
    scene_height_mm = (max_y - min_y) + (padding_mm * 2)

    offset_x = padding_mm - min_x
    offset_y = padding_mm - min_y

    # 6. Initialiser le dessin SVG global de la scène
    dwg = svgwrite.Drawing(
        output_path,
        size=(f"{scene_width_mm}mm", f"{scene_height_mm}mm"),
        viewBox=f"0 0 {scene_width_mm} {scene_height_mm}"
    )

    # Fond de scène dynamique
    dwg.add(Rect(insert=(0, 0), size=(scene_width_mm, scene_height_mm), fill="#111111"))
    port_coordinates = {}

    # 7. Dessiner chaque appareil sur la scène à l'aide du moteur partagé
    for dev_ref in scene.devices:
        layout = layouts_by_instance[dev_ref.id]
        rx, ry, dev_w, dev_h = resolved_rects[dev_ref.id]

        final_x = rx + offset_x
        final_y = ry + offset_y

        device_group = dwg.g(transform=f"translate({final_x} {final_y})")

        # Fond de l'appareil (basé sur le thème)
        bg_style = theme.background
        device_group.add(Rect(
            insert=(0, 0),
            size=(dev_w, dev_h),
            rx=bg_style.get("rx", 6),
            fill=bg_style.get("fill", "#222222"),
            stroke=bg_style.get("stroke", "#444444"),
            stroke_width=bg_style.get("stroke_width", 1.5)
        ))

        # Dessin unifié des composants et des labels éventuels
        draw_device_to_group(device_group, layout, theme, show_labels=show_labels)

        dwg.add(device_group)

        # Enregistrer les coordonnées absolues des ports pour les câbles
        for port in layout.ports:
            p_abs_x = final_x + (port.x * dev_w)
            p_abs_y = final_y + (port.y * dev_h)
            port_coordinates[(dev_ref.id, port.id)] = (p_abs_x, p_abs_y)

# 8. Routage réaliste type "Goulotte de câbles arrière" (Cable Tray)
    # On trie ou indexe les connexions pour leur donner des pistes parallèles distinctes le long des boîtiers
    for i, conn in enumerate(scene.connections):
        source_key = (conn.source.device_id, conn.source.port_id)
        target_key = (conn.target.device_id, conn.target.port_id)

        if source_key in port_coordinates and target_key in port_coordinates:
            x1, y1 = port_coordinates[source_key]
            x2, y2 = port_coordinates[target_key]

            # 1. Le stub vertical sortant du port (ex: 8mm)
            stub_len = 8.0
            y_out1 = y1 - stub_len
            y_out2 = y2 - stub_len

            # 2. Trouver le sommet de la machine source pour longer sa tranche arrière
            # On place le faisceau de câbles juste au-dessus du bord supérieur du boîtier source
            src_rect = resolved_rects[conn.source.device_id]
            src_top_y = src_rect[1]  # Coordonnée Y du haut de la machine source
            
            # Piste horizontale dédiée pour ce câble (espacée de 3.5mm par rapport aux autres pour éviter la superposition)
            cable_tray_y = src_top_y - 12.0 - (i * 3.5)

            # 3. Tracé orthogonal propre "en goulotte" :
            # - Départ port source
            # - Montée du stub
            # - Trajet horizontal le long du faisceau arrière
            # - Descente vers le port cible
            path_d = (
                f"M {x1} {y1} "
                f"L {x1} {y_out1} "
                f"L {x1} {cable_tray_y} "
                f"L {x2} {cable_tray_y} "
                f"L {x2} {y_out2} "
                f"L {x2} {y2}"
            )

            cable_color = "#e67e22" if "midi" in conn.source.port_id else "#3498db"

            dwg.add(Path(
                d=path_d,
                fill="none",
                stroke=cable_color,
                stroke_width=2.5,
                stroke_linecap="round",
                stroke_linejoin="round",
                opacity=0.9
            ))

    dwg.save()
    print(f"Scène rendue avec succès dans : {output_path} (Taille auto : {scene_width_mm:.1f}x{scene_height_mm:.1f} mm)")