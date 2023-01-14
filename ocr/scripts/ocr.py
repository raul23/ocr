#!/usr/bin/env python
import argparse
import logging
import os

from lib import convert, blue, green, red, yellow, OCR_PAGES
from ocr import __version__
# __version__ = '0.1.0'

# import ipdb

logger = logging.getLogger('ocr_script')
logger.setLevel(logging.CRITICAL + 1)

# =====================
# Default config values
# =====================

# Misc options
# ============
QUIET = False
OUTPUT_FILE = 'output.txt'

# Logging options
# ===============
LOGGING_FORMATTER = 'only_msg'
LOGGING_LEVEL = 'info'


class ArgumentParser(argparse.ArgumentParser):

    def error(self, message):
        print_(self.format_usage().splitlines()[0])
        self.exit(2, red(f'\nerror: {message}\n'))


class MyFormatter(argparse.HelpFormatter):
    """
    Corrected _max_action_length for the indenting of subactions
    """

    def add_argument(self, action):
        if action.help is not argparse.SUPPRESS:

            # find all invocations
            get_invocation = self._format_action_invocation
            invocations = [get_invocation(action)]
            current_indent = self._current_indent
            for subaction in self._iter_indented_subactions(action):
                # compensate for the indent that will be added
                indent_chg = self._current_indent - current_indent
                added_indent = 'x' * indent_chg
                invocations.append(added_indent + get_invocation(subaction))
            # print_('inv', invocations)

            # update the maximum item length
            invocation_length = max([len(s) for s in invocations])
            action_length = invocation_length + self._current_indent
            self._action_max_length = max(self._action_max_length,
                                          action_length)

            # add the item to the list
            self._add_item(self._format_action, [action])

    # Ref.: https://stackoverflow.com/a/23941599/14664104
    def _format_action_invocation(self, action):
        if not action.option_strings:
            metavar, = self._metavar_formatter(action, action.dest)(1)
            return metavar
        else:
            parts = []
            # if the Optional doesn't take a value, format is:
            #    -s, --long
            if action.nargs == 0:
                parts.extend(action.option_strings)

            # if the Optional takes a value, format is:
            #    -s ARGS, --long ARGS
            # change to
            #    -s, --long ARGS
            else:
                default = action.dest.upper()
                args_string = self._format_args(action, default)
                for option_string in action.option_strings:
                    # parts.append('%s %s' % (option_string, args_string))
                    parts.append('%s' % option_string)
                parts[-1] += ' %s'%args_string
            return ', '.join(parts)


class OptionsChecker:
    def __init__(self, add_opts, remove_opts):
        self.add_opts = init_list(add_opts)
        self.remove_opts = init_list(remove_opts)

    def check(self, opt_name):
        return not self.remove_opts.count(opt_name) or \
               self.add_opts.count(opt_name)


# General options
def add_general_options(parser, add_opts=None, remove_opts=None,
                        program_version=__version__,
                        title='General options'):
    checker = OptionsChecker(add_opts, remove_opts)
    parser_general_group = parser.add_argument_group(title=title)
    if checker.check('help'):
        parser_general_group.add_argument('-h', '--help', action='help',
                                          help='Show this help message and exit.')
    if checker.check('version'):
        parser_general_group.add_argument(
            '-v', '--version', action='version',
            version=f'%(prog)s v{program_version}',
            help="Show program's version number and exit.")
    if checker.check('quiet'):
        parser_general_group.add_argument(
            '-q', '--quiet', action='store_true',
            help='Enable quiet mode, i.e. nothing will be printed.')
    if checker.check('verbose'):
        parser_general_group.add_argument(
            '--verbose', action='store_true',
            help='Print various debugging information, e.g. print traceback '
                 'when there is an exception.')
    if checker.check('log-level'):
        parser_general_group.add_argument(
            '--log-level', dest='logging_level',
            choices=['debug', 'info', 'warning', 'error'], default=LOGGING_LEVEL,
            help='Set logging level.' + get_default_message(LOGGING_LEVEL))
    if checker.check('log-format'):
        parser_general_group.add_argument(
            '--log-format', dest='logging_formatter',
            choices=['console', 'only_msg', 'simple',], default=LOGGING_FORMATTER,
            help='Set logging formatter.' + get_default_message(LOGGING_FORMATTER))
    return parser_general_group


def get_default_message(default_value):
    return green(f' (default: {default_value})')


def init_list(list_):
    return [] if list_ is None else list_


def print_(msg):
    global QUIET
    if not QUIET:
        print(msg)


# Ref.: https://stackoverflow.com/a/4195302/14664104
def required_length(nmin, nmax, is_list=True):
    class RequiredLength(argparse.Action):
        def __call__(self, parser, args, values, option_string=None):
            if isinstance(values, str):
                tmp_values = [values]
            else:
                tmp_values = values
            if not nmin <= len(tmp_values) <= nmax:
                if nmin == nmax:
                    msg = 'argument "{f}" requires {nmin} arguments'.format(
                        f=self.dest, nmin=nmin, nmax=nmax)
                else:
                    msg = 'argument "{f}" requires between {nmin} and {nmax} ' \
                          'arguments'.format(f=self.dest, nmin=nmin, nmax=nmax)
                raise argparse.ArgumentTypeError(msg)
            setattr(args, self.dest, values)
    return RequiredLength


def setup_argparser():
    width = os.get_terminal_size().columns - 5
    name_input = 'input_file'
    name_output = 'output_file'
    usage_msg = blue(f'%(prog)s [OPTIONS] {{{name_input}}} [{{{name_output}}}]')
    end_msg = 'OCR documents (pdf, djvu or images)'
    parser = ArgumentParser(
        description="",
        usage=f"{usage_msg}\n\n{end_msg}",
        add_help=False,
        formatter_class=lambda prog: MyFormatter(
            prog, max_help_position=50, width=width))
    general_group = add_general_options(
        parser,
        remove_opts=[],
        program_version=__version__,
        title=yellow('General options'))
    # ===========
    # OCR options
    # ===========
    ocr_group = parser.add_argument_group(title=yellow('OCR options'))
    ocr_group.add_argument(
        '-p', '--pages', dest='pages', metavar='PAGES', default=OCR_PAGES,
        help=""""Specify which pages should be processed. When this option is
        not specified, the text of all pages of the documents is concatenated
        into the output file. The page specification PAGES contains one or more
        comma-separated page ranges. A page range is either a page number, or
        two page numbers separated by a dash. For instance, specification 1-10 
        outputs pages 1 to 10, and specification 1,3,99999-4 outputs pages 1
        and 3, followed by all the document pages in reverse order up to page 
        4." Ref.: https://man.archlinux.org/man/djvutxt.1.en""")
    # ==================
    # Input/output files
    # ==================
    input_output_files_group = parser.add_argument_group(
        title=yellow('Input/Output files'))
    input_output_files_group.add_argument(
        'input',
        help='Path of the file (pdf, djvu or image) that will be OCRed.')
    input_output_files_group.add_argument(
        'output', default=OUTPUT_FILE, nargs='*', action=required_length(0, 1),
        help='Path of the output txt file.'
             + get_default_message(OUTPUT_FILE))
    return parser


def setup_log(quiet=False, verbose=False, logging_level=LOGGING_LEVEL,
              logging_formatter=LOGGING_FORMATTER):
    if not quiet:
        for logger_name in ['ocr_script', 'ocr_lib']:
            logger_ = logging.getLogger(logger_name)
            if verbose:
                logger_.setLevel('DEBUG')
            else:
                logging_level = logging_level.upper()
                logger_.setLevel(logging_level)
            # Create console handler and set level
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            # Create formatter
            if logging_formatter:
                formatters = {
                    'console': '%(name)-10s | %(levelname)-8s | %(message)s',
                    # 'console': '%(asctime)s | %(levelname)-8s | %(message)s',
                    'only_msg': '%(message)s',
                    'simple': '%(levelname)-8s %(message)s',
                    'verbose': '%(asctime)s | %(name)-10s | %(levelname)-8s | %(message)s'
                }
                formatter = logging.Formatter(formatters[logging_formatter])
                # Add formatter to ch
                ch.setFormatter(formatter)
            # Add ch to logger
            logger_.addHandler(ch)
        # =============
        # Start logging
        # =============
        logger.debug("Running {} v{}".format(__file__, __version__))
        logger.debug("Verbose option {}".format("enabled" if verbose else "disabled"))


def main():
    global QUIET
    try:
        parser = setup_argparser()
        args = parser.parse_args()
        QUIET = args.quiet
        setup_log(args.quiet, args.verbose, args.logging_level, args.logging_formatter)
        # Actions
        if isinstance(args.output, list):
            output = args.output[0]
        else:
            output = args.output
        exit_code = convert(args.input, output, ocr_pages=args.pages)
    except KeyboardInterrupt:
        print_(yellow('\nProgram stopped!'))
        exit_code = 2
    except Exception as e:
        print_(yellow('Program interrupted!'))
        logger.exception(e)
        exit_code = 1
    return exit_code


if __name__ == '__main__':
    retcode = main()
    msg = f'Program exited with {retcode}'
    if retcode == 1:
        logger.error(red(f'{msg}'))
    else:
        logger.debug(msg)
