from django.template import Template, Context
from django.utils import timezone, dateformat
import StringIO, unicodecsv


class Report(object):
    title = "Report"
    fields = ()
    extra_css = ""
    template = """
        <!DOCTYPE html>
        <html lang="en">
          <head>
            <meta charset="UTF-8">
            <title>{{ title }}</title>
            <style type="text/css">
              table, th, td {
                border: 1px solid black;
              }
              table {
                width: 100%;
                border-collapse: collapse;
              }
              th, td {
                padding: 3px;
              }
              tbody tr:nth-child(odd) {
                background: #eee;
              }
              tbody tr:hover {
                background: #EED26A;
              }
              a {
                color: inherit;
              }
              {{ extra_css }}
            </style>
          </head>
          <body>
            <h3>{{ title }}</h3>
            <table>
              <thead>
                {% for heading in headings %}
                  <th>{{ heading }}</th>
                {% endfor %}
              </thead>
              <tbody>
                {% for row in rows %}
                  <tr>
                    {% for field in row %}
                      <td{% if field.1 %} class="{{ field.1 }}"{% endif %}>
                        {% if field.2 %}
                          <a href="{{ field.2 }}">{{ field.0 }}</a>
                        {% else %}
                          {{ field.0 }}
                        {% endif %}
                      </td>
                    {% endfor %}
                  </tr>
                {% endfor %}
              </tbody>
            </table>
            <p>{{ footer|safe }}</p>
          </body>
        </html>
        """

    def __init__(self, data, **kwargs):
        self.data = data
        self.kwargs = kwargs
        self.rows_output = None

    def get_title(self):
        return self.title

    def get_fields(self):
        return self.fields

    def get_footer(self):
        return "Generated: " + dateformat.format(timezone.now(), 'l dS F Y P')

    def get_headings(self):
        return [field[0] for field in self.get_fields()]

    def include_in_report(self, obj):
        return True

    def post_process(self, obj, fields):
        return fields

    def get_rows(self):
        for row in self.data:
            if not self.include_in_report(row):
              continue

            fields = self.post_process(row, [field_func(self, row) for field_name, field_func in self.get_fields()])

            if fields is not None:
                yield fields

    def run(self):
        self.rows_output = list(self.get_rows())

    def get_csv(self):
        output = StringIO.StringIO()
        cw = unicodecsv.writer(output)
        cw.writerow(self.get_headings())

        for row in self.rows_output:
            cw.writerow([field[0] for field in row])

        return output.getvalue()

    def get_html(self):
        template = Template(self.template)
        context = Context({
            'extra_css': self.extra_css,
            'title': self.get_title(),
            'headings': self.get_headings(),
            'rows': self.rows_output,
            'footer': self.get_footer()
        })

        return template.render(context).encode('UTF-8')
