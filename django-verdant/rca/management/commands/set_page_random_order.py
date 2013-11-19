from django.core.management.base import NoArgsCommand
from django.db import connection, models, transaction


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        # Get models which have a random_order field
        randomised_models = [
            model for model in models.get_models() 
            if [
                field for field in model._meta.fields 
                if field.name == 'random_order'
            ]
        ]

        # Update random order field
        cursor = connection.cursor()
        for model in randomised_models:
            cursor.execute('UPDATE ' + model._meta.db_table + ' SET random_order = floor(100000*RANDOM());')
        transaction.commit_unless_managed()