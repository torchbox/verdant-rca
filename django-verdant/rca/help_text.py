HELP_TEXT = {
    # Insert edited help text from the RCA here
}


def help_text(model_name, field_name, default=''):
    if (model_name, field_name) in HELP_TEXT:
        return HELP_TEXT[model_name, field_name]
    else:
        return default
