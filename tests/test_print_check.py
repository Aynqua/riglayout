from renderer.print_check import MIN_LINE_MM, analyse_print


def write_svg(tmp_path, body, width=200, height=100):
    path = tmp_path / "a.svg"
    path.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}mm" height="{height}mm" viewBox="0 0 {width} {height}">{body}</svg>',
        encoding="utf-8",
    )
    return path


def test_print_size_scale_and_pixels(tmp_path):
    report = analyse_print(write_svg(tmp_path, ""), print_width_mm=100)
    assert report.scale == 0.5
    assert report.print_height_mm == 50
    assert report.dpi == 150                       # 300 dpi à la taille imprimée
    assert report.pixels == (1181, 591)


def test_thin_lines_and_small_texts_are_counted_after_scaling(tmp_path):
    body = (
        '<path d="M0 0H10" stroke="#fff" stroke-width="2"/>'           # 2 mm × 0.5 = 1 mm : OK
        '<path d="M0 0H10" stroke="#fff" stroke-width="0.8"/>'         # 0.4 mm : trop fin
        '<g transform="translate(5 5) scale(0.1)"><path d="M0 0H9" stroke="#fff" stroke-width="8"/></g>'  # 0.4 mm
        '<path d="M0 0H10" stroke="none" stroke-width="0.1"/>'         # pas de trait : ignoré
        '<text font-size="6">OK</text><text font-size="3">petit</text>'  # 3 mm et 1.5 mm imprimés
    )
    report = analyse_print(write_svg(tmp_path, body), print_width_mm=100)
    assert report.thin_lines == 2
    assert abs(report.thinnest_line_mm - 0.4) < 1e-9
    assert report.small_texts == 1
    assert abs(report.smallest_text_mm - 1.5) < 1e-9
    assert MIN_LINE_MM == 0.5


def test_thin_filled_shapes_are_found(tmp_path):
    from renderer.print_check import find_thin_areas
    body = (
        '<rect x="10" y="10" width="40" height="0.6" fill="#fff"/>'   # 0.3 mm une fois imprimé à 50 % : trop fin
        '<rect x="10" y="40" width="40" height="4" fill="#fff"/>'     # 2 mm : OK
        '<circle cx="150" cy="50" r="5" fill="#fff"/>'                # disque plein : OK, y compris ses bords courbes
    )
    report = find_thin_areas(write_svg(tmp_path, body), print_width_mm=100, preview_path=tmp_path / "p.png")
    assert len(report.areas) == 1
    area = report.areas[0]
    assert 0.4 <= area.x_cm <= 0.6 and area.y_cm <= 0.6   # le trait fin, près de (5 mm, 5 mm) imprimés
    assert report.preview_path.exists()


def test_text_is_ignored_by_thin_area_check(tmp_path):
    from renderer.print_check import find_thin_areas
    report = find_thin_areas(write_svg(tmp_path, '<text x="10" y="20" font-size="3">fin</text>'), print_width_mm=100)
    assert report.areas == []


def test_narrow_gaps_between_lines_are_found(tmp_path):
    from renderer.print_check import find_narrow_gaps
    body = (
        '<rect x="10" y="10" width="60" height="2" fill="#fff"/>'
        '<rect x="10" y="12.6" width="60" height="2" fill="#fff"/>'    # 0.6 mm d'écart → 0.3 mm imprimé : se bouche
        '<rect x="10" y="40" width="60" height="2" fill="#fff"/>'
        '<rect x="10" y="44" width="60" height="2" fill="#fff"/>'      # 2 mm d'écart → 1 mm imprimé : OK
    )
    report = find_narrow_gaps(write_svg(tmp_path, body), print_width_mm=100)
    assert len(report.areas) == 1
    assert report.areas[0].y_cm <= 0.7


def test_text_can_be_excluded_from_gap_check(tmp_path):
    from renderer.print_check import find_narrow_gaps
    body = '<text x="10" y="20" font-size="3" font-weight="700">aaaa</text>'
    svg = write_svg(tmp_path, body)
    assert find_narrow_gaps(svg, print_width_mm=100).areas == []
