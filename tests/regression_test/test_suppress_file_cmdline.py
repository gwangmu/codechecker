#
# -----------------------------------------------------------------------------
#                     The CodeChecker Infrastructure
#   This file is distributed under the University of Illinois Open Source
#   License. See LICENSE.TXT for details.
# -----------------------------------------------------------------------------

import json
import os
import random
import re
import unittest

from codeCheckerDBAccess.ttypes import *

from test_helper.thrift_client_to_db import CCViewerHelper

from test_helper.testlog import info
from test_helper.testlog import debug


class RunResults(unittest.TestCase):

    _ccClient = None

    # selected runid for running the tests
    _runid = None

    def setUp(self):
        host = 'localhost'
        port = int(os.environ['CC_TEST_VIEWER_PORT'])
        uri = '/'
        self._testproject_data = json.loads(os.environ['CC_TEST_PROJECT_INFO'])
        self.assertIsNotNone(self._testproject_data)

        self._cc_client = CCViewerHelper(host, port, uri)

    # -----------------------------------------------------
    def test_suppress_file_set_in_cmd(self):
        # test server is started without a temporary
        # suppress file
        self.assertEquals(self._cc_client.getSuppressFile(),
                          '/tmp/test_suppress_file')
