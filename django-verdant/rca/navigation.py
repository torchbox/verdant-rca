"""Provides the navigation data by requesting it from the new API.

The new rebuild site is where the menu is being managed and updated.
Instead of copying and pasting rendered html when the new site's menu gets
updated, this template tag will request navigation data from the new site's
navigation API endpoint. Instead of making this API call on every page request
it's stored in cache['navigation_from_api'].

"""


import logging
import requests
from requests.auth import HTTPBasicAuth

from django.conf import settings
from django.core.cache import cache



class CantPullFromRcaApi(Exception):
    pass


class Navigation(object):
    def __init__(self, *args):
        self.logger = logging.getLogger("verdant-rca")


    def fetch_navigation_data(self):
        """Fetch the navigation data from the api.

        Raises:
            CantPullFromRcaApi: Failed to pull from the RCA api

        Returns:
            A dict of all the navigation data from the new rebuild site API passed
            through a parser
        """
        try:
            response = requests.get(
                url="{}api/v3/navigation/1/".format(
                    settings.NAVIGATION_API_CONTENT_BASE_URL, timeout=10
                ),
                auth=HTTPBasicAuth(settings.BASIC_AUTH_LOGIN, settings.BASIC_AUTH_PASSWORD),
            )
            response.raise_for_status()
            self.logger.info("Pulling Navigation data from API")
        except (requests.exceptions.HTTPError, AttributeError) as e:
            error_text = "Error occured when fetching navigation data {}".format(e)
            self.logger.error(error_text)
            raise CantPullFromRcaApi(error_text)
        else:
            data = response.json()
        return data


    def get_navigation_data(self):
        """Check if the navigation data is in the cache, otherwise pull it and set
        a cache key.

        Returns:
            A list containing all the navigation data through a cache check
        """
        cache_key = "navigation_from_api"
        navigation_data = cache.get(cache_key)
        if navigation_data is None:
            try:
                navigation_data = self.pull_navigation_data()
            except CantPullFromRcaApi:
                return []
            else:
                cache.set(cache_key, navigation_data, settings.NAVIGATION_API_CACHE_TIMEOUT)
        return navigation_data


    def get_primary_navigation(self):
        """Retrive just the primary navigation data.

        Returns:
            list
        """
        nav_data = self.get_navigation_data()
        return nav_data['primary_navigation'] if 'primary_navigation' in nav_data else []

    def get_quick_links(self):
        """Retrive just the quick links from navigation data.

        Returns:
            dict
        """
        nav_data = self.get_navigation_data()
        return nav_data['quick_links'] if 'quick_links' in nav_data else []

    def get_footer_links(self):
        """Retrive just the footer links from navigation data.

        Returns:
            dict
        """
        nav_data = self.get_navigation_data()
        return nav_data['footer_links'] if 'footer_links' in nav_data else []

    def get_footer_navigation(self):
        """Retrive just the footer navigation from navigation data.

        Returns:
            dict
        """
        nav_data = self.get_navigation_data()
        return nav_data['footer_navigation'] if 'footer_navigation' in nav_data else []
