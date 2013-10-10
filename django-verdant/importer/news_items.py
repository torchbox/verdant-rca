from lxml import etree as ET
from rca.models import NewsItem, RcaImage, NewsIndex, NewsItemCarouselItem
from django.utils.dateparse import parse_date
from django.core.files import File
from importer.import_utils import richtext_from_elem, text_from_elem, make_slug, check_length
import datetime
import urllib2


PATH = 'importer/export_news_pretty.xml'
IMAGE_PATH = 'importer/export_news_images/'


def doimport(path=PATH, image_path=IMAGE_PATH):
    tree = ET.parse(path)
    root = tree.getroot()
    errors = []
    images_errors = []
    try:
        newsindex = NewsIndex.objects.get(slug='master-news-index')
    except NewsIndex.DoesNotExist:
        return "Create newsindex with slug: 'master-news-index'"
    for item in root.findall('news_item'):
        itemerrors = {}
        newsitem = NewsItem()

        newsitem.title, itemerrors['title'] = text_from_elem(item, 'title', length=255)
        newsitem.intro = richtext_from_elem(item.find('intro'))

        newsitem.date = parse_date(item.find('goinglivedate').text.strip().replace('.','-')) or datetime.date.today()
        
        newsitem.slug = make_slug(newsitem)

        strings = []
        if item.find('texts'):
            for elem in item.find('texts').findall('text'):
                html = richtext_from_elem(elem.find('content'))
                strings.append(html)
        newsitem.body = '\n'.join(strings)
        if '&nbsp_' in newsitem.body:
            import pdb; pdb.set_trace()

        # save newsitem
        newsindex.add_child(newsitem)
        if item.find('images') is not None:
            tobesaved = False
            for image in item.find('images').findall('image'):
                imageerrors = {}
                metadata = image.find('imagemetadata')
                newimage = RcaImage()
                newimage.title, imageerrors['title'] = text_from_elem(metadata, 'title', length=255, textify=True)
                newimage.creator, imageerrors['creator'] = text_from_elem(metadata, 'creator', length=255, textify=True)
                newimage.medium, imageerrors['medium'] = text_from_elem(metadata, 'media', length=255, textify=True)
                newimage.photographer, imageerrors['photog'] = text_from_elem(metadata, 'photographer', length=255, textify=True)
                newimage.permission, imageerrors['perms'] = text_from_elem(metadata, 'rights', length=255, textify=True)

                caption, imageerrors['caption'] = text_from_elem(metadata, 'caption', length=255, textify=True)
                newimage.alt = caption
                if '<em>' in newimage.title:
                    import pdb; pdb.set_trace()
                    print newimage.title
                if '<em>' in caption:
                    import pdb; pdb.set_trace()
                    print caption

                #newimage.width, imageerrors['width'] = text_from_elem(metadata, 'width', length=255)
                #newimage.height, imageerrors['height'] = text_from_elem(metadata, 'height', length=255)

                filename = urllib2.unquote(image.find('filename').text.strip())
                with File(open(image_path + filename, 'r')) as f:
                    newimage.file = f
                    newimage.save()

                if newimage.is_landscape():
                    carousel = NewsItemCarouselItem(
                            page = newsitem,
                            image = newimage,
                            # don't print the image caption as overlay
                            #overlay_text = caption,
                            )
                    carousel.save()
                else:
                    imagestring = '<embed alt="%(alt)s" embedtype="image" format="right" id="%(id)s"/>' % {
                            'alt': newimage.alt,
                            'id': newimage.id,
                            }
                    newsitem.body = imagestring + newsitem.body
                    tobesaved = True

                imageerrordict = dict((k, v) for k, v in imageerrors.iteritems() if v)
                if imageerrordict:
                    images_errors.append({image: imageerrordict})
            if tobesaved:
                newsitem.save()

        errordict = dict((k, v) for k, v in itemerrors.iteritems() if v)
        if errordict:
            errors.append({item: errordict})
    return errors, images_errors
