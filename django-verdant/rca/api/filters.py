from datetime import datetime
from rest_framework import filters

from django.core.exceptions import FieldDoesNotExist
from django.db.models.fields.related import ForeignObjectRel, OneToOneRel
from rca.models import EventItemDatesTimes, EventItem

class RelatedProgrammesFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        if hasattr(queryset.model, 'related_programmes'):
            rp = request.GET.getlist('rp', [])
            if rp:
                queryset = queryset.filter(related_programmes__programme__slug__in=rp)

        if hasattr(queryset.model, 'related_programme'):
            rp = request.GET.getlist('rp', [])
            if rp:
                queryset = queryset.filter(related_programme__slug__in=rp)

        if hasattr(queryset.model, 'roles'):
            rp = request.GET.getlist('rp', [])
            if rp:
                queryset = queryset.filter(roles__programme__slug__in=rp)

        return queryset


class NegatedTagFilter(filters.BaseFilterBackend):
    # Filter for items that do no have specified tag
    def filter_queryset(self, request, queryset, view):
        if hasattr(queryset.model, 'tags'):
            tags = request.GET.getlist('tags_not', [])
            if tags:
                queryset = queryset.exclude(tags__name__in=tags)

        return queryset

class NextEventOrder(filters.OrderingFilter):
    def filter_queryset(self, request, queryset, view):
        if hasattr(queryset.model, 'dates_times'):
            date_from = request.query_params.get('event_date_from', None)
            if date_from:
                now = datetime.utcnow().date()
                queryset = queryset.filter(dates_times__date_from__gte=now) | queryset.filter(dates_times__date_to__gte=now)
                queryset = queryset.order_by('dates_times__date_from')

        return queryset


