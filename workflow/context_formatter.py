def _val(row, key):
    return row.get(key, {}).get("value", "")


def _fmt(value, unit=""):
    if not value:
        return "not specified"
    try:
        n = float(value)
        formatted = int(n) if n == int(n) else round(n, 2)
    except (ValueError, TypeError):
        formatted = value
    return f"{formatted}{unit}"


def format_definition(row, jur_override=None):
    jur    = jur_override or _val(row, "jurisdiction")
    year   = _val(row, "year")
    cat    = _val(row, "category")
    canopy = _val(row, "canopy")
    height = _val(row, "height")
    area   = _val(row, "area")
    text   = _val(row, "text")
    source = _val(row, "source")

    header = f"{jur} ({year}):" if (jur and year) else (f"{jur}:" if jur else "Definition:")
    lines = [
        header,
        f"  Category: {_fmt(cat)}",
        f"  Canopy: {_fmt(canopy, '%')}",
        f"  Height: {_fmt(height, ' m')}",
        f"  Area: {_fmt(area, ' ha')}",
    ]
    if text:   lines.append(f"  Text: {text[:300]}")
    if source: lines.append(f"  Source: {source[:100]}")
    return "\n".join(lines)


def format_results(bindings, intent="definitional"):
    if not bindings:
        return None

    if intent == "synthesis":
        lines = []
        for row in bindings:
            parts = [f"{key}: {row[key]['value']}" for key in row]
            lines.append(" | ".join(parts))
        return "\n".join(lines)

    return "\n\n".join(format_definition(row) for row in bindings)
