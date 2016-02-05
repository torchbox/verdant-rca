# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0020_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentpage',
            name='degree_subject',
            field=models.CharField(max_length=255, choices=[(b'animation', b'Animation'), (b'architecture', b'Architecture'), (b'ceramicsglass', b'Ceramics & Glass'), (b'communicationartdesign', b'Communication Art & Design'), (b'conservation', b'Conservation'), (b'contemporaryartpractice', b'Contemporary Art Practice'), (b'criticalhistoricalstudies', b'Critical & Historical Studies'), (b'criticalwritinginartdesign', b'Critical Writing in Art & Design'), (b'curatingcontemporaryart', b'Curating Contemporary Art'), (b'designinteractions', b'Design Interactions'), (b'designproducts', b'Design Products'), (b'drawingstudio', b'Drawing Studio'), (b'fashionmenswear', b'Fashion Menswear'), (b'fashionwomenswear', b'Fashion Womenswear'), (b'globalinnovationdesign', b'Global Innovation Design'), (b'goldsmithingsilversmithingmetalworkjewellery', b'Goldsmithing, Silversmithing, Metalwork & Jewellery'), (b'historyofdesign', b'History of Design'), (b'industrialdesignengineering', b'Industrial Design Engineering'), (b'informationexperiencedesign', b'Information Experience Design'), (b'innovationdesignengineering', b'Innovation Design Engineering'), (b'interiordesign', b'Interior Design'), (b'jewelleryandmetal', b'Jewellery & Metal'), (b'mres-healthcare-and-design', b'MRes: Healthcare & Design'), (b'mres-rca-communication-design-pathway', b'MRes RCA: Communication Design Pathway'), (b'mres-rca-design-pathway', b'MRes RCA: Design Pathway'), (b'mres-rca-fine-art-pathway', b'MRes RCA: Fine Art Pathway'), (b'mres-rca-humanities-pathway', b'MRes RCA: Humanities Pathway'), (b'painting', b'Painting'), (b'photography', b'Photography'), (b'print', b'Print'), (b'printmaking', b'Printmaking'), (b'sculpture', b'Sculpture'), (b'servicedesign', b'Service Design'), (b'textiles', b'Textiles'), (b'vehicledesign', b'Vehicle Design'), (b'visualcommunication', b'Visual Communication'), (b'curatingcontemporaryartcollegebased', b'Curating Contemporary Art (College-based)'), (b'curatingcontemporaryartworkbased', b'Curating Contemporary Art (Work-based)')]),
        ),
    ]
