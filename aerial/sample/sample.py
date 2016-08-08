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

"""aerial sample application main module."""

import sys
import signal
from argparse import ArgumentParser

from aerial.sample import utils
from aerial.sample.application import Application


# ---------------------------------------------------------------------------------------------------------------------
app = None # Global application instance


# ---------------------------------------------------------------------------------------------------------------------
def signal_handler(signal_number, stack_frame):
    """
    Handler for SIGINT (Ctrl+C) and SIGTERM (default kill) signals. Captures the mentioned signals and shuts everything
    down gracefully.
    """
    global app
    print '\x1b[2K\x1b[2D' + 'Shutting down...\n'
    if app is not None:
        app.shutdown()
    sys.exit(0)


# ---------------------------------------------------------------------------------------------------------------------
def parse_arguments():
    """
    Configures and parses command line arguments. In case of any error in the command line arguments specified by the
    user, this function responds with a brief usage help message and the description of the error.
    :return: Parsed arguments from the command line.
    """
    parser = ArgumentParser()
    parser.add_argument('server', type = str, help = 'IP address of the aerial Devkit')
    command_group = parser.add_mutually_exclusive_group(required = True)
    command_group.add_argument('-l', '--list', action = 'store_true', help = 'List current profiles and training sets')
    command_group.add_argument('-r', '--reset', action = 'store_true', help = 'Reset all profiles and remove all training sets.')
    command_group.add_argument('-t', '--train', metavar = 'profile', nargs = 1, help = 'Train the specified profile')
    command_group.add_argument('-e', '--enable', metavar = 'profile', nargs = 1, help = 'Enable the specified profile.')
    command_group.add_argument('-d', '--disable', metavar = 'profile', nargs = 1, help = 'Disable the specified profile.')
    command_group.add_argument('-dh', '--detect-home', action = 'store_true', help = 'Run home-level detection')
    command_group.add_argument('-dr', '--detect-room', action = 'store_true', help = 'Run room-level detection')
    return parser.parse_args()


# ---------------------------------------------------------------------------------------------------------------------
def main():
    """
    The main function which is the starting point for the sample application.
    """

    # Print application header
    utils.print_header('aerial Sample Application')

    # Configure signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGALRM, signal_handler)

    # Get command line arguments
    arguments = parse_arguments()

    # Create the application instance
    global app
    app = Application(arguments.server, 80)

    # Run application methods based on the arguments specified by the user

    if arguments.list:
        app.list_profiles()

    elif arguments.reset:
        app.reset()

    elif arguments.train is not None:
        profile_name = arguments.train[0]
        app.train(profile_name)

    elif arguments.enable is not None:
        profile_name = arguments.enable[0]
        app.enable(profile_name)

    elif arguments.disable is not None:
        profile_name = arguments.disable[0]
        app.disable(profile_name)

    elif arguments.detect_home:
        app.detect('home')

    elif arguments.detect_room:
        app.detect('room')

    print ''


# ---------------------------------------------------------------------------------------------------------------------
# If the script is run directly, simply run the main function.
if __name__ == '__main__':
    main()