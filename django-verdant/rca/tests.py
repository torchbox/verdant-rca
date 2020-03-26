import datetime
import json
import logging
import warnings
import mock

import requests
from django.conf import settings
from django.test import TestCase
from requests.exceptions import Timeout
from rca.navigation import Navigation


class TestNavigationFetch(TestCase):

    @mock.patch("rca.navigation.requests.get")
    def test_data_if_timeout(self, mock_get):
        """ If a timeout is caught the should be an empty list"""
        mock_get.side_effect = Timeout
        nav = Navigation().fetch_navigation_data()
        self.assertEqual(nav, [])
