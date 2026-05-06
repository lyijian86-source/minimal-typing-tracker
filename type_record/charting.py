from __future__ import annotations


def trend_geometry(width: int, height: int) -> tuple[int, int, int, int, int, int, int, int]:
    if width <= 1:
        width = 640
    if height <= 1:
        height = 360

    ml = min(56, max(36, int(width * 0.08)))
    mr = min(44, max(28, int(width * 0.06)))
    mt = min(58, max(30, int(height * 0.16)))
    mb = min(46, max(32, int(height * 0.14)))
    return width, height, ml, mr, mt, mb, max(1, width - ml - mr), max(1, height - mt - mb)


def trend_coords(
    data: list[dict],
    ml: int,
    mt: int,
    cw: int,
    ch: int,
    max_count: int,
) -> list[tuple[float, float, dict]]:
    n = len(data)
    plot_max = max(1, max_count) * 1.12
    coords = []
    for index, item in enumerate(data):
        x = ml + cw * index / (n - 1) if n > 1 else ml + cw / 2
        y = mt + ch * (1 - item["count"] / plot_max)
        y = max(mt, min(mt + ch, y))
        coords.append((x, y, item))
    return coords


def flatten_coords(coords: list[tuple[float, float, dict]]) -> list[float]:
    points: list[float] = []
    for x, y, _item in coords:
        points.extend([x, y])
    return points


def smooth_trend_points(coords: list[tuple[float, float, dict]], min_y: float, max_y: float) -> list[float]:
    if len(coords) < 3:
        return flatten_coords(coords)

    points = [(x, y) for x, y, _item in coords]
    smoothed: list[float] = []
    samples_per_segment = 10
    tension = 0.35

    for index in range(len(points) - 1):
        p0 = points[max(0, index - 1)]
        p1 = points[index]
        p2 = points[index + 1]
        p3 = points[min(len(points) - 1, index + 2)]

        for sample in range(samples_per_segment + 1):
            if index > 0 and sample == 0:
                continue
            t = sample / samples_per_segment
            t2 = t * t
            t3 = t2 * t

            m1x = (p2[0] - p0[0]) * tension
            m1y = (p2[1] - p0[1]) * tension
            m2x = (p3[0] - p1[0]) * tension
            m2y = (p3[1] - p1[1]) * tension

            h00 = 2 * t3 - 3 * t2 + 1
            h10 = t3 - 2 * t2 + t
            h01 = -2 * t3 + 3 * t2
            h11 = t3 - t2

            x = h00 * p1[0] + h10 * m1x + h01 * p2[0] + h11 * m2x
            y = h00 * p1[1] + h10 * m1y + h01 * p2[1] + h11 * m2y
            smoothed.extend([x, max(min_y, min(max_y, y))])

    return smoothed
