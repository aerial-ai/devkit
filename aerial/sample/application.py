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

"""Core application code."""


import signal
import socket

from concurrent.futures import ThreadPoolExecutor

from aerial.sample import utils
from aerial.sample.api_wrapper import ApiWrapper, AerialException


# ---------------------------------------------------------------------------------------------------------------------
def handle_api_errors(function):
    """
    Decorator for catching and pretty-printing standard aerial API errors thrown from the backend methods.
    """
    def wrapper(*args, **kwargs):
        try:
            function(*args, **kwargs)
        except AerialException as api_error:
            utils.print_api_error(api_error)
        except socket.error as socket_error:
            utils.print_api_error(AerialException('socket_error', '{0}.'.format(socket_error.strerror)))
    return wrapper


# ---------------------------------------------------------------------------------------------------------------------
class Application:
    """
    Main application class which forms the functionality of the app using the API facade (the "backend" module).
    Methods in this class are designed to be self-contained: They each contain a specific part of the application's
    functionality and do not return anything.
    """

    # -----------------------------------------------------------------------------------------------------------------
    def __init__(self, server, port):
        self.api_wrapper = ApiWrapper(server, port)
        self.executor = ThreadPoolExecutor(max_workers = 2)
        self.detection_thread = None

    # -----------------------------------------------------------------------------------------------------------------
    @handle_api_errors
    def list_profiles(self):
        """
        Retrieves and pretty-prints a list of all profiles with their training sets.
        """
        result = self.api_wrapper.list_profiles()
        for p in result:
            utils.print_profile(p)

    # -----------------------------------------------------------------------------------------------------------------
    @handle_api_errors
    def reset(self):
        """
        Resets all profiles and removes all of their training sets.
        """
        self.api_wrapper.reset()
        print 'All profiles are reset.'

    # -----------------------------------------------------------------------------------------------------------------
    @handle_api_errors
    def train(self, profile_name):
        """
        Creates a training set for the specified profile. Shows a timer and interacts with the server in the
        background. Once the recording is finished and the training set is successfully added to the profile, its date
        is printed in the console.
        :param profile_name: The name of the profile for which the training set is to be recorded.
        """
        utils.print_delay(5)
        task = self.executor.submit(self.api_wrapper.train, profile_name)
        utils.print_timer(45, task)
        if task.result() is not None:
            date = task.result()['date']
            print 'Training set added for profile "{0}" [{1}].'.format(profile_name, utils.format_datetime(date))

    # -----------------------------------------------------------------------------------------------------------------
    @handle_api_errors
    def enable(self, profile_name):
        """
        Enables a profile specified by its name.
        :param profile_name: The name of the profile to be enabled.
        """
        self.api_wrapper.change_status(profile_name, True)
        print 'Profile {0} is enabled.'.format(profile_name)

    # -----------------------------------------------------------------------------------------------------------------
    @handle_api_errors
    def disable(self, profile_name):
        """
        Disables a profile specified by its name.
        :param profile_name: The name of the profile to be disabled.
        """
        self.api_wrapper.change_status(profile_name, False)
        print 'Profile {0} is disabled.'.format(profile_name)

    # -----------------------------------------------------------------------------------------------------------------
    @handle_api_errors
    def detect(self, mode):
        """
        Initializes the system for the specified detection mode, runs a loop to receive detection results from the
        server, and gives the control to the signal handler to stop the loop once a keyboard interrupt or a termination
        signal is received from the user or the operating system.
        :param mode: A string with the value of 'home' or 'room' that respectively indicates home-level or room-level
                     detection.
        """

        # Initialize the system
        print 'Initializing...\n'
        init_result = self.api_wrapper.initialize(mode)

        # Verify the initialization response
        if init_result.get('profiles', None) is None:
            raise AerialException('unknown_error', 'Unexpected response received from server during initialization.')

        # Print a message, showing the detection expiry time if returned by the server
        if mode == 'room' and init_result.get('expiry', None) is not None:
            expiry_date = utils.format_datetime(init_result['expiry'], utils.DATETIME_FORMAT_TIME)
            print 'Detection is about to begin and expires at {0}. Press Ctrl+C to stop.\n'.format(expiry_date)
        else:
            print 'Detection is about to begin. Press Ctrl+C to stop.\n'

        # Start the detection loop and wait for a keyboard interrupt or a termination signal to stop
        self.detection_thread = self.api_wrapper.detect(utils.print_detection)
        signal.pause()

    # -----------------------------------------------------------------------------------------------------------------
    def shutdown(self):
        """
        Gracefully stops the detection loop and other long-running background tasks, if any. This method is typically
        called by a signal handler.
        """
        self.api_wrapper.stop()
        self.executor.shutdown(wait = False)
        if self.detection_thread is not None:
            self.detection_thread.join(3)