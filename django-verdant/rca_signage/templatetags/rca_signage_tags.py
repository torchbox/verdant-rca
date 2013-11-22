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
                ' '.join([
                    date_from.strftime('%d').lstrip('0'),
                    date_from.strftime('%B')
                ]),
                '&ndash;',
                ' '.join([
                    date_to.strftime('%d').lstrip('0'),
                    date_to.strftime('%B')
                ]),
            ])
    return date_from.strftime('%A %d %B')


@register.filter()
def date_display(date):
    return date_range_display(date, None)


@register.filter()
def event_date_display(event):
    return date_range_display(event.date_from, event.date_to)


@register.filter()
def event_times_display(event_datetime):
    if event_datetime.time_from:
        time_from = event_datetime.time_from.strftime('%H.%M')
        if event_datetime.time_to:
            time_to = event_datetime.time_to.strftime('%H.%M')
            return '&ndash;'.join([time_from, time_to])
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
        location.insert(0, event.get_gallery_display())

    return ', '.join(location)
