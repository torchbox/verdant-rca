"""Provides the {% navigation_via_api %} template tag.

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
from django import template
from django.core.cache import cache


register = template.Library()

logger = logging.getLogger("verdant-rca")


class CantPullFromRcaApi(Exception):
    pass


def parse_navigation(data):
    # Temporarily in place should we need to do any further parsing of the data
    return data


def pull_navigation_data():
    """Pull the navigation data from the api.

    Raises:
        CantPullFromRcaApi: Failed to pull from the RCA api

    Returns:
        A dict of all the navigation data from the new rebuild site API passed
        through a parser
    """
    try:
        response = requests.get(
            url="{}api/v3/navigation/1/".format(
                settings.NAVIGATION_API_CONTENT_BASE_URL
            ),
            auth=HTTPBasicAuth(settings.BASIC_AUTH_LOGIN, settings.BASIC_AUTH_PASSWORD),
        )
        response.raise_for_status()
        logger.info("Pulling Navigation data from API")
    except (requests.exceptions.HTTPError, AttributeError) as e:
        error_text = "Error occured when fetching navigation data {}".format(e)
        logger.error(error_text)
        raise CantPullFromRcaApi(error_text)
    else:
        data = response.json()
        nav_data = parse_navigation(data)

    return nav_data


def get_navigation_data():
    """Check if the navigation data is in the cache, otherwise pull it and set
    a cache key.

    Returns:
        A dict containing all the navigation data through a cache check
    """
    cache_key = "navigation_from_api"
    navigation_data = cache.get(cache_key)
    if navigation_data is None:
        try:
            navigation_data = pull_navigation_data()
        except CantPullFromRcaApi:
            return []
        else:
            cache.set(cache_key, navigation_data, settings.NAVIGATION_API_CACHE_TIMEOUT)
    return navigation_data


@register.simple_tag
def navigation_via_api():
    """Template tag to render the navigation from the new site via the API.

    Returns:
        A dict of all the navigation data from the new rebuild site API
    """
    nav = get_navigation_data()
    return nav
