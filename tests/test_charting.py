from __future__ import annotations

from type_record.charting import smooth_trend_points, trend_coords, trend_geometry


def test_trend_geometry_uses_actual_widget_size_without_virtual_clipping() -> None:
    width, height, ml, mr, mt, mb, cw, ch = trend_geometry(500, 180)

    assert width == 500
    assert height == 180
    assert ml + mr + cw == width
    assert mt + mb + ch == height
    assert ch > 0


def test_trend_coords_stay_inside_plot_area() -> None:
    data = [{"count": 0}, {"count": 50}, {"count": 100}]
    _width, _height, ml, _mr, mt, _mb, cw, ch = trend_geometry(500, 180)

    coords = trend_coords(data, ml, mt, cw, ch, max_count=100)

    assert coords[0][0] == ml
    assert coords[-1][0] == ml + cw
    assert all(mt <= y <= mt + ch for _x, y, _item in coords)


def test_smooth_trend_points_pass_through_real_points_and_stay_in_bounds() -> None:
    data = [{"count": 10}, {"count": 80}, {"count": 20}, {"count": 100}]
    _width, _height, ml, _mr, mt, _mb, cw, ch = trend_geometry(640, 260)
    coords = trend_coords(data, ml, mt, cw, ch, max_count=100)

    points = smooth_trend_points(coords, mt, mt + ch)
    pairs = list(zip(points[0::2], points[1::2], strict=True))

    assert pairs[0] == (coords[0][0], coords[0][1])
    assert pairs[-1] == (coords[-1][0], coords[-1][1])
    assert all(mt <= y <= mt + ch for _x, y in pairs)
