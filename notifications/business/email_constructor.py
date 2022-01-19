from notifications.utils.db import get_field_value
from notifications.utils.string import add_db_variable_brackets, display_as_str
from locales.translates_function import translate_label_by_language
import re

from jinja2 import Environment, PackageLoader, select_autoescape

env = Environment(
    loader=PackageLoader("notifications", "templates"),
    autoescape=select_autoescape(["html", "xml"]),
)


class EmailConstructor:
    @staticmethod
    def get_parsed_email_table_fields(module_name, fields):
        result = []

        for field in fields:
            field_name = translate_label_by_language(
                f"{module_name}_{field}".lower(), "pt-BR", field
            )
            result.append({"value": field, "name": field_name})

        return result

    @staticmethod
    def get_email_table_data(fields, data):
        result = []

        for value in data:
            values = []
            for field in fields:
                db_value = get_field_value(value, field)
                display_value = display_as_str(db_value)
                values.append(display_value)

            result.append(values)

        return result

    @staticmethod
    def get_parsed_email_message(message, data):
        db_fields = re.findall("\${(.*?)\}", message)

        result = message

        for db_field in db_fields:
            db_value = get_field_value(data, db_field)
            display_value = f"<b>{display_as_str(db_value)}</b>"

            result = result.replace(add_db_variable_brackets(db_field), display_value)

        return result

    @staticmethod
    def create_email_with_table_template(message, module_name, fields, data):
        parsed_fields = EmailConstructor.get_parsed_email_table_fields(
            module_name, fields
        )
        table_data = EmailConstructor.get_email_table_data(fields, data)
        template = env.get_template("email_with_table.html")

        rendered_template = template.render(
            message=message, fields=parsed_fields, table_data=table_data
        )

        return rendered_template

    @staticmethod
    def create_simple_email_template(message, data):
        parsed_message = EmailConstructor.get_parsed_email_message(message, data)

        template = env.get_template("simple_email.html")

        rendered_template = template.render(message=parsed_message)

        return rendered_template
