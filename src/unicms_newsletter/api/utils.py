def _format_week_day(value):
    week_day = ''
    for index, day in enumerate(value):
        week_day+=day
        if index + 1 < len(value): week_day+=','
    return week_day
