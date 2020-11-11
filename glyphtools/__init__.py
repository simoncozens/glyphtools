"""
glyphtools is a library of routines for extracting information from font glyphs.
"""

import math
import statistics
from .ckmeans import ckmeans
from beziers.path import BezierPath
from beziers.point import Point
import glyphtools.glyphs
import glyphtools.babelfont
import warnings
from beziers.path.representations.fontparts import FontParts


__author__ = """Simon Cozens"""
__email__ = 'simon@simon-cozens.org'
__version__ = '0.5.2'


def categorize_glyph(font, glyphname):
    """Returns the category of the given glyph.

    Args:
        font: a ``fontTools`` TTFont object OR a ``glyphsLib`` GSFontMaster object OR a ``babelfont`` Font object.
        glyphname: name of the glyph.

    Returns:
        A two-element tuple. The first element is one of the following
        strings: ``unknown``, ``base``, ``mark``, ``ligature``, ``component``.
        If the glyph is a mark, the second element is the mark attachment
        class number.
    """
    if glyphs.isglyphs(font):
        return glyphs.categorize_glyph(font, glyphname)
    if babelfont.isbabelfont(font):
        return (font[glyphname].category, None)
    if not "GDEF" in font:
        return ("unknown", None)
    gdef = font["GDEF"].table
    classdefs = gdef.GlyphClassDef.classDefs
    if not glyphname in classdefs:
        return ("unknown", None)
    if classdefs[glyphname] == 1:
        return ("base", None)
    if classdefs[glyphname] == 2:
        return ("ligature", None)
    if classdefs[glyphname] == 3:
        # Now find attachment class
        mclass = None
        if gdef.MarkAttachClassDef:
            markAttachClassDef = gdef.MarkAttachClassDef.classDefs
            if glyphname in markAttachClassDef:
                mclass = markAttachClassDef[glyphname]
        return ("mark", mclass)
    if classdefs[glyphname] == 4:
        return ("component", None)
    return ("unknown", None)


def set_glyph_category(font, glyphname, category, maClass=None):
    """Sets the category of the glyph in the font.

    Args:
        font: a ``fontTools`` TTFont object or a ``glyphsLib`` GSFontMaster object OR a ``babelfont`` Font object.
        glyphname: name of the glyph.
        category: one of ``base``, ``mark``, ``ligature``, ``component``.
        maClass: If the category is ``base``, the mark attachment class number.
    """
    if glyphs.isglyphs(font):
        return glyphs.set_glyph_category(font, glyphname, category)
    if babelfont.isbabelfont(font):
        font[glyphname].category = category
        return

    gdef = font["GDEF"].table
    classdefs = gdef.GlyphClassDef.classDefs
    if category == "base":
        classdefs[glyphname] = 1
    elif category == "ligature":
        classdefs[glyphname] = 2
    elif category == "mark":
        classdefs[glyphname] = 3
        if maClass and gdef.MarkAttachClassDef:
            gdef.MarkAttachClassDef.classDefs[glyphname] = maClass
    elif category == "component":
        classdefs[glyphname] = 4
    else:
        raise ValueError("Unknown category")


def get_glyph_metrics(font, glyphname, **kwargs):
    """Returns glyph metrics as a dictionary.

    Args:
        font: a ``fontTools`` TTFont object or a ``glyphsLib`` GSFontMaster object OR a ``babelfont`` Font object.
        glyphname: name of the glyph.

    Returns: A dictionary with the following keys:
            - ``width``: Advance width of the glyph.
            - ``lsb``: Left side-bearing
            - ``rsb``: Right side-bearing
            - ``xMin``: minimum X coordinate
            - ``xMax``: maximum X coordinate
            - ``yMin``: minimum Y coordinate
            - ``yMax``: maximum Y coordinate
            - ``rise``: difference in Y coordinate between cursive entry and exit
    """
    if glyphs.isglyphs(font):
        return glyphs.get_glyph_metrics(font, glyphname, **kwargs)
    if babelfont.isbabelfont(font):
        return babelfont.get_glyph_metrics(font, glyphname, **kwargs)
    metrics = {}
    if "hmtx" in font:
        metrics = {
            "width": font["hmtx"][glyphname][0],
            "lsb": font["hmtx"][glyphname][1],
        }
    else:
        warnings.warn("No hmtx table in this font!")
        metrics = {
            "width": font["head"].unitsPerEm,
            "lsb": 0
        }
    if "glyf" in font:
        glyf = font["glyf"][glyphname]
        try:
            metrics["xMin"], metrics["xMax"], metrics["yMin"], metrics["yMax"] = (
                glyf.xMin,
                glyf.xMax,
                glyf.yMin,
                glyf.yMax,
            )
        except Exception as e:
            metrics["xMin"], metrics["xMax"], metrics["yMin"], metrics["yMax"] = (
                0,
                0,
                0,
                0,
            )
    else:
        bounds = font.getGlyphSet()[glyphname]._glyph.calcBounds(font.getGlyphSet())
        try:
            metrics["xMin"], metrics["yMin"], metrics["xMax"], metrics["yMax"] = bounds
        except Exception as e:
            metrics["xMin"], metrics["xMax"], metrics["yMin"], metrics["yMax"] = (
                0,
                0,
                0,
                0,
            )
    metrics["rise"] = get_rise(font, glyphname)
    metrics["rsb"] = metrics["width"] - metrics["xMax"]
    return metrics


def get_rise(font, glyphname):
    # Find a cursive positioning feature or it's game over
    if "GPOS" not in font:
        return 0
    t = font["GPOS"].table
    cursives = filter(lambda x: x.LookupType == 3, font["GPOS"].table.LookupList.Lookup)
    anchors = {}
    for c in cursives:
        for s in c.SubTable:
            for glyph, record in zip(s.Coverage.glyphs, s.EntryExitRecord):
                anchors[glyph] = []
                if record.EntryAnchor:
                    anchors[glyph].append(
                        (record.EntryAnchor.XCoordinate, record.EntryAnchor.YCoordinate)
                    )
                if record.ExitAnchor:
                    anchors[glyph].append(
                        (record.ExitAnchor.XCoordinate, record.ExitAnchor.YCoordinate)
                    )
    if glyphname not in anchors:
        return 0
    if len(anchors[glyphname]) == 1:
        return anchors[glyphname][0][1]
    return anchors[glyphname][0][1] - anchors[glyphname][1][1]


def bin_glyphs_by_metric(font, glyphs, category, bincount=5):
    """Organise glyphs according to a given metric.

    Organises similar glyphs into a number of bins. The bins are not
    guaranteed to contain the same number of glyphs; the one-dimensional
    ckmeans clustering algorithm is used to cluster glyphs based on metric
    similarity. For example, if there are five glyphs of width 100, 102, 105,
    210, and 220 units respectively, and you ask for two bins, the first
    bin will contain three glyphs and the second will contain two. This is
    usually what you want.

    Args:
        font: a ``fontTools`` TTFont object or a ``glyphsLib`` GSFontMaster object OR a ``babelfont`` Font object.
        glyphs: a collection of glyph names
        category: the metric (see metric keys in :func:`get_glyph_metrics`.)
        bincount: number of bins to return

    Returns:
        A list of ``bincount`` two-element tuples. The first element is a
        list of glyphnames in this bin; the second is the average metric
        value of the glyphs in this bin.
    """

    metrics = [(g, get_glyph_metrics(font, g)[category]) for g in glyphs]
    justmetrics = [x[1] for x in metrics]
    if bincount > len(glyphs):
        bincount = len(glyphs)
    clusters = ckmeans(justmetrics, bincount)
    binned = []
    for c in clusters:
        thiscluster = []
        for m in metrics:
            if m[1] in c:
                thiscluster.append(m)
        thiscluster = (
            [x[0] for x in thiscluster],
            int(statistics.mean([x[1] for x in thiscluster])),
        )
        binned.append(thiscluster)
    return binned


def determine_kern(
    font, glyph1, glyph2, targetdistance, offset1=(0, 0), offset2=(0, 0), maxtuck=0.4
):
    """Determine a kerning value required to set two glyphs at given
    ink-to-ink distance.

    The value is bounded by the ``maxtuck`` parameter. For example, if
    ``maxtuck`` is 0.20, the right glyph will not be placed any further
    left than 80% of the width of left glyph, even if this places the
    ink further than ``targetdistance`` units away.

    Args:
        font: a ``fontTools`` TTFont object or a ``glyphsLib`` GSFontMaster object OR a ``babelfont`` Font object.
        glyph1: name of the left glyph.
        glyph2: name of the right glyph.
        targetdistance: distance to set the glyphs apart.
        offset1: offset (X-coordinate, Y-coordinate) to place left glyph.
        offset2: offset (X-coordinate, Y-coordinate) to place right glyph.
        maxtuck: maximum proportion of the left glyph's width to kern.

    Returns: A kerning value, in units.
    """
    if glyphs.isglyphs(font):
        paths1 = glyphs.beziers(font, glyph1)
        paths2 = glyphs.beziers(font, glyph2)
    elif glyphs.isbeziers(font):
        paths1 = FontParts.fromFontpartsGlyph(font[glyph1])
        paths2 = FontParts.fromFontpartsGlyph(font[glyph2])
    else:
        paths1 = BezierPath.fromFonttoolsGlyph(font, glyph1)
        paths2 = BezierPath.fromFonttoolsGlyph(font, glyph2)
    metrics1 = get_glyph_metrics(font, glyph1)
    offset1 = Point(*offset1)
    offset2 = Point(offset2[0] + metrics1["width"], offset2[1])
    kern = 0
    lastBest = None

    iterations = 0
    while True:
        # Compute min distance
        minDistance = None
        closestpaths = None
        for p1 in paths1:
            p1 = p1.clone().translate(offset1)
            for p2 in paths2:
                p2 = p2.clone().translate(Point(offset2.x + kern, offset2.y))
                d = p1.distanceToPath(p2, samples=3)
                if not minDistance or d[0] < minDistance:
                    minDistance = d[0]
                    closestsegs = (d[3], d[4])
        if not lastBest or minDistance < lastBest:
            lastBest = minDistance
        else:
            break  # Nothing helped
        if abs(minDistance - targetdistance) < 1 or iterations > 10:
            break
        iterations = iterations + 1
        kern = kern + (targetdistance - minDistance)

    if maxtuck:
        kern = max(kern, -(metrics1["width"] * maxtuck))
    else:
        kern = max(kern, -(metrics1["width"]))
    return int(kern)


def duplicate_glyph(babelfont, existing, new):
    """Add a new glyph to the font duplicating an existing one.

    Args:
        font: a ``babelfont``/``fontParts`` Font object.
        existing: name of the glyph to duplicate.
        new: name of the glyph to add.
    """
    existingGlyph = babelfont.layers[0][existing]
    newGlyph = babelfont.layers[0].newGlyph(new)

    for c in existingGlyph.contours:
        newGlyph.appendContour(c)
    for c in existingGlyph.components:
        newGlyph.appendComponent(c)
    newGlyph.width = existingGlyph.width
    oldCategory = babelfont[existing].category # babelfont only
    set_glyph_category(font, new, oldCategory[0], oldCategory[1])
