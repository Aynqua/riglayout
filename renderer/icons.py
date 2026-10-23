from svgwrite.path import Path
from svgwrite.shapes import Circle, Line, Polyline, Rect
from svgwrite.container import Group

def draw_device_logo(dwg, logo, center_x: float, center_y: float, color: str):
    draw_custom_icon(
        dwg, logo.icon_path_d, logo.icon_view_box,
        center_x, center_y, logo.width_mm, logo.height_mm,
        color, logo.icon_fill_rule, logo.icon_mode
    )

def draw_custom_icon(
    dwg, path_d: str, view_box: tuple,
    center_x: float, center_y: float, width: float, height: float,
    color: str, fill_rule: str = "nonzero", mode: str = "fill"
):
    view_x, view_y, view_width, view_height = view_box
    scale = min(width / view_width, height / view_height)
    translate_x = center_x - (view_x + view_width / 2) * scale
    translate_y = center_y - (view_y + view_height / 2) * scale
    transform = f"translate({translate_x} {translate_y}) scale({scale})"

    fill = "none" if mode == "stroke" else color
    stroke = color if mode == "stroke" else "none"
    stroke_width = min(width, height) * 0.06 if mode == "stroke" else 0

    dwg.add(Path(
        d=path_d, transform=transform, fill=fill,
        fill_rule=fill_rule, stroke=stroke, stroke_width=stroke_width,
        stroke_linecap="round", stroke_linejoin="round"
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
        transform = f"translate({center_x} {center_y}) scale({scale}) translate({-source_x} {-source_y})"
        group = Group(transform=transform)
        
        if icon == "perform":
            group.add(Path(
                d="M119.876 260.88V251.026H130.434M123.395 253.842H130.434M123.395 256.657H130.434M123.395 259.473H130.434",
                fill="none", stroke=color, stroke_width=1.40775, stroke_linecap="round", stroke_linejoin="round"
            ))
            group.add(Circle(center=(118.468, 260.88), r=2.111, fill=color, stroke="none"))
        elif icon == "save_project":
            group.add(Path(
                d="M170.23 248.563L170.974 250.301L171.705 250.446L173.058 249.125L173.925 249.553L173.701 251.43L174.262 251.922L176.093 251.454L176.63 252.258L175.497 253.771L175.737 254.478L177.557 254.988L177.62 255.953L175.883 256.697L175.737 257.429L177.058 258.782L176.63 259.649L174.753 259.424L174.262 259.985L174.729 261.817L173.925 262.354L172.412 261.22L171.705 261.46L171.195 263.281L170.23 263.344L169.486 261.606L168.754 261.46L167.402 262.782L166.534 262.354L166.759 260.476L166.198 259.985L164.366 260.453L163.829 259.649L164.963 258.135L164.723 257.429L162.902 256.918L162.839 255.953L164.577 255.209L164.723 254.478L163.401 253.125L163.829 252.258L165.707 252.483L166.198 251.922L165.731 250.09L166.534 249.553L168.048 250.686L168.754 250.446L169.265 248.626L170.23 248.563Z",
                fill="none", stroke=color, stroke_width=0.985427, stroke_linejoin="round"
            ))
            group.add(Circle(center=(170.23, 255.953), r=3.1675, fill="none", stroke=color, stroke_width=1.19659))
        elif icon == "samples":
            group.add(Path(
                d="M209.376 253.138V258.769M212.544 249.618V262.288M215.711 252.434V259.473M218.879 248.915V262.992M222.046 253.138V258.769",
                fill="none", stroke=color, stroke_width=1.40775, stroke_linecap="round", stroke_linejoin="round"
            ))
        else:
            group.add(Path(
                d="M266.089 253.894L267.419 258.769C267.888 260.646 267.419 261.584 266.011 261.584H257.565C256.157 261.584 255.688 260.646 256.157 258.769L259.676 251.73C260.146 250.322 260.849 249.618 261.788 249.618H263.196C264.369 249.618 265.073 250.088 265.307 251.026L266.089 253.894ZM266.089 253.894L261.084 258.065M266.089 253.894L269.531 251.026",
                fill="none", stroke=color, stroke_width=1.40775, stroke_linecap="round", stroke_linejoin="round"
            ))
        dwg.add(group)
        return

    if icon in ("play", "stop"):
        viewbox_size = 16 if icon == "play" else 14
        scale = min(width * 0.38 / viewbox_size, height * 0.5 / viewbox_size)
        transform = (
            f"translate({center_x} {center_y}) scale({scale}) "
            f"translate({-viewbox_size / 2} {-viewbox_size / 2})"
        )
        path = (
            "M3.24867 1.95785C2.81552 1.5247 2.59894 1.95785 2.59894 3.25732V13.0033C2.59894 13.8696 3.03209 14.0862 3.8984 13.653L12.9947 8.45517C13.861 8.02202 13.861 7.58886 12.9947 7.15571L3.24867 1.95785Z"
            if icon == "play" else
            "M3.41109 1.1446H10.2333C11.4892 1.1446 12.5073 2.16274 12.5073 3.41867V10.2409C12.5073 11.4968 11.4892 12.5149 10.2333 12.5149H3.41109C2.15516 12.5149 1.13702 11.4968 1.13702 10.2409V3.41867C1.13702 2.16274 2.15516 1.1446 3.41109 1.1446Z"
        )
        dwg.add(Path(
            d=path, transform=transform, fill="none", stroke=color,
            stroke_width=1.62433 if icon == "play" else 1.42129,
            stroke_linejoin="round", stroke_linecap="round"
        ))
        return

    scale = min(width, height) * 0.38
    stroke_width = scale * 0.18
    if icon == "record":
        dwg.add(Circle(center=(center_x, center_y), r=scale * 0.72, fill="none", stroke=color, stroke_width=stroke_width))
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
        dwg.add(Rect(
            insert=(key_left, key_top), size=(key_size, key_size),
            rx=0.45 * keyboard_scale, fill=color, stroke="none"
        ))
        for separator_x in (6.05334, 10.7693):
            x, top_y = keyboard_point(separator_x, source_min)
            _, bottom_y = keyboard_point(separator_x, 15.4947)
            dwg.add(Line(
                start=(x, top_y), end=(x, bottom_y),
                stroke="#202020", stroke_width=0.703877 * keyboard_scale
            ))
        for black_key_x in (4.22327, 9.1504, 13.3737):
            black_left, black_top = keyboard_point(black_key_x - 2.11163 / 2, source_min)
            black_right, black_bottom = keyboard_point(black_key_x + 2.11163 / 2, 9.15977)
            dwg.add(Rect(
                insert=(black_left, black_top),
                size=(black_right - black_left, black_bottom - black_top),
                rx=0.12 * keyboard_scale, fill="#202020", stroke="none"
            ))
        return

    points_by_icon = {
        "arrow_up": [(-0.5, 0.3), (0, -0.3), (0.5, 0.3)],
        "arrow_down": [(-0.5, -0.3), (0, 0.3), (0.5, -0.3)],
        "arrow_left": [(0.3, -0.5), (-0.3, 0), (0.3, 0.5)],
        "arrow_right": [(-0.3, -0.5), (0.3, 0), (-0.3, 0.5)]
    }
    if icon not in points_by_icon:
        raise ValueError(f"Icône intégrée inconnue : {icon}. Fournis icon_path_d et icon_view_box.")
    dwg.add(Polyline(
        points=[(center_x + x * scale, center_y + y * scale) for x, y in points_by_icon[icon]],
        fill="none", stroke=color, stroke_width=stroke_width,
        stroke_linecap="round", stroke_linejoin="round"
    ))