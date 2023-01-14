import ast
import logging
import mimetypes
import os
import re
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger('ocr_lib')
logger.setLevel(logging.CRITICAL + 1)


# =====================
# Default config values
# =====================

# OCR options
# ===========
OCR_PAGES = None
OCR_COMMAND = 'tesseract_wrapper'


class Result:
    def __init__(self, stdout='', stderr='', returncode=None, args=None):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.args = args

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f'stdout={str(self.stdout).strip()}, ' \
               f'stderr={str(self.stderr).strip()}, ' \
               f'returncode={self.returncode}, args={self.args}'


# ------
# Colors
# ------
COLORS = {
    'GREEN': '\033[0;36m',  # 32
    'RED': '\033[0;31m',
    'YELLOW': '\033[0;33m',  # 32
    'BLUE': '\033[0;34m',  #
    'VIOLET': '\033[0;35m',  #
    'BOLD': '\033[1m',
    'NC': '\033[0m',
}
_COLOR_TO_CODE = {
    'g': COLORS['GREEN'],
    'r': COLORS['RED'],
    'y': COLORS['YELLOW'],
    'b': COLORS['BLUE'],
    'v': COLORS['VIOLET'],
    'bold': COLORS['BOLD']
}


def color(msg, msg_color='y', bold_msg=False):
    msg_color = msg_color.lower()
    colors = list(_COLOR_TO_CODE.keys())
    assert msg_color in colors, f'Wrong color: {msg_color}. Only these ' \
                                f'colors are supported: {msg_color}'
    msg = bold(msg) if bold_msg else msg
    msg = msg.replace(COLORS['NC'], COLORS['NC']+_COLOR_TO_CODE[msg_color])
    return f"{_COLOR_TO_CODE[msg_color]}{msg}{COLORS['NC']}"


def blue(msg):
    return color(msg, 'b')


def bold(msg):
    return color(msg, 'bold')


def green(msg):
    return color(msg, 'g')


def red(msg):
    return color(msg, 'r')


def violet(msg):
    return color(msg, 'v')


def yellow(msg):
    return color(msg)


# Ref.: https://stackoverflow.com/a/28909933
def command_exists(cmd):
    return shutil.which(cmd) is not None


def convert_result_from_shell_cmd(old_result):
    new_result = Result()

    for attr_name, new_val in new_result.__dict__.items():
        old_val = getattr(old_result, attr_name)
        if old_val is None:
            shell_args = getattr(old_result, 'args', None)
            # logger.debug(f'result.{attr_name} is None. Shell args: {shell_args}')
        else:
            if isinstance(new_val, str):
                try:
                    new_val = old_val.decode('UTF-8')
                except (AttributeError, UnicodeDecodeError) as e:
                    if type(e) == UnicodeDecodeError:
                        # old_val = b'...'
                        new_val = old_val.decode('unicode_escape')
                    else:
                        # `old_val` already a string
                        # logger.debug('Error decoding old value: {}'.format(old_val))
                        # logger.debug(e.__repr__())
                        # logger.debug('Value already a string. No decoding necessary')
                        new_val = old_val
                try:
                    new_val = ast.literal_eval(new_val)
                except (SyntaxError, ValueError) as e:
                    # NOTE: ValueError might happen if value consists of [A-Za-z]
                    # logger.debug('Error evaluating the value: {}'.format(old_val))
                    # logger.debug(e.__repr__())
                    # logger.debug('Aborting evaluation of string. Will consider
                    # the string as it is')
                    pass
            else:
                new_val = old_val
        setattr(new_result, attr_name, new_val)
    return new_result


def convert(input_file, output_file=None,
            ocr_command=OCR_COMMAND,
            ocr_pages=OCR_PAGES,
            **kwargs):
    func_params = locals().copy()
    file_hash = None
    mime_type = get_mime_type(input_file)
    if mime_type == 'text/plain':
        logger.warning(yellow('The file is already in .txt'))
        # Return text if no output file was specified
        if output_file is None:
            with open(input_file, 'r') as f:
                text = f.read()
            return text
        else:
            return 0
    return_txt = False
    # Create temp output file if output file not specified by user
    if output_file is None:
        return_txt = True
        output_file = tempfile.mkstemp(suffix='.txt')[1]
    else:
        output_file = Path(output_file)
        # Check first that the output text file is valid
        if output_file.suffix != '.txt':
            logger.error(red("The output file needs to have a .txt extension!"))
            return 1
        # Create output file text if it doesn't exist
        if output_file.exists():
            logger.warning(f"{yellow('Output text file already exists:')} {output_file.name}")
            logger.debug(f"Full path of output text file: '{output_file.absolute()}'")
        else:
            # Create output text file
            touch(output_file)
    func_params['mime_type'] = mime_type
    func_params['output_file'] = output_file
    logger.info("Starting OCR...")
    if ocr_file(input_file, output_file, mime_type, ocr_command, ocr_pages):
        logger.error(f'{red("OCR failed!")}')
        return 1
    else:
        logger.debug("ocr_file() returned 0")
    # Check conversion
    logger.debug('Checking converted text...')
    if isalnum_in_file(output_file):
        logger.debug("Converted text is valid!")
    else:
        logger.error(red("Conversion failed!"))
        logger.error(red(f'The converted txt with size {os.stat(output_file).st_size} '
                         'bytes does not seem to contain text'))
        # Only remove output file if it is a temp file (i.e. return_txt = True)
        if return_txt:
            remove_file(output_file)
        return 1
    logger.info(blue("OCR successful!"))
    # Only remove output file if it is a temp file (i.e. return_txt = True)
    if return_txt:
        with open(output_file, 'r', encoding="utf8", errors='ignore') as f:
            text = f.read()
        assert text
        remove_file(output_file)
        return text
    else:
        return 0


# Using Python built-in module mimetypes
def get_mime_type(file_path):
    return mimetypes.guess_type(file_path)[0]


# Return number of pages in a djvu document
def get_pages_in_djvu(file_path):
    cmd = f'djvused -e "n" "{file_path}"'
    args = shlex.split(cmd)
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return convert_result_from_shell_cmd(result)


# Return number of pages in a pdf document
def get_pages_in_pdf(file_path, cmd='mdls'):
    assert cmd in ['mdls', 'pdfinfo']
    if command_exists(cmd) and cmd == 'mdls':
        cmd = f'mdls -raw -name kMDItemNumberOfPages "{file_path}"'
        args = shlex.split(cmd)
        result = subprocess.run(args, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        if '(null)' in str(result.stdout):
            return get_pages_in_pdf(file_path, cmd='pdfinfo')
    else:
        cmd = f'pdfinfo "{file_path}"'
        args = shlex.split(cmd)
        result = subprocess.run(args, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        if result.returncode == 0:
            result = convert_result_from_shell_cmd(result)
            result.stdout = int(re.findall('^Pages:\s+([0-9]+)',
                                           result.stdout,
                                           flags=re.MULTILINE)[0])
            return result
    return convert_result_from_shell_cmd(result)


def isalnum_in_file(file_path):
    with open(file_path, 'r', encoding="utf8", errors='ignore') as f:
        isalnum = False
        for line in f:
            for ch in line:
                if ch.isalnum():
                    isalnum = True
                    break
            if isalnum:
                break
    return isalnum


# OCR on a pdf, djvu document or image
# NOTE: If pdf or djvu document, then first needs to be converted to image and then OCR
def ocr_file(file_path, output_file, mime_type,
             ocr_command=OCR_COMMAND,
             ocr_pages=OCR_PAGES, **kwargs):
    # Convert pdf to png image
    def convert_pdf_page(page, input_file, output_file):
        cmd = f'gs -dSAFER -q -r300 -dFirstPage={page} -dLastPage={page} ' \
              '-dNOPAUSE -dINTERPOLATE -sDEVICE=png16m ' \
              f'-sOutputFile="{output_file}" "{input_file}" -c quit'
        args = shlex.split(cmd)
        result = subprocess.run(args, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        return convert_result_from_shell_cmd(result)

    # Convert djvu to tif image
    def convert_djvu_page(page, input_file, output_file):
        cmd = f'ddjvu -page={page} -format=tif "{input_file}" "{output_file}"'
        args = shlex.split(cmd)
        result = subprocess.run(args, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        return convert_result_from_shell_cmd(result)

    if mime_type.startswith('application/pdf'):
        result = get_pages_in_pdf(file_path)
        num_pages = result.stdout
        logger.debug(f"Result of '{get_pages_in_pdf.__name__}()' on '{file_path}':\n{result}")
        page_convert_cmd = convert_pdf_page
    elif mime_type.startswith('image/vnd.djvu'):
        result = get_pages_in_djvu(file_path)
        num_pages = result.stdout
        logger.debug(f"Result of '{get_pages_in_djvu.__name__}()' on '{file_path}':\n{result}")
        page_convert_cmd = convert_djvu_page
    elif mime_type.startswith('image/'):
        logger.debug(f"Running OCR on file '{file_path}' and with mime type '{mime_type}'...")
        if ocr_command in globals():
            result = eval(f'{ocr_command}("{file_path}", "{output_file}")')
            logger.debug(f"Result of '{ocr_command}':\n{result}")
            return 0
        else:
            msg = red("Function '{ocr_command}' doesn't exit.")
            logger.error(f'{msg}')
            return 1
    else:
        logger.error(f"{red('Unsupported mime type')} '{mime_type}'!")
        return 1

    if result.returncode == 1:
        err_msg = result.stdout if result.stdout else result.stderr
        msg = "Couldn't get number of pages:"
        logger.error(f"{red(msg)} '{str(err_msg).strip()}'")
        return 1

    if ocr_command not in globals():
        msg = red("Function '{ocr_command}' doesn't exit.")
        logger.error(f'{msg}')
        return 1

    logger.debug(f"The file '{file_path}' has {num_pages} page{'s' if num_pages > 1 else ''}")
    logger.debug(f'mime type: {mime_type}')

    # Pre-compute the list of pages to process based on ocr_pages
    if ocr_pages:
        pages_to_process = []
        for p in ocr_pages.split(','):
            if '-' in p:
                p1, p2 = p.split('-')
                p1 = int(p1)
                p2 = int(p2)
                if p1 > p2:
                    pages = sorted(range(p2, p1 + 1), reverse=True)
                else:
                    pages = sorted(range(p1, p2 + 1))
                pages_to_process.extend(pages)
            else:
                pages_to_process.append(int(p))
    else:
        logger.warning(f"{yellow('OCR will be applied to all ({pages}) pages of the document')}")
        pages_to_process = [i for i in range(1, num_pages+1)]
    logger.debug(f'Pages to process: {pages_to_process}')

    text = ''
    for i, page in enumerate(pages_to_process, start=1):
        logger.debug(f'Processing page {i} of {len(pages_to_process)}')
        # Make temporary files
        tmp_file = tempfile.mkstemp()[1]
        tmp_file_txt = tempfile.mkstemp(suffix='.txt')[1]
        logger.debug(f'Running OCR of page {page}...')
        logger.debug(f'Using tmp files {tmp_file} and {tmp_file_txt}')
        # doc(pdf, djvu) --> image(png, tiff)
        result = page_convert_cmd(page, file_path, tmp_file)
        if result.returncode == 0:
            logger.debug(f"Result of {page_convert_cmd.__name__}():\n{result}")
            # image --> text
            logger.debug(f"Running the '{ocr_command}'...")
            result = eval(f'{ocr_command}("{tmp_file}", "{tmp_file_txt}")')
            if result.returncode == 0:
                logger.debug(f"Result of '{ocr_command}':\n{result}")
                with open(tmp_file_txt, 'r') as f:
                    data = f.read()
                    # logger.debug(f"Text content of page {page}:\n{data}")
                text += data
            else:
                msg = red(f"Document couldn't be converted to image: {result}")
                logger.error(f'{msg}')
                logger.error(f'Skipping current page ({page})')
        else:
            msg = red(f"Image couldn't be converted to text: {result}")
            logger.error(f'{msg}')
            logger.error(f'Skipping current page ({page})')
        # Remove temporary files
        logger.debug('Cleaning up tmp files')
        remove_file(tmp_file)
        remove_file(tmp_file_txt)
    # Everything on the stdout must be copied to the output file
    logger.debug('Saving the text content')
    with open(output_file, 'w') as f:
        f.write(text)
    return 0


def remove_file(file_path):
    # Ref.: https://stackoverflow.com/a/42641792
    try:
        os.remove(file_path)
        return 0
    except OSError as e:
        logger.error(red(f'{e.filename} - {e.strerror}.'))
        return 1


# OCR: convert image to text
def tesseract_wrapper(input_file, output_file):
    cmd = f'tesseract "{input_file}" stdout --psm 12'
    args = shlex.split(cmd)
    result = subprocess.run(args,
                            stdout=open(output_file, 'w'),
                            stderr=subprocess.PIPE,
                            encoding='utf-8',
                            bufsize=4096)
    return convert_result_from_shell_cmd(result)


def touch(path, mode=0o666, exist_ok=True):
    logger.debug(f"Creating file: '{path}'")
    Path(path).touch(mode, exist_ok)
    logger.debug("File created!")
