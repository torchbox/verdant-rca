# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2019-05-03 13:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0104_auto_20190503_1202'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newstudentpage',
            name='ma_specialism',
            field=models.CharField(blank=True, choices=[(b'2018/19', ((b'animation--experimental-animation-pathway', b'Animation: Experimental Animation Pathway'), (b'animation--documentary-animation-pathway', b'Animation: Documentary Animation Pathway'), (b'animation--narrative-animation-pathway', b'Animation: Narrative Animation Pathway'), (b'contemporary-art-practice--critical-practice-pathway', b'Contemporary Art Practice: Critical Practice Pathway'), (b'contemporary-art-practice--moving-image-pathway', b'Contemporary Art Practice: Moving Image Pathway'), (b'contemporary-art-practice--performance-pathway', b'Contemporary Art Practice: Performance Pathway'), (b'contemporary-art-practice--public-sphere-pathway', b'Contemporary Art Practice: Public Sphere Pathway'), (b'fashion--millinery', b'Fashion: Millinery'), (b'fashion--footwear', b'Fashion: Footwear'), (b'fashion--accessories', b'Fashion: Accessories'), (b'fashion--knitwear', b'Fashion: Knitwear'), (b'ied--experimental-design', b'IED: Experimental Design'), (b'ied--moving-image-design', b'IED: Moving Image Design'), (b'ied--sound-design', b'IED: Sound Design'), (b'interior-design--exhibition-design-pathway', b'Interior Design: Exhibition Design Pathway'), (b'textiles--knit', b'Textiles: Knit'), (b'textiles--mixed-media', b'Textiles: Mixed-media'), (b'textiles--print', b'Textiles: Print'), (b'textiles--smart-textiles', b'Textiles: Smart Textiles'), (b'textiles--weave', b'Textiles: Weave'), (b'visual-communication--graphic-design', b'Visual Communication: Graphic Design'), (b'visual-communication--illustration', b'Visual Communication: Illustration'), (b'visual-communication--experimental-communication', b'Visual Communication: Experimental Communication'))), (b'2016/17', ((b'accessories', b'Accessories'), (b'footwear', b'Footwear'), (b'knitwear', b'Knitwear'), (b'millinery', b'Millinery'), (b'knit', b'Knit'), (b'mixed-media', b'Mixed-media'), (b'print', b'Print'), (b'weave', b'Weave'), (b'critical-Practice', b'Critical Practice'), (b'performance', b'Performance'), (b'public-sphere', b'Public Sphere'), (b'moving-image', b'Moving Image'))), (b'2015/16', ((b'ads1', b'ADS1'), (b'ads2', b'ADS2'), (b'ads3', b'ADS3'), (b'ads4', b'ADS4'), (b'ads5', b'ADS5'), (b'ads6', b'ADS6'), (b'ads7', b'ADS7'), (b'ads9', b'ADS9'), (b'knit', b'Knit'), (b'mixed media', b'Mixed media'), (b'print', b'Print'), (b'weave', b'Weave'), (b'performance', b'Performance'), (b'movingimage', b'Moving Image'), (b'knitwear', b'Knitwear'), (b'footwear', b'Footwear'), (b'accessory-design', b'Accessory Design'), (b'millinery', b'Millinery'), (b'design-as-catalyst-platform', b'Design as Catalyst Platform'), (b'design-through-making-platform', b'Design through Making Platform'), (b'design-for-manufacture-platform', b'Design for Manufacture Platform'), (b'object-mediated-interactions-platform', b'Object Mediated Interactions Platform'), (b'exploring-emergent-futures-platform', b'Exploring Emergent Futures Platform'))), (b'2014/15', ((b'ads1', b'ADS1'), (b'ads2', b'ADS2'), (b'ads3', b'ADS3'), (b'ads4', b'ADS4'), (b'ads5', b'ADS5'), (b'ads6', b'ADS6'), (b'ads7', b'ADS7'), (b'ads9', b'ADS9'), (b'knit', b'Knit'), (b'mixed media', b'Mixed media'), (b'print', b'Print'), (b'weave', b'Weave'), (b'performance', b'Performance'), (b'movingimage', b'Moving Image'), (b'platform13', b'Platform 13'), (b'platform14', b'Platform 14'), (b'platform15', b'Platform 15'), (b'platform17', b'Platform 17'), (b'platform18', b'Platform 18'), (b'platform21', b'Platform 21'), (b'footwear-accessories-millinery', b'Footwear, Accessories & Millinery')))], help_text=b'', max_length=255, verbose_name=b'Specialism'),
        ),
    ]
