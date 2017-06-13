from django.template.loader import select_template


def get_base_show_template(year):
    """
    Returns base template (a Template object)
    chosen dynamically based on a `year`.

    If there is no specific template for a year,
    falls back to the generic `rca_show/base.html` template.
    """
    return select_template([
        'rca_show/base_{}.html'.format(year),
        'rca_show/base.html',
    ])
