from django.template import Template, Context
from django.utils import timezone


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
            <p>Generated: {{ time|date:'l dS F Y P' }}</p>
          </body>
        </html>
        """

    def __init__(self, data):
        self.data = data

    def get_title(self):
        return self.title

    def get_headings(self):
        return [field[0] for field in self.fields]

    def get_rows(self):
        for row in self.data:
            yield [field_func(self, row) for field_name, field_func in self.fields]

    def get_csv(self):
        csv = ', '.join(['"' + heading + '"' for heading in self.get_headings()]) + '\n'

        for row in self.get_rows():
            csv += ', '.join(['"' + field[0] + '"' for field in row]) + '\n'

        return csv

    def get_html(self):
        template = Template(self.template)
        context = Context({
            'extra_css': self.extra_css,
            'title': self.get_title(),
            'headings': self.get_headings(),
            'rows': self.get_rows(),
            'time': timezone.now(),
        })

        return template.render(context)
