# -*- encoding: utf-8 -*-
"""
Create a copyable and embeddable form of the supplied help text values (in CSV form).

The generated output can be copied directly into the help_text.py dictionary.
Make sure that the supplied filename is 'rca_fields.csv'. Because of laziness on my
part, there are no parameters or command line switches.
"""


import csv


with open('rca_fields.csv') as csvfile:
    reader = csv.reader(csvfile, delimiter=',', quotechar='"')
    for row in reader:
        modelname, fieldname, _, help_text = row
        if help_text:
            print "    ({}, {}): {},".format(repr(modelname), repr(fieldname), repr(help_text))
