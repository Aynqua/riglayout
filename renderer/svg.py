import math

import svgwrite
from renderer.models import DeviceLayout, LogoComponent
from renderer.themes import Theme


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


def draw_device_logo(dwg, logo: LogoComponent, center_x: float, center_y: float, color: str):
    draw_custom_icon(
        dwg, logo.icon_path_d, logo.icon_view_box,
        center_x, center_y, logo.width_mm, logo.height_mm,
        color, logo.icon_fill_rule, logo.icon_mode
    )


def draw_custom_icon(
    dwg,
    path_d: str,
    view_box: tuple,
    center_x: float,
    center_y: float,
    width: float,
    height: float,
    color: str,
    fill_rule: str = "nonzero",
    mode: str = "fill"
):
    view_x, view_y, view_width, view_height = view_box
    scale = min(width / view_width, height / view_height)
    translate_x = center_x - (view_x + view_width / 2) * scale
    translate_y = center_y - (view_y + view_height / 2) * scale
    transform = f"translate({translate_x} {translate_y}) scale({scale})"

    if mode == "stroke":
        fill = "none"
        stroke = color
        stroke_width = min(width, height) * 0.06
    else:
        fill = color
        stroke = "none"
        stroke_width = 0

    dwg.add(dwg.path(
        d=path_d,
        transform=transform,
        fill=fill,
        fill_rule=fill_rule,
        stroke=stroke,
        stroke_width=stroke_width,
        stroke_linecap="round",
        stroke_linejoin="round"
    ))


def add_control_icon(dwg, icon: str, center_x: float, center_y: float, width: float, height: float, color: str):
    source_icons = {
        "perform": (123.395, 257.154, 14.078, 12.255),
        "save_project": (170.23, 255.954, 14.781, 14.781),
        "samples": (215.711, 255.954, 12.67, 14.077),
        "metronome": (262.844, 255.601, 13.374, 11.966)
    }
    if icon in source_icons:
        source_x, source_y, source_width, source_height = source_icons[icon]
        scale = min(width * 0.55 / source_width, height * 0.55 / source_height)
        transform = (
            f"translate({center_x} {center_y}) scale({scale}) "
            f"translate({-source_x} {-source_y})"
        )
        group = dwg.g(transform=transform)
        if icon == "perform":
            group.add(dwg.path(
                d="M119.876 260.88V251.026H130.434M123.395 253.842H130.434M123.395 256.657H130.434M123.395 259.473H130.434",
                fill="none", stroke=color, stroke_width=1.40775,
                stroke_linecap="round", stroke_linejoin="round"
            ))
            group.add(dwg.circle(
                center=(118.468, 260.88), r=2.111,
                fill=color, stroke="none"
            ))
        elif icon == "save_project":
            group.add(dwg.path(
                d="M170.23 248.563L170.974 250.301L171.705 250.446L173.058 249.125L173.925 249.553L173.701 251.43L174.262 251.922L176.093 251.454L176.63 252.258L175.497 253.771L175.737 254.478L177.557 254.988L177.62 255.953L175.883 256.697L175.737 257.429L177.058 258.782L176.63 259.649L174.753 259.424L174.262 259.985L174.729 261.817L173.925 262.354L172.412 261.22L171.705 261.46L171.195 263.281L170.23 263.344L169.486 261.606L168.754 261.46L167.402 262.782L166.534 262.354L166.759 260.476L166.198 259.985L164.366 260.453L163.829 259.649L164.963 258.135L164.723 257.429L162.902 256.918L162.839 255.953L164.577 255.209L164.723 254.478L163.401 253.125L163.829 252.258L165.707 252.483L166.198 251.922L165.731 250.09L166.534 249.553L168.048 250.686L168.754 250.446L169.265 248.626L170.23 248.563Z",
                fill="none", stroke=color, stroke_width=0.985427,
                stroke_linejoin="round"
            ))
            group.add(dwg.circle(
                center=(170.23, 255.953), r=3.1675,
                fill="none", stroke=color, stroke_width=1.19659
            ))
        elif icon == "samples":
            group.add(dwg.path(
                d="M209.376 253.138V258.769M212.544 249.618V262.288M215.711 252.434V259.473M218.879 248.915V262.992M222.046 253.138V258.769",
                fill="none", stroke=color, stroke_width=1.40775,
                stroke_linecap="round", stroke_linejoin="round"
            ))
        else:
            group.add(dwg.path(
                d="M266.089 253.894L267.419 258.769C267.888 260.646 267.419 261.584 266.011 261.584H257.565C256.157 261.584 255.688 260.646 256.157 258.769L259.676 251.73C260.146 250.322 260.849 249.618 261.788 249.618H263.196C264.369 249.618 265.073 250.088 265.307 251.026L266.089 253.894ZM266.089 253.894L261.084 258.065M266.089 253.894L269.531 251.026",
                fill="none", stroke=color, stroke_width=1.40775,
                stroke_linecap="round", stroke_linejoin="round"
            ))
        dwg.add(group)
        return

    if icon in ("play", "stop"):
        viewbox_size = 16 if icon == "play" else 14
        scale = min(width * 0.38 / viewbox_size, height * 0.5 / viewbox_size)
        icon_color = color
        transform = (
            f"translate({center_x} {center_y}) scale({scale}) "
            f"translate({-viewbox_size / 2} {-viewbox_size / 2})"
        )
        path = (
            "M3.24867 1.95785C2.81552 1.5247 2.59894 1.95785 2.59894 3.25732V13.0033C2.59894 13.8696 3.03209 14.0862 3.8984 13.653L12.9947 8.45517C13.861 8.02202 13.861 7.58886 12.9947 7.15571L3.24867 1.95785Z"
            if icon == "play" else
            "M3.41109 1.1446H10.2333C11.4892 1.1446 12.5073 2.16274 12.5073 3.41867V10.2409C12.5073 11.4968 11.4892 12.5149 10.2333 12.5149H3.41109C2.15516 12.5149 1.13702 11.4968 1.13702 10.2409V3.41867C1.13702 2.16274 2.15516 1.1446 3.41109 1.1446Z"
        )
        dwg.add(dwg.path(
            d=path,
            transform=transform,
            fill="none",
            stroke=icon_color,
            stroke_width=1.62433 if icon == "play" else 1.42129,
            stroke_linejoin="round",
            stroke_linecap="round"
        ))
        return

    scale = min(width, height) * 0.38
    stroke_width = scale * 0.18
    if icon == "record":
        dwg.add(dwg.circle(
            center=(center_x, center_y), r=scale * 0.72,
            fill="none", stroke=color, stroke_width=stroke_width
        ))
        return
    if icon == "stop":
        dwg.add(dwg.rect(
            insert=(center_x - scale * 0.65, center_y - scale * 0.65),
            size=(scale * 1.3, scale * 1.3),
            rx=scale * 0.52,
            fill="none",
            stroke=color,
            stroke_width=stroke_width
        ))
        return
    if icon == "keyboard":
        source_min = 1.40775
        source_size = 14.07755
        keyboard_scale = min(width * 0.42 / source_size, height * 0.58 / source_size)
        left = center_x - 8.5 * keyboard_scale
        top = center_y - 8.5 * keyboard_scale

        def keyboard_point(x: float, y: float):
            return left + x * keyboard_scale, top + y * keyboard_scale

        key_left, key_top = keyboard_point(source_min, source_min)
        key_size = source_size * keyboard_scale
        dwg.add(dwg.rect(
            insert=(key_left, key_top),
            size=(key_size, key_size),
            rx=0.45 * keyboard_scale,
            fill=color,
            stroke="none"
        ))
        for separator_x in (6.05334, 10.7693):
            x, top_y = keyboard_point(separator_x, source_min)
            _, bottom_y = keyboard_point(separator_x, 15.4947)
            dwg.add(dwg.line(
                start=(x, top_y),
                end=(x, bottom_y),
                stroke="#202020",
                stroke_width=0.703877 * keyboard_scale
            ))
        for black_key_x in (4.22327, 9.1504, 13.3737):
            black_left, black_top = keyboard_point(black_key_x - 2.11163 / 2, source_min)
            black_right, black_bottom = keyboard_point(black_key_x + 2.11163 / 2, 9.15977)
            dwg.add(dwg.rect(
                insert=(black_left, black_top),
                size=(black_right - black_left, black_bottom - black_top),
                rx=0.12 * keyboard_scale,
                fill="#202020",
                stroke="none"
            ))
        return
    if icon == "perform":
        note_x = center_x - scale * 0.55
        note_y = center_y + scale * 0.38
        stem_x = note_x + scale * 0.28
        dwg.add(dwg.circle(center=(note_x, note_y), r=scale * 0.17, fill=color, stroke="none"))
        dwg.add(dwg.line(
            start=(stem_x, note_y),
            end=(stem_x, center_y - scale * 0.66),
            stroke=color,
            stroke_width=stroke_width
        ))
        for line_index, line_length in enumerate((1.15, 1.42, 1.22)):
            line_y = center_y - scale * 0.55 + line_index * scale * 0.42
            dwg.add(dwg.line(
                start=(stem_x, line_y),
                end=(stem_x + scale * line_length, line_y),
                stroke=color,
                stroke_width=stroke_width
            ))
        return
    if icon == "save_project":
        radius = scale * 0.72
        gear_points = []
        for point_index in range(32):
            angle = point_index * math.pi / 16
            point_radius = radius if point_index % 4 in (0, 1) else radius * 0.76
            gear_points.append((
                center_x + point_radius * math.cos(angle),
                center_y + point_radius * math.sin(angle)
            ))
        dwg.add(dwg.polygon(
            points=gear_points,
            fill="none",
            stroke=color,
            stroke_width=stroke_width,
            stroke_linejoin="round"
        ))
        dwg.add(dwg.circle(
            center=(center_x, center_y),
            r=radius * 0.24,
            fill="none",
            stroke=color,
            stroke_width=stroke_width
        ))
        for spoke_index in range(8):
            angle = spoke_index * 3.141592653589793 / 4
            inner = radius * 1.1
            outer = radius * 1.42
            dwg.add(dwg.line(
                start=(center_x + inner * math.cos(angle), center_y + inner * math.sin(angle)),
                end=(center_x + outer * math.cos(angle), center_y + outer * math.sin(angle)),
                stroke=color,
                stroke_width=stroke_width
            ))
        return
    if icon == "samples":
        for bar_x, bar_height in ((-0.68, 0.72), (-0.34, 1.25), (0, 0.92), (0.34, 1.18), (0.68, 0.62)):
            x = center_x + bar_x * scale
            dwg.add(dwg.line(
                start=(x, center_y - scale * bar_height / 2),
                end=(x, center_y + scale * bar_height / 2),
                stroke=color,
                stroke_width=stroke_width * 1.5,
                stroke_linecap="round"
            ))
        return
    if icon == "metronome":
        path = (
            f"M {center_x - scale * 0.68} {center_y + scale * 0.58} "
            f"Q {center_x - scale * 0.76} {center_y + scale * 0.58} {center_x - scale * 0.7} {center_y + scale * 0.42} "
            f"L {center_x - scale * 0.3} {center_y - scale * 0.52} "
            f"Q {center_x - scale * 0.25} {center_y - scale * 0.64} {center_x - scale * 0.1} {center_y - scale * 0.64} "
            f"L {center_x + scale * 0.42} {center_y - scale * 0.64} "
            f"Q {center_x + scale * 0.55} {center_y - scale * 0.64} {center_x + scale * 0.58} {center_y - scale * 0.48} "
            f"L {center_x + scale * 0.72} {center_y + scale * 0.42} "
            f"Q {center_x + scale * 0.75} {center_y + scale * 0.58} {center_x + scale * 0.58} {center_y + scale * 0.58} Z"
        )
        dwg.add(dwg.path(
            d=path,
            fill="none",
            stroke=color,
            stroke_width=stroke_width,
            stroke_linejoin="round",
            stroke_linecap="round"
        ))
        dwg.add(dwg.line(
            start=(center_x + scale * 0.05, center_y + scale * 0.4),
            end=(center_x + scale * 0.35, center_y - scale * 0.38),
            stroke=color,
            stroke_width=stroke_width
        ))
        return
    if icon == "play":
        path = (
            f"M {center_x - scale * 0.42} {center_y - scale * 0.68} "
            f"Q {center_x - scale * 0.56} {center_y - scale * 0.76} {center_x - scale * 0.56} {center_y - scale * 0.57} "
            f"L {center_x - scale * 0.56} {center_y + scale * 0.57} "
            f"Q {center_x - scale * 0.56} {center_y + scale * 0.76} {center_x - scale * 0.4} {center_y + scale * 0.67} "
            f"L {center_x + scale * 0.55} {center_y + scale * 0.1} "
            f"Q {center_x + scale * 0.73} {center_y} {center_x + scale * 0.55} {center_y - scale * 0.1} Z"
        )
        dwg.add(dwg.path(
            d=path,
            fill="none",
            stroke=color,
            stroke_width=stroke_width,
            stroke_linejoin="round",
            stroke_linecap="round"
        ))
        return
    else:
        points_by_icon = {
            "arrow_up": [(-0.5, 0.3), (0, -0.3), (0.5, 0.3)],
            "arrow_down": [(-0.5, -0.3), (0, 0.3), (0.5, -0.3)],
            "arrow_left": [(0.3, -0.5), (-0.3, 0), (0.3, 0.5)],
            "arrow_right": [(-0.3, -0.5), (0.3, 0), (-0.3, 0.5)]
        }
        if icon not in points_by_icon:
            raise ValueError(f"Icône intégrée inconnue : {icon}. Fournis icon_path_d et icon_view_box.")
        points = points_by_icon[icon]
    dwg.add(dwg.polyline(
        points=[(center_x + x * scale, center_y + y * scale) for x, y in points],
        fill="none",
        stroke=color,
        stroke_width=stroke_width,
        stroke_linecap="round",
        stroke_linejoin="round"
    ))


def default_control_font_size(component, theme: Theme, device_model: str) -> float:
    explicit_font_size = component.legend_font_size_mm
    if explicit_font_size is not None:
        return explicit_font_size

    if device_model.casefold() == "octatrack":
        if component.type == "pad":
            if component.width_mm <= 60:
                return 12.5
            return 16.0
        width = component.width_mm
        if width <= 18:
            return 7.5
        if width <= 26:
            return 9.5
        if width <= 36:
            return 11.5
        if width <= 46:
            return 13.0
        if width <= 65:
            return 16.0
        return 18.5

    max_font_size = min(
        component.width_mm * 0.88 / (max(len(component.legend or ""), 1) * 0.62),
        component.height_mm * 0.55
    )
    return min(theme.labels.font_size_mm, max_font_size)


def add_control_legend(dwg, component, theme: Theme, center_x: float, center_y: float, device_model: str = ""):
    legend = component.legend
    if component.type == "frame" and legend:
        color = component.legend_color or label_color(theme)
        font_size = component.legend_font_size_mm or theme.labels.font_size_mm
        if component.legend_position == "bottom_left":
            left_margin = max(font_size * 1.2, 3.0)
            bottom_margin = max(font_size * 1.1, 2.0)
            text_x = center_x - component.width_mm / 2 + left_margin
            text_y = center_y + component.height_mm / 2 - bottom_margin
            anchor = "start"
        else:
            text_x = center_x
            text_y = center_y
            anchor = "middle"
        dwg.add(dwg.text(
            legend,
            insert=(text_x, text_y),
            text_anchor=anchor,
            dominant_baseline="central",
            fill=color,
            font_family=theme.labels.font_family,
            font_size=font_size,
            font_weight="bold" if component.legend_bold else "normal"
        ))
        return

    if component.type not in ("button", "pad") or (
        not legend and not component.icon and not component.icon_path_d
    ):
        return

    color = component.legend_color or label_color(theme)
    if component.icon_path_d and component.icon_view_box:
        draw_custom_icon(
            dwg, component.icon_path_d, component.icon_view_box,
            center_x, center_y, component.width_mm, component.height_mm,
            color, component.icon_fill_rule, component.icon_mode
        )
    elif component.icon:
        add_control_icon(dwg, component.icon, center_x, center_y, component.width_mm, component.height_mm, color)
    elif legend:
        font_size = default_control_font_size(component, theme, device_model)
        dwg.add(dwg.text(
            legend,
            insert=(center_x, center_y),
            text_anchor="middle",
            dominant_baseline="central",
            fill=color,
            font_family=theme.labels.font_family,
            font_size=font_size,
            font_weight="bold" if component.legend_bold or component.type == "button" else "normal"
        ))
        if component.underline:
            underline_width = min(component.width_mm * 0.66, len(legend) * font_size * 0.58)
            underline_y = center_y + font_size * 0.62
            dwg.add(dwg.line(
                start=(center_x - underline_width / 2, underline_y),
                end=(center_x + underline_width / 2, underline_y),
                stroke=color,
                stroke_width=max(font_size * 0.08, 0.12)
            ))


def render_svg(device: DeviceLayout, theme: Theme, output_path: str, show_labels: bool = False):
    w_mm = device.physical.width_mm
    h_mm = device.physical.height_mm

    # On utilise viewbox en mm pour garder des proportions exactes
    dwg = svgwrite.Drawing(
        output_path,
        size=(f"{w_mm}mm", f"{h_mm}mm"),
        viewBox=f"0 0 {w_mm} {h_mm}"
    )

    bg_style = theme.background
    dwg.add(dwg.rect(
        insert=(0, 0),
        size=(w_mm, h_mm),
        rx=bg_style.get("rx", 0),
        fill=bg_style.get("fill", "none"),
        stroke=bg_style.get("stroke", "none"),
        stroke_width=bg_style.get("stroke_width", 0)
    ))

    # 2. Dessin des composants
    for comp in device.components:
        # Conversion coordonnées normalisées -> mm réels
        cx = comp.x * w_mm
        cy = comp.y * h_mm

        if comp.type == "logo":
            draw_device_logo(dwg, comp, cx, cy, comp.fill or label_color(theme))
            continue

        style = theme.components.get(comp.type)
        if not style:
            continue

        if comp.type == "screen":
            x = cx - (comp.width_mm / 2)
            y = cy - (comp.height_mm / 2)
            dwg.add(dwg.rect(
                insert=(x, y),
                size=(comp.width_mm, comp.height_mm),
                rx=style.rx,
                fill=comp.fill or style.fill,
                stroke=comp.stroke or style.stroke,
                stroke_width=style.stroke_width
            ))

        elif comp.type == "encoder":
            r = comp.diameter_mm / 2
            dwg.add(dwg.circle(
                center=(cx, cy),
                r=r,
                fill=comp.fill or style.fill,
                stroke=comp.stroke or style.stroke,
                stroke_width=style.stroke_width
            ))

        elif comp.type in ("button", "pad"):
            x = cx - (comp.width_mm / 2)
            y = cy - (comp.height_mm / 2)
            dwg.add(dwg.rect(
                insert=(x, y),
                size=(comp.width_mm, comp.height_mm),
                rx=style.rx,
                fill=comp.fill or style.fill,
                stroke=comp.stroke or style.stroke,
                stroke_width=style.stroke_width
            ))

        elif comp.type == "led":
            r = comp.diameter_mm / 2
            dwg.add(dwg.circle(
                center=(cx, cy),
                r=r,
                fill=comp.fill or style.fill,
                stroke=comp.stroke or style.stroke,
                stroke_width=style.stroke_width
            ))

        elif comp.type == "screw":
            r = comp.diameter_mm / 2
            dwg.add(dwg.circle(
                center=(cx, cy),
                r=r,
                fill=comp.fill or style.fill,
                stroke=comp.stroke or style.stroke,
                stroke_width=style.stroke_width
            ))

        elif comp.type == "frame":
            x = cx - (comp.width_mm / 2)
            y = cy - (comp.height_mm / 2)
            dwg.add(dwg.rect(
                insert=(x, y),
                size=(comp.width_mm, comp.height_mm),
                rx=style.rx,  # <-- Modification ici (accès direct à l'attribut Pydantic)
                fill=comp.fill or style.fill,
                stroke=comp.stroke or style.stroke,
                stroke_width=style.stroke_width
            ))

        if show_labels:
            add_control_legend(dwg, comp, theme, cx, cy, device.model)

    dwg.save()