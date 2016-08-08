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

"""aerial sample application setup script."""


from setuptools import setup, find_packages


# ---------------------------------------------------------------------------------------------------------------------

setup(

    name                = 'aerial-sample',
    version             = '1.0.0',
    author              = 'aerial.ai',
    namespace_packages  = ['aerial'],
    packages            = find_packages(),

    package_data        = {
        'aerial': ['aerial.config']
    },

    install_requires    = ['termcolor', 'tornado', 'python-dateutil'],

    entry_points        = {
        'console_scripts': ['aerial-sample = aerial.sample.sample:main']
    }

)