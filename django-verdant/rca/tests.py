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
from rca.models import HomePage

class TestNavigationFetch(TestCase):

    @mock.patch("rca.navigation.requests.get")
    def test_data_if_timeout(self, mock_get):
        """ If a timeout is caught the should be an empty list"""
        mock_get.side_effect = Timeout
        nav = Navigation().get_navigation_data()
        self.assertEqual(nav, [])

    @mock.patch("rca.navigation.requests.get")
    def test_page_renders_with_timeout(self, mock_get):
        """ If there is a timeout for the get request when the page loads,
        ensure the page still renders with the empty data so it doesn't bork the page"""
        home_page = HomePage.objects.first()
        mock_get.side_effect = Timeout
        response = self.client.get(home_page.path)
        self.assertTemplateUsed(response, "home/home_page.html")
        self.assertEqual(response.render().status_code, 200)
