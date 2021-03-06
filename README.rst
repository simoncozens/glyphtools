===========
glyphtools
===========


.. image:: https://img.shields.io/pypi/v/glyphtools.svg
        :target: https://pypi.python.org/pypi/glyphtools

.. image:: https://img.shields.io/travis/simoncozens/glyphtools.svg
        :target: https://travis-ci.com/simoncozens/glyphtools

.. image:: https://readthedocs.org/projects/glyphtools/badge/?version=latest
        :target: https://glyphtools.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status


Routines for extracting information from font glyphs


**glyphtools.bin_glyphs_by_metric(font, glyphs, category,
bincount=5)**

   Organise glyphs according to a given metric.

   Organises similar glyphs into a number of bins. The bins are not
   guaranteed to contain the same number of glyphs; the
   one-dimensional ckmeans clustering algorithm is used to cluster
   glyphs based on metric similarity. For example, if there are five
   glyphs of width 100, 102, 105, 210, and 220 units respectively, and
   you ask for two bins, the first bin will contain three glyphs and
   the second will contain two. This is usually what you want.

   :Parameters:
      * **font** – a ``fontTools`` TTFont object OR a ``glyphsLib`` GSFontMaster object OR a ``babelfont`` Font object.

      * **glyphs** – a collection of glyph names

      * **category** – the metric (see metric keys in
         get_glyph_metrics().)

      * **bincount** – number of bins to return

   :Returns:
      A list of ``bincount`` two-element tuples. The first element is
      a list of glyphnames in this bin; the second is the average
      metric value of the glyphs in this bin.

**glyphtools.categorize_glyph(font, glyphname)**

   Returns the category of the given glyph.

   :Parameters:
      * **font** – a ``fontTools`` TTFont object OR a ``glyphsLib`` GSFontMaster object OR a ``babelfont`` Font object.

      * **glyphname** – name of the glyph.

   :Returns:
      A two-element tuple. The first element is one of the following
      strings: ``unknown``, ``base``, ``mark``, ``ligature``,
      ``component``. If the glyph is a mark, the second element is the
      mark attachment class number.

**glyphtools.determine_kern(font, glyph1, glyph2, targetdistance,
offset1=0, 0, offset2=0, 0, maxtuck=0.4)**

   Determine a kerning value required to set two glyphs at given
   ink-to-ink distance.

   The value is bounded by the ``maxtuck`` parameter. For example, if
   ``maxtuck`` is 0.20, the right glyph will not be placed any further
   left than 80% of the width of left glyph, even if this places the
   ink further than ``targetdistance`` units away.

   :Parameters:
      * **font** – a ``fontTools`` TTFont object OR a ``glyphsLib`` GSFontMaster object  OR a ``babelfont`` Font object.

      * **glyph1** – name of the left glyph.

      * **glyph2** – name of the right glyph.

      * **targetdistance** – distance to set the glyphs apart.

      * **offset1** – offset (X-coordinate, Y-coordinate) to place
         left glyph.

      * **offset2** – offset (X-coordinate, Y-coordinate) to place
         right glyph.

      * **maxtuck** – maximum proportion of the left glyph’s width to
         kern.

   Returns: A kerning value, in units.

**glyphtools.duplicate_glyph(font, existing, new)**

   Add a new glyph to the font duplicating an existing one.

   :Parameters:
      * **font** – a ``babelfont`` Font object.

      * **existing** – name of the glyph to duplicate.

      * **new** – name of the glyph to add.

**glyphtools.get_glyph_metrics(font, glyphname)**

   Returns glyph metrics as a dictionary.

   :Parameters:
      * **font** – a ``fontTools`` TTFont object OR a ``glyphsLib`` GSFontMaster object OR a ``babelfont`` Font object.

      * **glyphname** – name of the glyph.

   :Returns:
      width: Advance width of the glyph. lsb: Left side-bearing rsb:
      Right side-bearing xMin: minimum X coordinate xMax: maximum X
      coordinate yMin: minimum Y coordinate yMax: maximum Y coordinate
      rise: difference in Y coordinate between cursive entry and exit

   :Return type:
      A dictionary with the following keys

**glyphtools.set_glyph_category(font, glyphname, category,
maClass=None)**

   Sets the category of the glyph in the font.

   :Parameters:
      * **font** – a ``fontTools`` TTFont object OR a ``glyphsLib`` GSFontMaster object OR a ``babelfont`` Font object.

      * **glyphname** – name of the glyph.

      * **category** – one of ``base``, ``mark``, ``ligature``,
         ``component``.

      * **maClass** – If the category is ``base``, the mark
         attachment class number.



* Free software: Apache Software License 2.0
* Documentation: https://glyphtools.readthedocs.io.
