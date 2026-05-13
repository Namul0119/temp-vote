def build_chart_data(temp_scores):

    chart_dots = []

    points = []

    for idx, score in enumerate(temp_scores):

        temp_value = 18 + idx

        x = 50 + idx * (610 / 12)

        y = 220 - (score / 100) * 180

        chart_dots.append({
            "temp": temp_value,
            "x": round(x, 1),
            "y": round(y, 1)
        })

        points.append(
            f"{round(x, 1)},{round(y, 1)}"
        )

    chart_points = " ".join(points)

    return chart_points, chart_dots