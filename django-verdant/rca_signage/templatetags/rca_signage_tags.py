from django import template


register = template.Library()


@register.filter()
def date_display(date):
    return date.strftime('%A %d %B')


@register.filter()
def event_times_display(event_datetime):
    if event_datetime.time_from:
        time_from = event_datetime.time_from.strftime('%H.%M')
        if event_datetime.time_to:
            time_to = event_datetime.time_to.strftime('%H.%M')
            return ' &ndash; '.join([time_from, time_to])
        else:
            return time_from

    return event_datetime.time_other


@register.filter()
def event_location_display(event_datetime):
    event = event_datetime.page

    if event.location == 'other':
        return event.location_other

    location = [event.get_location_display()]

    if event.location_other:
        location.append(event.location_other)

    if event.gallery:
        location.insert(0, event.gallery)

    return ', '.join(location)
