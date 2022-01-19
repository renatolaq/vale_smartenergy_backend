from rest_framework import serializers

class DeepSerializer(serializers.Field):
    def __init__(self, converter=None, read_only=False, write_only=False, required=None, default=serializers.empty,
                 initial=serializers.empty, source=None, label=None, help_text=None, style=None, error_messages=None, validators=None, allow_null=False):
        super().__init__(read_only=read_only, write_only=write_only, required=required, default=default, initial=initial, source="*",
                         label=label, help_text=help_text, style=style, error_messages=error_messages, validators=validators, allow_null=allow_null)
        self.__local_field = source
        self.__converter = converter

    def deep_get(self, dictionary, keys):
        keys = [""] + keys.split(".")
        def it(o):
            keys.pop(0)
            if(not keys or o is None):
                return o            
            if isinstance(o, dict):
                return it(o.get(keys[0]))
            return it(getattr(o, keys[0]))
        return it(dictionary)

    def to_representation(self, obj):
        if(self.__local_field is None):
            self.__local_field = self.field_name
        ret = self.deep_get(obj, self.__local_field)
        if self.__converter:
            ret = self.__converter(ret)
        return ret