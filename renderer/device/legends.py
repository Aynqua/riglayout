"""Légendes imprimées sur les commandes : couleur, taille de police, texte ou icône."""
from svgwrite.shapes import Line
from svgwrite.text import TSpan, Text

from renderer.models.theme import Theme
from renderer.device.icons import add_control_icon, draw_custom_icon


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


def legend_text(component, theme: Theme, insert, anchor: str, font_size: float, color: str, bold: bool, **attributes) -> Text:
    """Élément <text> d'une légende. Avec `legend_spans`, chaque morceau devient un <tspan> avec son propre style
    (graisse, police, couleur, taille) ; sinon le texte est `legend` d'un seul tenant."""
    family = component.font_family or theme.labels.font_family
    spans = component.legend_spans
    text = Text(
        "" if spans else component.legend, insert=insert, text_anchor=anchor, dominant_baseline="central",
        fill=color, font_family=family, font_size=font_size, font_weight="bold" if bold else "normal", **attributes
    )
    if spans:
        # Sans cela, l'espace en tête d'un morceau (« Digitakt » + « II ») est supprimé au rendu.
        text.attribs["xml:space"] = "preserve"
    for span in spans or ():
        style = {}
        if span.weight is not None:
            style["font_weight"] = span.weight
        if span.font_family:
            style["font_family"] = span.font_family
        if span.color:
            style["fill"] = span.color
        if span.font_size_mm:
            style["font_size"] = span.font_size_mm
        text.add(TSpan(span.text, **style))
    return text


def add_control_legend(dwg, component, theme: Theme, center_x: float, center_y: float):
    legend = component.legend
    if component.type == "frame" and legend:
        color = component.legend_color or label_color(theme)
        font_size = component.legend_font_size_mm or theme.labels.font_size_mm
        text_x = center_x - component.width_mm / 2 + max(font_size * 1.2, 3.0) if component.legend_position == "bottom_left" else center_x
        text_y = center_y + component.height_mm / 2 - max(font_size * 1.1, 2.0) if component.legend_position == "bottom_left" else center_y
        anchor = "start" if component.legend_position == "bottom_left" else "middle"

        dwg.add(legend_text(component, theme, (text_x, text_y), anchor, font_size, color, component.legend_bold))
        return

    if component.type not in ("button", "pad") or (not legend and not component.icon and not component.icon_path_d):
        return

    color = component.legend_color or label_color(theme)
    if component.icon_path_d and component.icon_view_box:
        draw_custom_icon(dwg, component.icon_path_d, component.icon_view_box, center_x, center_y, component.width_mm, component.height_mm, color, component.icon_fill_rule, component.icon_mode, component.icon_stroke_width, component.icon_linecap)
    elif component.icon:
        add_control_icon(dwg, component.icon, center_x, center_y, component.width_mm, component.height_mm, color)
    elif legend:
        font_size = default_control_font_size(component, theme)
        dwg.add(legend_text(component, theme, (center_x, center_y), "middle", font_size, color,
                            component.legend_bold or component.type == "button"))
        if component.underline:
            underline_width = min(component.width_mm * 0.66, len(legend) * font_size * 0.58)
            underline_y = center_y + font_size * 0.62
            dwg.add(Line(
                start=(center_x - underline_width / 2, underline_y), end=(center_x + underline_width / 2, underline_y),
                stroke=color, stroke_width=max(font_size * 0.08, 0.12)
            ))


def add_printed_text(dwg, component, theme: Theme, x: float, y: float):
    """Inscription imprimée (composant `text`) : toujours dessinée, ancrée en (x, y) sur sa ligne médiane."""
    font_size = component.legend_font_size_mm or theme.labels.font_size_mm
    attributes = {}
    if component.width_mm:
        attributes = {"textLength": component.width_mm, "lengthAdjust": "spacingAndGlyphs"}
    dwg.add(legend_text(component, theme, (x, y), component.text_anchor, font_size,
                        component.legend_color or label_color(theme), component.legend_bold,
                        class_="printed-text", **attributes))
