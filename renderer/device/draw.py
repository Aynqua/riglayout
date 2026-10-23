"""Dessin d'un appareil : formes des composants, partagé entre le rendu seul et la scène."""
import svgwrite
from svgwrite.shapes import Rect, Circle

from renderer.models.device import DeviceLayout
from renderer.models.theme import Theme
from renderer.device.icons import draw_device_logo
from renderer.device.legends import add_control_legend, label_color


def draw_device_to_group(dwg_container, layout: DeviceLayout, theme: Theme, show_labels: bool = False):
    """Dessine les composants d'un device directement dans un groupe SVG conteneur."""
    for comp in layout.components:
        cx = comp.x * layout.physical.width_mm
        cy = comp.y * layout.physical.height_mm

        if comp.type == "logo":
            draw_device_logo(dwg_container, comp, cx, cy, comp.fill or label_color(theme))
            if show_labels:
                add_control_legend(dwg_container, comp, theme, cx, cy)
            continue

        style = theme.components.get(comp.type)
        if not style:
            continue

        if comp.type == "screen":
            x = cx - (comp.width_mm / 2)
            y = cy - (comp.height_mm / 2)
            dwg_container.add(Rect(
                insert=(x, y), size=(comp.width_mm, comp.height_mm), rx=style.rx,
                fill=comp.fill or style.fill, stroke=comp.stroke or style.stroke, stroke_width=style.stroke_width
            ))
        elif comp.type in ("encoder", "led", "screw"):
            r = comp.diameter_mm / 2
            dwg_container.add(Circle(
                center=(cx, cy), r=r, fill=comp.fill or style.fill,
                stroke=comp.stroke or style.stroke, stroke_width=style.stroke_width
            ))
        elif comp.type in ("button", "pad", "frame"):
            x = cx - (comp.width_mm / 2)
            y = cy - (comp.height_mm / 2)
            dwg_container.add(Rect(
                insert=(x, y), size=(comp.width_mm, comp.height_mm), rx=style.rx,
                fill=comp.fill or style.fill, stroke=comp.stroke or style.stroke, stroke_width=style.stroke_width
            ))

        if show_labels:
            add_control_legend(dwg_container, comp, theme, cx, cy)


def render_svg(device: DeviceLayout, theme: Theme, output_path: str, show_labels: bool = False):
    w_mm = device.physical.width_mm
    h_mm = device.physical.height_mm

    dwg = svgwrite.Drawing(output_path, size=(f"{w_mm}mm", f"{h_mm}mm"), viewBox=f"0 0 {w_mm} {h_mm}")
    bg_style = theme.background
    dwg.add(Rect(insert=(0, 0), size=(w_mm, h_mm), rx=bg_style.get("rx", 0), fill=bg_style.get("fill", "none"), stroke=bg_style.get("stroke", "none"), stroke_width=bg_style.get("stroke_width", 0)))

    draw_device_to_group(dwg, device, theme, show_labels=show_labels)
    dwg.save()
