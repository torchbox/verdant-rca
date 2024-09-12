# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

def migrate_area_content_types(apps, schema_editor):
    """
    Migration described there:
    https://projects.torchbox.com/projects/rca-django-cms-project/tickets/872#update-43627825
    """
    School = apps.get_model('taxonomy.School')
    Programme = apps.get_model('taxonomy.Programme')
    Area = apps.get_model('taxonomy.Area')

    EventItem = apps.get_model('rca', 'EventItem')
    EventItemRelatedArea = apps.get_model('rca', 'EventItemRelatedArea')
    JobPage = apps.get_model('rca', 'JobPage')
    NewsItem = apps.get_model('rca', 'NewsItem')
    NewsItemArea = apps.get_model('rca', 'NewsItemArea')
    StaffPage = apps.get_model('rca', 'StaffPage')
    StaffPageRole = apps.get_model('rca', 'StaffPageRole')
    PressReleaseArea = apps.get_model('rca', 'PressReleaseArea')
    RcaBlogPageArea = apps.get_model('rca', 'RcaBlogPageArea')
    RcaNowPage = apps.get_model('rca', 'RcaNowPage')
    RcaNowPageArea = apps.get_model('rca', 'RcaNowPageArea')
    ResearchInnovationPage = apps.get_model('rca', 'ResearchInnovationPage')
    StandardPage = apps.get_model('rca', 'StandardPage')
    StandardIndex = apps.get_model('rca', 'StandardIndex')

    StandardStreamPage = apps.get_model('standard_stream_page', 'StandardStreamPage')


    SCHOOL_OF_ARTS_AND_HUMANITIES_SLUG = 'school-of-arts-and-humanities'
    SCHOOL_OF_MATERIAL_SLUG = 'schoolofmaterial'
    SCHOOL_OF_HUMANITIES_SLUG = 'schoolofhumanities'
    SCHOOL_OF_FINE_ART_SLUG = 'schooloffineart'
    SCHOOL_OF_DESIGN_SLUG = 'schoolofdesign'


    ################################################################
    # Skip models that have no existing association
    # with the areas we want to migrate.
    ################################################################

    # skipping StandardPage
    standard_page_areas = StandardPage.objects.filter(related_area__slug__contains='school').values_list('related_area__slug', flat=True)

    for area_slug in (SCHOOL_OF_HUMANITIES_SLUG, SCHOOL_OF_FINE_ART_SLUG, SCHOOL_OF_MATERIAL_SLUG):
        assert area_slug not in standard_page_areas, "{} found in StandardPage.related_area".format(area_slug)

    # Skipping StandardStreamPage
    assert not StandardStreamPage.objects.filter(related_area__slug__contains='school').values_list('related_area__slug', flat=True), "StandardStreamPage.related_area contains school area(s)"

    # skipping StandardIndex
    assert not StandardIndex.objects.filter(staff_feed_source__isnull=False).values_list('staff_feed_source', flat=True), "StandardIndex.staff_feed_source is not null"

    # Skipping StandardIndex.news_carousel.area
    assert not StandardIndex.objects.filter(news_carousel_area__slug__contains='school').values_list('news_carousel_area__slug', flat=True), "StandardIndex.news_carousel_area contains school area(s)"

    # Skipping StandardIndex.events_feed_area
    standard_index_events_feed_areas = StandardIndex.objects.filter(events_feed_area__slug__contains='school').values_list('events_feed_area__slug', flat=True)

    for area_slug in (SCHOOL_OF_HUMANITIES_SLUG, SCHOOL_OF_FINE_ART_SLUG, SCHOOL_OF_MATERIAL_SLUG):
        assert area_slug not in standard_index_events_feed_areas, "{} found in StandardIndex.events_feed_area".format(area_slug)

    # skipping JobPage.area
    assert not JobPage.objects.filter(area__slug__contains='school').values_list('area__slug', flat=True), "JobPage.area contains school area(s)"

    # Skipping ResearchInnovationPage.news_carousel_area
    assert not ResearchInnovationPage.objects.filter(news_carousel_area__slug__contains='school').values_list('news_carousel_area__slug', flat=True), "ResearchInnovationPage.news_carousel_area contains school area(s)"

    # skipping PressRelease.area
    assert not PressReleaseArea.objects.filter(area__slug__contains='school').values_list('area__slug', flat=True), "PressReleaseArea.area contains school area(s)"

    # skipping RcaBlogPage.area
    assert not RcaBlogPageArea.objects.filter(area__slug__contains='school').values_list('area__slug', flat=True), "RcaBlogPageArea.area contains school area(s)"


    ################################################################
    # Create School of Arts & Humanities and transfer
    # School of Humanities and School of Fine Art into it
    #################################################################

    area_of_arts_and_humanities, _ = Area.objects.get_or_create(
        slug=SCHOOL_OF_ARTS_AND_HUMANITIES_SLUG,
        display_name='School of Arts & Humanities')

    # M2M models
    for ct in [NewsItemArea, EventItemRelatedArea, StaffPageRole, RcaNowPageArea]:
        for related_area in ct.objects.filter(area__slug__in=[SCHOOL_OF_HUMANITIES_SLUG, SCHOOL_OF_FINE_ART_SLUG]):
            related_area.area = area_of_arts_and_humanities
            related_area.save()
            page = related_area.page
            page.save()

    # Models with single area
    for ct in [EventItem, StaffPage]:
        for obj in ct.objects.filter(area__slug__in=[SCHOOL_OF_HUMANITIES_SLUG, SCHOOL_OF_FINE_ART_SLUG]):
            obj.area = area_of_arts_and_humanities
            obj.save(update_fields=['area'])


    ################################################################
    # Update entries with School of Material association.
    # It's updated into two different schools based on programme.
    ################################################################

    area_of_design = Area.objects.get(slug=SCHOOL_OF_DESIGN_SLUG)

    programmes_and_areas = [
        (['ceramicsglass', 'jewelleryandmetal'], area_of_arts_and_humanities),
        (['textiles', 'fashionmenswear', 'fashionwomenswear'], area_of_design),
    ]

    for (programmes, new_area) in programmes_and_areas:
        # print("\n\nHas some of these programmes: %s -> new area: %s" % (programmes, new_area.display_name))

        # NewsItem.areas, NewsItem.related_programmes - NewsItemArea
        # print("\n\nUpdating - NewsItem.areas, NewsItem.related_programmes - NewsItemArea:")
        for news_item_area in NewsItemArea.objects.filter(area__slug=SCHOOL_OF_MATERIAL_SLUG, page__related_programmes__programme__slug__in=programmes).distinct():
            assert news_item_area.area.slug == SCHOOL_OF_MATERIAL_SLUG, "wrong slug {}, expected {}".format(news_item_area.area.slug, SCHOOL_OF_MATERIAL_SLUG)

            # print "\tUpdated {} (#{}) ({} -> {})".format(news_item_area.page.title, news_item_area.page_id, news_item_area.area.slug, new_area.slug)

            news_item_area.area = new_area
            news_item_area.save(update_fields=['area'])
            news_item_area.page.save()

        # EventItem.area
        # print("\n\nUpdating - EventItem.area:")
        for event_item in EventItem.objects.filter(area__slug=SCHOOL_OF_MATERIAL_SLUG, related_programmes__programme__slug__in=programmes):
            assert event_item.area.slug == SCHOOL_OF_MATERIAL_SLUG, "wrong slug {}, expected {}".format(event_item.area.slug, SCHOOL_OF_MATERIAL_SLUG)

            # print "\tUpdated {} (#{}) ({} -> {})".format(event_item.title, event_item.id, event_item.area.slug, new_area.slug)

            event_item.area = new_area
            event_item.save(update_fields=['area'])


        # EventItem.related_areas, EventItem.related_programmes (through EventItemArea)
        # print("\n\nUpdating - EventItem.related_areas, EventItem.related_programmes (through EventItemArea):")
        for event_item_area in EventItemRelatedArea.objects.filter(area__slug=SCHOOL_OF_MATERIAL_SLUG, page__related_programmes__programme__slug__in=programmes).distinct():
            assert event_item_area.area.slug == SCHOOL_OF_MATERIAL_SLUG, "wrong slug {}, expected {}".format(event_item_area.area.slug, SCHOOL_OF_MATERIAL_SLUG)

            # print("\tUpdated {} (#{}) ({} -> {})".format(event_item_area.page.title, event_item_area.page_id, event_item_area.area.slug, new_area.slug))

            event_item_area.area = new_area
            event_item_area.save(update_fields=['area'])
            event_item_area.page.save()

        # RcaNowPage.areas, RcaNowPage.programme (through RcaNowPageArea)
        # print("\n\nUpdating - RcaNowPage.areas, RcaNowPage.programme (through RcaNowPageArea):")
        for rca_now_area in RcaNowPageArea.objects.filter(area__slug=SCHOOL_OF_MATERIAL_SLUG, page__programme__slug__in=programmes).distinct():
            assert rca_now_area.area.slug == SCHOOL_OF_MATERIAL_SLUG, "wrong slug {}, expected {}".format(rca_now_area.area.slug, SCHOOL_OF_MATERIAL_SLUG)

            # print("\tUpdated {} (#{}) ({} -> {})".format(rca_now_area.page.title, rca_now_area.page_id, rca_now_area.area.slug, new_area.slug))

            rca_now_area.area = new_area
            rca_now_area.save(update_fields=['area'])
            rca_now_area.page.save()

        # StaffPageRole.area, StaffPageRole.programme
        # print("\n\nUpdating - StaffPageRole.area, StaffPageRole.programme:")
        for staff_role in StaffPageRole.objects.filter(area__slug=SCHOOL_OF_MATERIAL_SLUG, programme__slug__in=programmes).distinct():
            assert staff_role.area.slug == SCHOOL_OF_MATERIAL_SLUG, "wrong slug {}, expected {}".format(staff_role.area.slug, SCHOOL_OF_MATERIAL_SLUG)

            # print("\tUpdated {} (#{}) ({} -> {})".format(staff_role.page.title, staff_role.page_id, staff_role.area.slug, new_area.slug))

            staff_role.area = new_area
            staff_role.save(update_fields=['area'])

        # StaffPage.area
        # print("\n\nUpdating - StaffPage.area")
        for staff in StaffPage.objects.filter(area__slug=SCHOOL_OF_MATERIAL_SLUG, roles__programme__slug__in=programmes).distinct():
            assert staff.area.slug == SCHOOL_OF_MATERIAL_SLUG, "wrong slug {}, expected {}".format(staff_role.area.slug, SCHOOL_OF_MATERIAL_SLUG)

            # print("\tUpdated {} (#{}) ({} -> {})".format(staff.title, staff.id, staff.area.slug, new_area.slug))

            staff.area = new_area
            staff.save(update_fields=['area'])


    ################################################################related_area
    # List all the pages that are left with school of material
    # association, they usually just don't have any programme
    # associated with them and have to be changed manually.
    ################################################################

    news_item_areas = NewsItemArea.objects.filter(area__slug=SCHOOL_OF_MATERIAL_SLUG)

    if news_item_areas.exists():
        print("\n\nThere are still school of material entries in NewsItemArea:")

        for area in news_item_areas:
            print('\t{0} (#{1}) - https://rca.ac.uk/admin/pages/{1}/edit/'.format(area.page.title, area.page_id))


    event_item_areas = EventItemRelatedArea.objects.filter(area__slug=SCHOOL_OF_MATERIAL_SLUG)

    if event_item_areas.exists():
        print("\n\nThere are still school of material entries in EventItemRelatedArea:")

        for area in event_item_areas:
            print('\t{0} (#{1}) - https://rca.ac.uk/admin/pages/{1}/edit/'.format(area.page.title, area.page_id))

    event_items = EventItem.objects.filter(area__slug=SCHOOL_OF_MATERIAL_SLUG)

    if event_items.exists():
        print("\n\nThere are still school of material entries in EventItem:")

        for event_item in event_items:
            print('\t{0} (#{1}) - https://rca.ac.uk/admin/pages/{1}/edit/'.format(event_item.title, event_item.id))


    rca_now_pages_areas = RcaNowPageArea.objects.filter(area__slug=SCHOOL_OF_MATERIAL_SLUG)

    if rca_now_pages_areas.exists():
        print("\n\nThere are still school of material entries in RcaNowPageArea:")

        for area in rca_now_pages_areas:
            print('\t{0} (#{1}) - https://rca.ac.uk/admin/pages/{1}/edit/'.format(area.page.title, area.page_id))

    staff_roles = StaffPageRole.objects.filter(area__slug=SCHOOL_OF_MATERIAL_SLUG)

    if staff_roles.exists():
        print("\n\nThere are still school of material entries in StaffPageRole:")

        for staff_role in staff_roles:
            print('\t{0} (#{1}) - https://rca.ac.uk/admin/pages/{1}/edit/'.format(staff_role.page.title, staff_role.page_id))

    staff_pages = StaffPage.objects.filter(area__slug=SCHOOL_OF_MATERIAL_SLUG)

    if staff_pages.exists():
        print("\n\nThere are still school of material entries in StaffPage:")

        for staff in staff_pages:
            print('\t{0} (#{1}) - https://rca.ac.uk/admin/pages/{1}/edit/'.format(staff.title, staff.id))


class Migration(migrations.Migration):
    dependencies = [
        ('rca', '0086_schoolpageresearchlinks_allow_to_add_external_links'),
        ('standard_stream_page', '0001_initial'),
        ('taxonomy', '0021_auto_20170629_1622'),
    ]

    operations = [
        migrations.RunPython(migrate_area_content_types, lambda: None),
    ]
