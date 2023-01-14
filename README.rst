=================================
OCR documents (pdf, djvu, images)
=================================
.. contents:: **Contents**
   :depth: 3
   :local:
   :backlinks: top

Dependencies
============
This is the environment on which the script `ocr.py <./scripts/ocr.py>`_ was tested:

* **Platform:** macOS
* **Python**: version **3.7**
* `Tesseract <https://github.com/tesseract-ocr/tesseract>`_ for running OCR on books - version 4 gives 
  better results. OCR is a slow resource-intensive process.
* `Ghostscript <https://www.ghostscript.com/>`_: **v9.53.3**, for converting *pdf* to *png*
* `DjVuLibre <http://djvu.sourceforge.net/>`_: **v3.5.27**, it includes ``ddjvu`` for 
  converting *djvu* to *tif* image, and ``djvused`` to get number of pages from a *djvu* document

**Optionally:**

- `poppler <https://poppler.freedesktop.org/>`_ which includes ``pdfinfo`` to get number of pages from 
  a *pdf* document if ``mdls`` is not found.
  
Script options
==============

Examples
========
