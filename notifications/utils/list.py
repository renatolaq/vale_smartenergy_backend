from django.db.models import ForeignKey, TimeField


def find(array, parameter, value):
    for object in array:
        if object[parameter].lower() == value.lower():
            return object


def remove_primary_key_from_field_list(x):
    if "primary_key" in dir(x) and x.primary_key:
        return False
    return True


def remove_keys_and_relations_from_field_list(x):
    if "primary_key" in dir(x) and x.primary_key or x.is_relation:
        return False
    return True


def remove_time_fields_from_field_list(x):
    if type(x.get('object')) == TimeField:
        return False
    return True
