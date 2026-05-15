def build_analysis(
    cold_count,
    hot_count,
    ac_count,
    temp_gap,
    avg_temp,
    expected_satisfaction
):

    analysis_points = []

    if cold_count > hot_count:
        analysis_points.append(
            "추위를 느끼는 사용자가 더 많습니다."
        )

    elif hot_count > cold_count:
        analysis_points.append(
            "더위를 느끼는 사용자가 더 많습니다."
        )

    else:
        analysis_points.append(
            "추위와 더위 의견이 비슷합니다."
        )

    if ac_count > 0:
        analysis_points.append(
            f"에어컨 근처 사용자가 {ac_count}명 있습니다."
        )

    if temp_gap >= 4:
        analysis_points.append(
            f"사용자 선호 온도 차이가 {temp_gap}°C로 큰 편입니다."
        )
    else:
        analysis_points.append(
            f"사용자 선호 온도 차이는 {temp_gap}°C입니다."
        )

    analysis_points.append(
        f"평균 희망 온도는 {avg_temp}°C입니다."
    )

    if cold_count > hot_count:
        short_reason = (
            "추위를 느끼는 사용자가 더 많아 "
            "온도를 높이는 방향을 고려했습니다."
        )

    elif hot_count > cold_count:
        short_reason = (
            "더위를 느끼는 사용자가 더 많아 "
            "온도를 낮추는 방향을 고려했습니다."
        )

    else:
        short_reason = (
            "추위와 더위 의견이 비슷해 "
            "가장 균형 잡힌 온도를 선택했습니다."
        )

    if expected_satisfaction < 0.5:

        message = (
            "선호 차이가 커 일부 사용자 불편 가능"
        )

        if cold_count > hot_count:
            advice = (
                "추위를 느끼는 사용자가 더 많습니다. "
                "온도를 조금 올리거나, "
                "에어컨 바람을 직접 맞는 사용자의 "
                "자리를 조정하는 것이 좋습니다."
            )

        elif hot_count > cold_count:
            advice = (
                "더위를 느끼는 사용자가 더 많습니다. "
                "온도를 조금 낮추거나, "
                "더운 사용자가 바람이 잘 닿는 자리로 "
                "이동하는 것이 좋습니다."
            )

        else:
            advice = (
                "추운 사용자와 더운 사용자가 비슷합니다. "
                "온도 변경보다는 담요, 자리 이동, "
                "바람 방향 조정 같은 보조 조치가 "
                "더 적합합니다."
            )

    elif expected_satisfaction < 0.7:

        message = (
            "대체로 괜찮지만 일부 불편 가능"
        )

        advice = (
            "추천 온도를 바로 크게 바꾸기보다는 "
            "0.5~1°C 정도만 미세 조정하면서 "
            "반응을 확인하는 것이 좋습니다."
        )

    else:

        message = (
            "대부분 사용자 만족 가능"
        )

        advice = (
            "추천 온도를 적용해도 무리가 적습니다. "
            "다만 시간이 지나면 활동량이나 자리 위치에 따라 "
            "체감이 달라질 수 있습니다."
        )

    return (
        analysis_points,
        short_reason,
        message,
        advice
    )