import os
import sys
import traceback

from six.moves import input

import coloredlogs, logging

from ScoutSuite import ERRORS_LIST

########################################
# Output configuration
########################################

verbose_exceptions = False
logger = logging.getLogger('scout')

def set_config_debug_level(is_debug):
    """
    Configure whether full stacktraces should be dumped in the console output
    """
    global verbose_exceptions
    verbose_exceptions = is_debug
    coloredlogs.install(level='DEBUG' if is_debug else 'INFO', logger=logger)


########################################
# Output functions
########################################

def print_generic(msg):
    logger.info(msg)


def print_debug(msg):
    logger.debug(msg)


def print_error(msg):
    logger.error(msg)


def print_exception(exception, additional_details=None):

    try:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        file_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        line_number = exc_tb.tb_lineno
        traceback_exc = traceback.format_exc()
        str = '{} L{}: {}'.format(file_name, line_number, exception)
    except Exception as e:
        file_name = None
        line_number = None
        traceback_exc = None
        str = '{}'.format(exception)

    global verbose_exceptions
    if verbose_exceptions:
        logger.exception(str)
    else:
        logger.error(str)

    ERRORS_LIST.append({'file': file_name,
                        'line': line_number,
                        'exception': '{}'.format(exception),
                        'traceback': '{}'.format(traceback_exc),
                        'additional_details': additional_details})


def print_info(msg):

    print_generic(msg)


########################################
# Prompt functions
########################################

def prompt(test_input=None):
    """
    Prompt function that works for Python2 and Python3

    :param test_input:                  Value to be returned when testing

    :return:                            Value typed by user (or passed in argument when testing)
    """
    if test_input is not None:
        if type(test_input) == list and len(test_input):
            choice = test_input.pop(0)
        elif type(test_input) == list:
            choice = ''
        else:
            choice = test_input
    else:
        choice = input()
    return choice


def prompt_overwrite(filename, force_write, test_input=None):
    """
    Prompt whether the file should be overwritten

    :param filename:                    Name of the file about to be written
    :param force_write:                 Skip confirmation prompt if this flag is set
    :param test_input:                       Used for unit testing

    :return:                            Boolean whether file write operation is allowed
    """
    if not os.path.exists(filename) or force_write:
        return True
    return prompt_yes_no('File \'{}\' already exists. Do you want to overwrite it'.format(filename),
                         test_input=test_input)


def prompt_value(question, choices=None, default=None, display_choices=True, display_indices=False,
                 authorize_list=False, is_question=False, no_confirm=False, required=True,
                 regex=None,
                 regex_format='', max_laps=5, test_input=None, return_index=False):
    """
    Prompt for a value
                                        .                    .
    :param return_index:
    :param question:                    Question to be asked
    :param choices:                     List of authorized answers
    :param default:                     Value suggested by default
    :param display_choices:             Display accepted choices
    :param display_indices:             Display the indice in the list next to the choice
    :param authorize_list:              Set to true if a list of answers may be accepted
    :param is_question:                 Set to true to append a question mark
    :param no_confirm:                  Set to true to not prompt for a confirmation of the value
    :param required:                    Set to false if an empty answer is authorized
    :param regex:                       TODO
    :param regex_format                 TODO
    :param max_laps:                    Exit after N laps
    :param test_input:                  Used for unit testing
    :param return_index                 TODO

    :return:
    """
    int_choice = 0

    if choices and display_choices and not display_indices:
        question = question + ' (' + '/'.join(choices) + ')'
    lap_n = 0
    while True:
        if lap_n >= max_laps:
            print_error('Automatically aborting prompt loop after 5 failures')
            return None
        lap_n += 1
        can_return = False
        # Display the question, choices, and prompt for the answer
        if is_question:
            question = question + '? '
        print_error(question)
        if choices and display_indices:
            for c in choices:
                print_error('%3d. %s' % (choices.index(c), c))
            print_error('Enter the number corresponding to your choice: ', False)
        choice = prompt(test_input)
        # Set the default value if empty choice
        if not choice or choice == '':
            if default:
                if no_confirm or prompt_yes_no('Use the default value (' + default + ')'):
                    # return default
                    choice = default
                    can_return = True
            elif not required:
                can_return = True
            else:
                print_error('Error: you cannot leave this parameter empty.')
        # Validate the value against a whitelist of choices
        elif choices:
            user_choices = [item.strip() for item in choice.split(',')]
            if not authorize_list and len(user_choices) > 1:
                print_error(
                    'Error: multiple values are not supported; please enter a single value.')
            else:
                choice_valid = True
                if display_indices and int(choice) < len(choices):
                    int_choice = choice
                    choice = choices[int(choice)]
                else:
                    for c in user_choices:
                        if c not in choices:
                            print_error('Invalid value (%s).' % c)
                            choice_valid = False
                            break
                if choice_valid:
                    can_return = True
        # Validate against a regex
        elif regex:
            if regex.match(choice):
                # return choice
                can_return = True
            else:
                print_error('Error: expected format is: %s' % regex_format)
        else:
            # No automated validation, can attempt to return
            can_return = True
        if can_return:
            # Manually confirm that the entered value is correct if needed
            if no_confirm or prompt_yes_no('You entered "' + choice + '". Is that correct',
                                           test_input=test_input):
                return int(int_choice) if return_index else choice


def prompt_yes_no(question, test_input=None):
    """
    Prompt for a yes/no or y/n answer
                                        .
    :param question:                    Question to be asked
    :param test_input:                  Used for unit testing

    :return:                            True for yes/y, False for no/n
    """
    count = 0
    while True:
        print_error(question + ' (y/n)? ')
        choice = prompt(test_input).lower()
        if choice == 'yes' or choice == 'y':
            return True
        elif choice == 'no' or choice == 'n':
            return False
        else:
            count += 1
            print_error('\'%s\' is not a valid answer. Enter \'yes\'(y) or \'no\'(n).' % choice)
            if count > 3:
                return None
