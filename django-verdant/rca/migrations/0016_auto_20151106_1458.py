# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import wagtail.wagtailcore.fields


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0015_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newstudentpage',
            name='ma_specialism',
            field=models.CharField(blank=True, help_text=b'Only complete for Fashion (Knitwear; Accessories, Footwear and Millinery) Textiles (Knit; Mixed-media; Print, Weave) or Fine Art (Performance; Moving Image)', max_length=255, verbose_name=b'Specialism', choices=[(b'ads1', b'ADS1'), (b'ads2', b'ADS2'), (b'ads3', b'ADS3'), (b'ads4', b'ADS4'), (b'ads5', b'ADS5'), (b'ads6', b'ADS6'), (b'ads7', b'ADS7'), (b'ads9', b'ADS9'), (b'knit', b'Knit'), (b'mixed media', b'Mixed media'), (b'print', b'Print'), (b'weave', b'Weave'), (b'performance', b'Performance'), (b'movingimage', b'Moving Image'), (b'platform13', b'Platform 13'), (b'platform14', b'Platform 14'), (b'platform15', b'Platform 15'), (b'platform17', b'Platform 17'), (b'platform18', b'Platform 18'), (b'platform21', b'Platform 21'), (b'footwear-accessories-millinery', b'Footwear, Accessories & Millinery'), (b'knitwear', b'Knitwear'), (b'footwear', b'Footwear'), (b'accessory-design', b'Accessory Design'), (b'millinery', b'Millinery'), (b'design-as-catalyst-platform', b'Design as Catalyst Platform'), (b'design-through-making-platform', b'Design through Making Platform'), (b'design-for-manufacture-platform', b'Design for Manufacture Platform'), (b'object-mediated-interactions-platform', b'Object Mediated Interactions Platform'), (b'exploring-emergent-futures-platform', b'Exploring Emergent Futures Platform')]),
        ),
        migrations.AlterField(
            model_name='rcanowpage',
            name='body',
            field=wagtail.wagtailcore.fields.RichTextField(help_text=b"This is the main text of your post. It should be a description of the work, project or idea you're posting about"),
        ),
    ]
