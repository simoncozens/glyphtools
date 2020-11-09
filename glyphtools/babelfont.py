def isbabelfont(font):
    return hasattr(font, "_set_kerning")


def get_glyph_metrics(font, glyphname):
    g = font[glyphname]
    metrics = {"width": g.width, "lsb": g.leftMargin, "rsb": g.rightMargin}
    bounds = g.bounds
    if bounds:
        (metrics["xMin"], metrics["yMin"], metrics["xMax"], metrics["yMax"]) = g.bounds
    else:
        (metrics["xMin"], metrics["yMin"], metrics["xMax"], metrics["yMax"]) = (0,0,0,0)
    metrics["rise"] = get_rise(g)
    return metrics


def get_rise(glyph):
    entry = [a.y for a in glyph.anchors if a.name == "entry"]
    entry.append(0)  # In case there isn't one
    exit = [a.y for a in glyph.anchors if a.name == "exit"]
    exit.append(0)

    return entry[0] - exit[0]
