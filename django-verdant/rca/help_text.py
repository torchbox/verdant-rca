HELP_TEXT = {
    # Insert edited help text from the RCA here
}


ALL_FIELDS = []


def help_text(model_name, field_name, default=''):
    # Commented out to improve memory usage. Uncomment if you would like
    # to export the fields to CSV
    # ALL_FIELDS.append((model_name, field_name, default))

    if (model_name, field_name) in HELP_TEXT:
        return HELP_TEXT[model_name, field_name]
    else:
        return default


def export_csv(f):
    from django.db.models import get_model
    import csv

    csvwriter = csv.writer(f)
    for model_name, field_name, help_text in ALL_FIELDS:
        model = get_model(*model_name.split('.'))

        if model is not None:
            field_verbose_name = model._meta.get_field_by_name(field_name)[0].verbose_name.title()
        else:
            field_verbose_name = field_name.replace('_', ' ').title()

        csvwriter.writerow([model_name, field_name, field_verbose_name, help_text])
