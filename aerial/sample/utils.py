# ---------------------------------------------------------------------------------------------------------------------
#
# Copyright (C) 2016 aerial
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# ---------------------------------------------------------------------------------------------------------------------

"""aerial sample application utility functions."""


from dateutil import parser, tz
import subprocess
import time
from termcolor import colored


DATETIME_FORMAT_FULL = 0
DATETIME_FORMAT_TIME = 1

# ---------------------------------------------------------------------------------------------------------------------
try:
    # Try to capture the width of the terminal (the number of available columns).
    terminal_width = int(subprocess.check_output(['stty', 'size']).split()[1])
except Exception:
    # If it fails for any reason, including being run on Windows, assume a default value.
    terminal_width = 60


# ---------------------------------------------------------------------------------------------------------------------
def print_profile(profile):
    """
    Pretty-prints a profile, its enabled status and its training sets in the console.
    :param profile: The profile to be pretty-printed.
    """
    if profile['enabled']:
        status = 'Enabled'
    else:
        status = 'Disabled'
    print colored('{0:15}{1:>8}'.format(profile['name'], status), 'magenta', attrs=['bold', 'underline'])
    for training_set in profile['trainingSets']:
        print format_datetime(training_set['date'])
    print ''


# ---------------------------------------------------------------------------------------------------------------------
def print_detection(detection_result):
    """
    Pretty-prints a detection result in the console.
    :param detection_result: The detection result (dictionary) to be displayed.
    """
    cursor_up_one = '\x1b[1A'
    erase_line = '\x1b[2K'
    result = detection_result['results']
    text = colored(('{:^' + str(terminal_width) + '}').format(result), None, attrs=['bold'])
    print erase_line + text + cursor_up_one


# ---------------------------------------------------------------------------------------------------------------------
def print_header(title):
    """
    Print the application header.
    :param title: Title of the application to be printed in the header.
    """
    text = ('{:^' + str(terminal_width) + '}').format(title)
    print colored(' ' * (terminal_width), None, attrs=['underline', 'dark'])
    print colored(' ' * (terminal_width), None, 'on_grey')
    print colored(text, None, 'on_grey')
    print colored(' ' * (terminal_width), None, 'on_grey', attrs=['underline', 'dark'])
    print ''


# ---------------------------------------------------------------------------------------------------------------------
def format_datetime(naive_date, format = DATETIME_FORMAT_FULL):
    """
    Formats a naive (timezone-free) UTC datetime object into a string while converting it into the local time.
    :param naive_date: The naive datetime object to be formatted.
    :param format: (Optional) The string format, one of the utils module's DATETIME_FORMAT_* constants. Assumes
                   DATETIME_FORMAT_FULL by default.
    :return: The string representing the date in the local timezone.
    """

    format_string = {
        DATETIME_FORMAT_FULL: '%Y-%m-%d  %I:%M:%S %p',
        DATETIME_FORMAT_TIME: '%I:%M:%S %p'
    }[format]

    return parser.parse(naive_date)\
        .replace(tzinfo = tz.tzutc()).astimezone(tz.tzlocal())\
        .strftime(format_string)

# ---------------------------------------------------------------------------------------------------------------------
def print_api_error(aerial_exception):
    """
    Pretty-prints an AerialException instance.
    :param aerial_exception: The instance to be printed.
    """
    error_type = aerial_exception.type.replace('_', ' ').upper()
    print colored('[' + error_type + '] ', 'red', attrs=['bold']) + aerial_exception.message


# ---------------------------------------------------------------------------------------------------------------------
def print_delay(delay):
    """
    Displays a countdown timer for recording new training sets, and blocks while the countdown is in progress.
    :param delay: Countdown duration in seconds.
    """
    def __text(step, duration):
        return 'Recording starts in {0:02d}:{1:02d}'.format(step / 60, step % 60)
    __timer(delay, __text)


# ---------------------------------------------------------------------------------------------------------------------
def print_timer(duration, task = None):
    """
    Displays a timer with a pre-defined duration. This method accepts an optional "task" argument which should be a
    Future instance representing the background task to be finished. If the task is finished at any point in time, the
    timer is not displayed anymore. This function blocks while the timer is being displayed.
    :param duration: Duration of the timer.
    :param task: The Future instance representing the background task.
    """
    def __text(step, duration):
        width = terminal_width - 18
        progress = float(duration - step) / duration
        filled_width = int(round(progress * width))
        full = colored(' ', None, 'on_white') * filled_width
        empty = colored(' ', None, 'on_grey') * (width - filled_width)
        return 'Recording {2}{3} {0:02d}:{1:02d}'.format(step / 60, step % 60, full, empty)
    __timer(duration, __text, task)


# ---------------------------------------------------------------------------------------------------------------------
def __timer(duration, text_generator, task = None):
    """
    Displays a timer in the console and blocks while it's running.
    :param duration: Total duration for the timer.
    :param text_generator: The function that generates the custom timer display text.
    :param task: (Optional) A future which represents the background task. If specified, this function returns when the
                 task is finished or the specified duration has passed, whichever happens first.
    """

    cursor_up_one = '\x1b[1A'
    erase_line = '\x1b[2K'

    # The countdown loop
    for step in range(duration, 0, -1):
        print erase_line + text_generator(step, duration)
        time.sleep(1)
        print cursor_up_one + cursor_up_one
        if task is not None and not task.running():
            break

    # Cleanup
    print erase_line + cursor_up_one