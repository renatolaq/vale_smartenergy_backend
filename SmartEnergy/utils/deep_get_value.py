from typing import Collection, List, Mapping, Union

from django.db.models.manager import BaseManager
from django.db.models.query import QuerySet


def deep_get_value(source: Union[object, Mapping], path: Union[str, Collection], converter=lambda x: x, convert_when_none=False):
    def process(obj, array: List[str]):
        value = None
        if isinstance(obj, Mapping):
            value = obj.get(array[0])
        elif array[0].isdigit():
            i = int(array[0])
            if isinstance(obj, (BaseManager, QuerySet)):
                value = next(iter(obj.all()[i:i+1]), None)
            elif isinstance(obj, Collection):
                value = next(iter(obj[i:i+1]), None)
        else:
            value = getattr(obj, array[0], None)
        if len(array) == 1 or value is None:
            return converter(value) if convert_when_none or value is not None else None
        return process(value, array[1:])

    return process(source, path if isinstance(path, Collection) and not isinstance(path, str) else path.split('.'))
