from django import template


register = template.Library()


@register.filter()
def date_range_display(date_from, date_to):
    if date_to:
        if date_to.month == date_from.month:
            return ''.join([
                date_from.strftime('%d').lstrip('0'), '&ndash;', date_to.strftime('%d').lstrip('0'), # From and to days
                date_from.strftime(' %B') # Month
            ])
        else:
            return ''.join([
                date_from.strftime('%d %B').lstrip('0'), '&ndash;', date_to.strftime('%d %B').lstrip('0')
            ])
    return ' '.join([
            date_from.strftime('%A'),
            date_from.strftime('%d').lstrip('0'),
            date_from.strftime('%B')
        ])


@register.filter()
def date_display(date):
    return date_range_display(date, None)


@register.filter()
def event_date_display(event):
    return date_range_display(event.date_from, event.date_to)


@register.filter()
def event_times_display(event_datetime):
    if event_datetime.time_from:
        time_from = event_datetime.time_from.strftime('%I.%M%p').lstrip("0").replace(" 0", " ").replace(".00", "")
        if event_datetime.time_to:
            time_to = event_datetime.time_to.strftime('%I.%M%p').lstrip("0").replace(" 0", " ").replace(".00", "")
            return '&ndash;'.join([time_from, time_to]).lower()
        else:
            return time_from.lower()

    return event_datetime.time_other.lower()


@register.filter()
def event_location_display(event_datetime):
    event = event_datetime.page

    # NB: events with a location "other" are excluded from signage completely

    location = []

    if event.gallery:
        location.append(event.get_gallery_display())

    if event.location_other:
        location.append(event.location_other)   

    location.append(event.get_location_display())

    return ', '.join(location)
