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

"""Wrapper for aerial REST API and detection websocket."""


import json
import urllib
import signal
from threading import Thread

from tornado import gen, websocket
from tornado.httpclient import HTTPClient, HTTPError
from tornado.ioloop import IOLoop


# ---------------------------------------------------------------------------------------------------------------------
class AerialException(Exception):
    """
    Wrapper class for errors that may either be returned from the API or created by the application code.
    """

    # -----------------------------------------------------------------------------------------------------------------
    def __init__(self, type, message):
        self.type = type
        self.message = message


# ---------------------------------------------------------------------------------------------------------------------
class ApiWrapper:
    """
    This class encapsulates the DevKit API client code and provides convenient methods for interacting with the API.
    Methods in this class parse the API JSON responses into dictionaries and return them. In case the API returns an
    errors, it is wrapped inside an AerialException instance and raised. All of the methods in this class will block
    until a response is received from the API.
    """

    # -----------------------------------------------------------------------------------------------------------------
    def __init__(self, server, port):
        self.server = server
        self.port = port
        self.client = HTTPClient()
        self.__stop_detection = False

    # -----------------------------------------------------------------------------------------------------------------
    def list_profiles(self):
        """
        Retrieves and returns a list of all profiles and their training sets by sending a GET request.
        :return: A list of dictionaries, each representing a profile and its training sets.
        """
        return self.__http_request('/profiles/')

    # -----------------------------------------------------------------------------------------------------------------
    def reset(self):
        """
        Sends a DELETE request to the API to reset all the profiles.
        """
        self.__http_request('/profiles/', method = 'DELETE')

    # -----------------------------------------------------------------------------------------------------------------
    def train(self, profile_name):
        """
        Sends a long-running POST request to the API to add a training set for the specified profile.
        :param profile_name: The name of the profile for which a new training set should be recorded.
        :return: A dictionary representing the newly added training set.
        """
        return self.__http_request('/profiles/{0}/training-sets/'.format(profile_name),
                                   method ='POST', body = None, request_timeout = 60)

    # -----------------------------------------------------------------------------------------------------------------
    def change_status(self, profile_name, enabled):
        """
        Changes the enabled status of the specified profile.
        :param profile_name: The name of the profile to be enabled / disabled.
        :param enabled: A boolean indicating the desired enabled status of the profile.
        """
        modifications = { 'enabled': enabled }
        return self.__http_request('/profiles/{0}'.format(profile_name),
                                   method = 'PUT', body = json.dumps(modifications))

    # -----------------------------------------------------------------------------------------------------------------
    def initialize(self, mode):
        return self.__http_request('/initialization/{}'.format(mode),
                                   method = 'POST', body = None, request_timeout = 300)

    # -----------------------------------------------------------------------------------------------------------------
    def detect(self, listener):
        """
        Initializes the DevKit for detection by sending a POST request and establishes the web socket connection,
        waiting for detection results to be received from the server and passing them to a specified callback function.
        :param listener: The callback function which is called with the detection result as the sole argument every
        time it is received from the DevKit.
        :return: The thread on which the web socket loop is run. The thread is not supposed to be explicitly stopped,
        but only joined to make sure the detection loop is stopped. See the stop() method.
        """

        # Define the co-routine to be synchronously run on the event loop.
        @gen.coroutine
        def __connect():

            # Form the websocket URL and connect to it
            url = 'ws://{0}:{1}/api/detection'.format(self.server, self.port)
            socket = yield websocket.websocket_connect(url)

            # The loop which waits for a response (a web socket message), a stop signal, or a break in the connection
            while not self.__stop_detection:
                # Obtain a potential message (a "future") from the server and wait for something to happen
                message_future = socket.read_message()
                while True:
                    # If the socket is unexpectedly closed, send an alarm to shutdown
                    if message_future.done() and message_future.result() is None :
                        self.__stop_detection = True
                        print '\nConnection with aerial Devkit lost.\n'
                        signal.alarm(1) # send SIGALRM to shutdown via our signal handler;
                        break;
                    # If a stop signal is received, simply break out
                    if self.__stop_detection :
                        break
                    # If a response is received, parse it and call the callback function
                    elif message_future.done():
                        detection_result = json.loads(message_future.result())
                        listener(detection_result)
                        break
                    # Otherwise, check again in half a second
                    yield gen.sleep(0.5)

            # After the loop is finished, close the socket.
            if socket is not None:
                socket.close()

        # Create the thread to run the event loop, start it, and return it
        loop_thread = Thread(target = lambda: IOLoop.current().run_sync(__connect))
        loop_thread.start()
        return loop_thread

    # -----------------------------------------------------------------------------------------------------------------
    def stop(self):
        """
        If the detection loop is already started, sends it a stop signal. This method returns immediately, typically
        before the loop is actually stopped.
        """
        self.__stop_detection = True

    # -----------------------------------------------------------------------------------------------------------------
    def __http_request(self, url, method = 'GET', body = None, request_timeout = 30):
        """
        Sends an HTTP request, while parsing JSON responses into dictionaries and wrapping aerial API errors in
        AerialException instances.
        :return: The parsed response.
        """

        # Encode and prepare the request URL
        url = urllib.quote(url)
        full_url = 'http://{0}:{1}/api{2}'.format(self.server, self.port, url)

        # Fix missing 'body' in POST and PUT requests
        if method in ['POST', 'PUT'] and body is None:
            body = ''

        # Try to send the request
        try:
            response = self.client.fetch(full_url, method = method, body = body, request_timeout = request_timeout)
        except HTTPError as error:
            # In case the response indicates an error, try to transform it into an AerialException instance. Fails if
            # the error response is not a standard aerial API error.
            try:
                aerial_error = json.loads(error.response.body)['error']
                error = AerialException(aerial_error['type'], aerial_error['message'])
            finally:
                # Nevertheless, wrapped or not, raise the HTTP error.
                raise error
        else:
            # If everything went smoothly, try to parse the JSON response and return the result.
            if response.body is not None and response.body != '':
                try:
                    return json.loads(response.body)
                except ValueError:
                    # If the response is not a JSON document, something unexpected has happened. Raise an appropriate
                    # exception.
                    raise AerialException('malformed_response',
                                          'An unexpected response has been received from the server.')
