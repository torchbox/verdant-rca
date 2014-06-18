import random
from django import template
from rca_show import models
from rca import models as rca_models, utils as rca_utils

register = template.Library()


@register.simple_tag
def get_school_display(school):
    return "HELLO"