def get_db_field_internal_type(field_name, module):
    non_related_fields, related_fields = module.get_fields()
    fields = non_related_fields + related_fields
    field = [x["object"] for x in fields if x["name"] == field_name][0]
    return field.get_internal_type()


def get_field_value(data, field_name):
    if data == None:
        return ""

    splited_field = field_name.split("__", 1)

    if len(splited_field) > 1:
        return get_field_value(getattr(data, splited_field[0]), splited_field[1])

    return getattr(data, field_name)


def get_field_list_by_data(data, field_name):
    result = []

    for data_field in data:
        result.append(getattr(data_field, field_name))

    return result
