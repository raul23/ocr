=================================
OCR documents (pdf, djvu, images)
=================================
The script `ocr.py <./ocr/scripts/ocr.py>`_ applies optical character recognition (OCR) to documents (pdf, djvu, images).
It is based on the great `ebook-tools <https://github.com/na--/ebook-tools>`_ which is written in Shell by 
`na-- <https://github.com/na-->`_.

.. contents:: **Contents**
   :depth: 3
   :local:
   :backlinks: top

Dependencies
============
This is the environment on which the script `ocr.py <./ocr/scripts/ocr.py>`_ was tested:

* **Platform:** macOS
* **Python**: version **3.7**
* `Tesseract <https://github.com/tesseract-ocr/tesseract>`_ for running OCR on books - version 4 gives 
  better results. 
  
  `:warning:` OCR is a slow resource-intensive process. Hence, use the option ``-p PAGES`` to specify the pages
  that you want to apply OCR. More info at `Script options <#script-options>`_.
* `Ghostscript <https://www.ghostscript.com/>`_: ``gs`` converts *pdf* to *png*
* `DjVuLibre <http://djvu.sourceforge.net/>`_: it includes ``ddjvu`` for 
  converting *djvu* to *tif* image, and ``djvused`` to get number of pages from a *djvu* document
  
  `:warning:` To access the *djvu* command line utilities and their documentation,
   you must set the shell variable ``PATH`` and ``MANPATH`` appropriately. This can
   be achieved by invoking a convenient shell script hidden inside the
   application bundle::
   
    $ eval `/Applications/DjView.app/Contents/setpath.sh`
   
   Ref.: ReadMe from DjVuLibre

**Optionally:**

- `poppler <https://poppler.freedesktop.org/>`_ which includes ``pdfinfo`` to get number of pages from 
  a *pdf* document if `mdls <https://ss64.com/osx/mdls.html>`_ is not found.

Installation
============
To install the `ocr <./ocr/>`_ package::

 $ pip install git+https://github.com/raul23/ocr#egg=ocr
 
**Test installation**

1. Test your installation by importing ``ocr`` and printing its
   version::

   $ python -c "import ocr; print(ocr.__version__)"

2. You can also test that you have access to the ``ocr.py`` script by
   showing the program's version::

   $ ocr --version

Uninstall
=========
To uninstall the `ocr <./ocr/>`_ package::

 $ pip uninstall ocr

Script options
==============
To display the script `ocr.py <./ocr/scripts/ocr.py>`_ list of options and their descriptions::

 $ ocr -h
 usage: ocr [OPTIONS] {input_file} [{output_file}]

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

  Of course, if the given document is an image (e.g. *image.png*), then the option ``-p`` is ignored.

  `:warning:` If the option ``-p`` is not used, then by default all pages from the given document will be OCRed!
- ``input`` and ``output`` are positional arguments. Thus they must follow directly each other. ``output`` is not required since by
  default the output *txt* file will be saved as ``output.txt`` directly under the working directory.
  
  `:warning:` ``output`` needs to have a *.txt* extension!

How OCR is applied
==================
Here are the important steps that the script `ocr.py <./ocr/scripts/ocr.py>`_ follows when applying OCR to a given document:

1. If the given document is already in *.txt*, then no need to go further!
2. If it is an image, then OCR is applied directly through the ``tesseract`` command.
3. If it is neither a *djvu* nor a *pdf* file, OCR is abruptly ended with an error.
4. The specifc pages to be OCRed are computed from the option ``-p, --pages PAGES``.
5. For each page from the given document:

   i. Convert the page (*djvu* or *pdf*) to an image (*png* or *tif*) through the command ``gs`` (for *pdf*) or ``ddjvu`` (for *djvu*)
   ii. Convert the image to *txt* through the ``tesseract`` command
   iii. Concatenate the *txt* page with the rest of the converted *txt* pages
6. Save all the converted *txt* pages to the output file.
7. The output *txt* file is checked if it actually contains text. If it doesn't, the user is warned that OCR failed.

Example: convert a ``pdf`` file to ``txt``
==========================================
Through the script ``ocr.py``
-----------------------------
Let's say a *pdf* file is made up of images and you want to convert specific pages of said *pdf*
file to *txt*, then the following command will do the trick::

 ocr -p 23-30,50,90-92 ~/Data/ocr/Book.pdf Book.txt
 
`:information_source:` Explaining the command

- ``-p 23-30,50,90-92``: specifies that pages 23 to 30, 50 and 90 to 92 from the given *pdf* document will be OCRed.

  `:warning:` No spaces when specifying the pages.
- ``~/Data/ocr/Book.pdf Book.txt``: these are the input and output files, respectively.

  **NOTE:** by default if no output file is specified, then the resultant text will be saved as ``output.txt`` 
  directly under the working directory.

Sample output::

 Output text file already exists: Book.txt
 Starting OCR...
 OCR successful!

Through the API
---------------
To convert a *pdf* file to *txt* using the API:

.. code-block:: python

   from ocr.lib import convert
   
   txt = convert('/Users/test/Data/ocr/B.pdf', ocr_pages='10-12')
   # Do something with `txt`

`:information_source:` Explaining the snippet of code

- ``convert(input_file, output_file=None, ocr_command=OCR_COMMAND, ocr_pages=OCR_PAGES)``:

  By default ``output_file`` is None and hence ``convert()`` will return the text from the conversion. 
  If you set ``output_file`` to for example **output.txt**, then ``convert()`` will just return a status code
  (1 for error and 0 for success) and will write the text from the conversion to **output.txt**.
- The variable ``txt`` will contain the text from the conversion.

By default when using the API, the loggers are disabled. If you want to enable them, use the
function ``setup_log()`` at the beginning of your code before the conversion:

.. code-block:: python

   from ocr.lib import convert, setup_log
   
   setup_log(logging_level='INFO')
   txt = convert('/Users/test/Data/ocr/B.pdf', ocr_pages='10-12')
   # Do something with `txt`
   
Sample output::

 Starting OCR...
 OCR successful!
