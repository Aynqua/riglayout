import svgwrite
from svgwrite.shapes import Rect, Circle, Line
from svgwrite.text import Text
from svgwrite.path import Path
from renderer.models import DeviceLayout
from renderer.themes import Theme
from renderer.icons import draw_device_logo, add_control_icon, draw_custom_icon

def label_color(theme: Theme) -> str:
    if theme.labels.fill:
        return theme.labels.fill
    background_fill = theme.background.get("fill", "none")
    if background_fill.lower() == "none":
        return theme.background.get("stroke", "#ffffff")
    color = background_fill.lstrip("#")
    if len(color) == 3:
        color = "".join(channel * 2 for channel in color)
    try:
        red, green, blue = (int(color[index:index + 2], 16) for index in (0, 2, 4))
    except ValueError:
        return "#ffffff"
    luminance = (0.299 * red + 0.587 * green + 0.114 * blue) / 255
    return "#111111" if luminance > 0.55 else "#ffffff"

def default_control_font_size(component, theme: Theme) -> float:
    if component.legend_font_size_mm is not None:
        return component.legend_font_size_mm
    max_font_size = min(
        component.width_mm * 0.88 / (max(len(component.legend or ""), 1) * 0.62),
        component.height_mm * 0.55
    )
    return min(theme.labels.font_size_mm, max_font_size)


def add_control_legend(dwg, component, theme: Theme, center_x: float, center_y: float):
    legend = component.legend
    if component.type == "frame" and legend:
        color = component.legend_color or label_color(theme)
        font_size = component.legend_font_size_mm or theme.labels.font_size_mm
        text_x = center_x - component.width_mm / 2 + max(font_size * 1.2, 3.0) if component.legend_position == "bottom_left" else center_x
        text_y = center_y + component.height_mm / 2 - max(font_size * 1.1, 2.0) if component.legend_position == "bottom_left" else center_y
        anchor = "start" if component.legend_position == "bottom_left" else "middle"
        
        dwg.add(Text(
            legend, insert=(text_x, text_y), text_anchor=anchor, dominant_baseline="central",
            fill=color, font_family=theme.labels.font_family, font_size=font_size,
            font_weight="bold" if component.legend_bold else "normal"
        ))
        return

    if component.type not in ("button", "pad") or (not legend and not component.icon and not component.icon_path_d):
        return

    color = component.legend_color or label_color(theme)
    if component.icon_path_d and component.icon_view_box:
        draw_custom_icon(dwg, component.icon_path_d, component.icon_view_box, center_x, center_y, component.width_mm, component.height_mm, color, component.icon_fill_rule, component.icon_mode)
    elif component.icon:
        add_control_icon(dwg, component.icon, center_x, center_y, component.width_mm, component.height_mm, color)
    elif legend:
        font_size = default_control_font_size(component, theme)
        dwg.add(Text(
            legend, insert=(center_x, center_y), text_anchor="middle", dominant_baseline="central",
            fill=color, font_family=theme.labels.font_family, font_size=font_size,
            font_weight="bold" if component.legend_bold or component.type == "button" else "normal"
        ))
        if component.underline:
            underline_width = min(component.width_mm * 0.66, len(legend) * font_size * 0.58)
            underline_y = center_y + font_size * 0.62
            dwg.add(Line(
                start=(center_x - underline_width / 2, underline_y), end=(center_x + underline_width / 2, underline_y),
                stroke=color, stroke_width=max(font_size * 0.08, 0.12)
            ))

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