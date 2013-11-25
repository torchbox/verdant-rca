from lxml import etree as ET
from rca.models import NewsItem, RcaImage, NewsIndex, NewsItemCarouselItem
from django.utils.dateparse import parse_date
from django.core.files import File
from importer.import_utils import richtext_from_elem, text_from_elem, make_slug, check_length
import datetime
import urllib2
from bs4 import BeautifulSoup


PATH = 'importer/export_news_pretty.xml'
IMAGE_PATH = 'importer/export_news_images/'
NEWS_INDEX = NewsIndex.objects.get(slug='master-news-index')


def clear_news_items():
    newsindex=NEWS_INDEX
    pages = newsindex.get_children()
    print str(pages.count()) + ' news items to be deleted'
    for page in pages:
        newsitem = NewsItem.objects.get(id=page.id)
        for c in NewsItemCarouselItem.objects.filter(page=newsitem):
            if c.image:
                c.image.delete()
        soup = BeautifulSoup(newsitem.body, 'html.parser')
        to_delete_ids = []
        for x in soup.find_all('embed'):
            try:
                to_delete_ids.append(int(x.attrs['id']))
            except ValueError:
                pass
        if to_delete_ids:
            RcaImage.objects.filter(id__in=to_delete_ids).delete()
        page.delete()


def doimport(**kwargs):
    path = kwargs.get('path', PATH)
    save = kwargs.get('save', False)
    image_path = kwargs.get('image_path', IMAGE_PATH)
    ruthless = kwargs.get('ruthless', False)
    newsindex = NEWS_INDEX
    tree = ET.parse(path)
    root = tree.getroot()
    errors = []
    images_errors = []
    for item in root.findall('news_item'):
        itemerrors = {}

        # sort out what instance this is
        news_contentid = item.attrib['contentid']
        title, itemerrors['title'] = text_from_elem(item, 'title', length=255)
        date = parse_date(item.find('goinglivedate').text.strip().replace('.','-')) or datetime.date.today()
        try:
            newsitem = NewsItem.objects.get(rca_content_id=news_contentid)
        except NewsItem.DoesNotExist:
            newsitem = NewsItem(rca_content_id=news_contentid)
        newsitem.title = title
        newsitem.date = date
        newsitem.intro = richtext_from_elem(item.find('intro'))
        newsitem.slug = make_slug(newsitem)

        # possibly delete any images that are embedded in the existing body
        if ruthless:
            soup = BeautifulSoup(newsitem.body, 'html.parser')
            to_delete_ids = []
            for x in soup.find_all('embed'):
                try:
                    to_delete_ids.append(int(x.attrs['id']))
                except ValueError:
                    pass
            if to_delete_ids:
                RcaImage.objects.filter(id__in=to_delete_ids).delete()

        # build the body
        strings = []
        if item.find('texts'):
            for elem in item.find('texts').findall('text'):
                html = richtext_from_elem(elem.find('content'))
                strings.append(html)
        newsitem.body = '\n'.join(strings)

        # save newsitem
        if save:
            if newsitem.id:
                newsitem.save()
            else:
                newsindex.add_child(newsitem)

        tobesaved = False
        if item.find('images') is not None:
            # first delete images that haven't got a contentid
            if ruthless:
                for c in NewsItemCarouselItem.objects.filter(page=newsitem):
                    c.image.delete()
                    c.delete()

            for image in item.find('images').findall('image'):
                imageerrors = {}
                metadata = image.find('imagemetadata')
                im_contentid = image.attrib['contentid']
                filename = urllib2.unquote(image.find('filename').text.strip())
                try:
                    theimage = RcaImage.objects.get(rca_content_id=im_contentid)
                except RcaImage.DoesNotExist:
                    theimage = RcaImage(rca_content_id=im_contentid)

                theimage.title, imageerrors['title'] = text_from_elem(metadata, 'title', length=255, textify=True)
                theimage.creator, imageerrors['creator'] = text_from_elem(metadata, 'creator', length=255, textify=True)
                theimage.medium, imageerrors['medium'] = text_from_elem(metadata, 'media', length=255, textify=True)
                theimage.photographer, imageerrors['photog'] = text_from_elem(metadata, 'photographer', length=255, textify=True)
                theimage.permission, imageerrors['perms'] = text_from_elem(metadata, 'rights', length=255, textify=True)

                caption, imageerrors['caption'] = text_from_elem(metadata, 'caption', length=255, textify=True)
                theimage.alt = caption

                #theimage.width, imageerrors['width'] = text_from_elem(metadata, 'width', length=255)
                #theimage.height, imageerrors['height'] = text_from_elem(metadata, 'height', length=255)

                try:
                    with File(open(image_path + filename.encode('utf-8'), 'r')) as f:
                        if theimage.id:
                            if save:
                                theimage.delete()
                        theimage.file = f
                        if save:
                            theimage.save()
                except IOError as e:
                    print "I/O error({0}): {1}".format(e.errno, e.strerror)
                    print repr(filename)
                except ValueError:
                    print "Could not convert data to an integer."
                except:
                    import sys
                    print "Unexpected error:", sys.exc_info()[0]
                    raise

                if save and theimage.is_landscape():
                    try:
                        carousel = NewsItemCarouselItem.objects.get(
                                page = newsitem,
                                image = theimage,
                                )
                    except NewsItemCarouselItem.DoesNotExist:
                        carousel = NewsItemCarouselItem(
                                page = newsitem,
                                image = theimage,
                                )
                        if save:
                            carousel.save()
                elif save and theimage.id:
                    imagestring = '<embed alt="%(alt)s" embedtype="image" format="right" id="%(id)s"/>' % {
                            'alt': theimage.alt,
                            'id': theimage.id,
                            }
                    newsitem.body = imagestring + newsitem.body
                    tobesaved = True

                imageerrordict = dict((k, v) for k, v in imageerrors.iteritems() if v)
                if imageerrordict:
                    images_errors.append({image: imageerrordict})
        if tobesaved and save:
            newsitem.save()

        errordict = dict((k, v) for k, v in itemerrors.iteritems() if v)
        if errordict:
            errors.append({item: errordict})
    return errors, images_errors
