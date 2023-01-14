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
  better results. 
  
  `:warning:` OCR is a slow resource-intensive process. Hence, use the option ``-p PAGES`` to specify the pages
  that you want to apply OCR. More info at `Script options <#script-options>`_.
* `Ghostscript <https://www.ghostscript.com/>`_: **v9.53.3**, for converting *pdf* to *png*
* `DjVuLibre <http://djvu.sourceforge.net/>`_: **v3.5.27**, it includes ``ddjvu`` for 
  converting *djvu* to *tif* image, and ``djvused`` to get number of pages from a *djvu* document

**Optionally:**

- `poppler <https://poppler.freedesktop.org/>`_ which includes ``pdfinfo`` to get number of pages from 
  a *pdf* document if ``mdls`` is not found.
  
Script options
==============
To display the script's list of options and their descriptions::

 $ python ocr.py -h
 usage: python ocr.py [OPTIONS] {input_file} [{output_file}]

 General options:
   -h, --help                              Show this help message and exit.
   -v, --version                           Show program's version number and exit.
   -q, --quiet                             Enable quiet mode, i.e. nothing will be printed.
   --verbose                               Print various debugging information, e.g. print traceback when there is an exception.
   --log-level {debug,info,warning,error}  Set logging level. (default: info)
   --log-format {console,only_msg,simple}  Set logging formatter. (default: only_msg)

 OCR options:
   -p, --pages PAGES                       "Specify which pages should be processed. When this option is not specified, 
                                           the text of all pages of the documents is concatenated into the output file. 
                                           The page specification PAGES contains one or more comma-separated page ranges. 
                                           A page range is either a page number, or two page numbers separated by a dash. 
                                           For instance, specification 1-10 outputs pages 1 to 10, and specification 
                                           1,3,99999-4 outputs pages 1 and 3, followed by all the document pages in 
                                           reverse order up to page 4."
                                           Ref.: https://man.archlinux.org/man/djvutxt.1.en

 Input/Output files:
   input                                   Path of the file (pdf, djvu or image) that will be OCRed.
   output                                  Path of the output txt file. (default: output.txt)

`:information_source:` Explaining some of the options/arguments

- The option ``-p, --pages`` is taken straight from `djvutxt <https://man.archlinux.org/man/djvutxt.1.en>`_ option ``--page=pagespec``.
- ``input`` and ``output`` are positional arguments. Thus they must follow directly each other. ``output`` is not required since by
  default the output *txt* file will be saved as ``output.txt`` directly under the working directory. 

Example: convert a ``pdf`` file to ``txt``
==========================================
Let's say a ``pdf`` file is made up of images and you want to convert specific pages of said ``pdf`` 
file to ``txt``, then the following command will do the trick::

 python ocr.py -p 23-30,50,90-92 ~/Data/ocr/Book.pdf Book.txt
 
`:information_source:` Explaining the command

- ``-p 23-30,50,90-92``: specifies that pages 23 to 30, 50 and 90 to 92 from the given ``pdf`` document will be OCRed.

  `:warning:` No spaces when specifying the pages.
- ``~/Data/ocr/Book.pdf Book.txt``: these are the input and output files, respectively.

  **NOTE:** by default if no output file is specified, then the converted text will be saved as ``output.txt`` 
  directly under the working directory.

Sample output::

 Output text file already exists: Book.txt
 Starting OCR...
 OCR successful!

