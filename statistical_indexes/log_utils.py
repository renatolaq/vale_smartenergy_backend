import simplejson as json
from django.utils import timezone
from core.models import Log
from .utils import get_user_username


class LogUtils(object):
    def __init__(self):
        self._log = None

    def save_log(self, _id, _table_name, _new, action_type="CREATE", observation='', request=None):
        _str_new = json.dumps(_new, encoding='utf8', ensure_ascii=False)
        _str_new = _str_new.replace('"', "'")
        old_value = self.get_old_log(_id, _table_name)

        try:
            self._log = Log()
            self._log.field_pk = _id
            self._log.table_name = _table_name
            self._log.action_type = action_type
            self._log.old_value = old_value
            self._log.new_value = _str_new
            self._log.user = get_user_username(request)
            self._log.date = timezone.now()
            self._log.observation = observation
            self._log.save()

        except ValueError:
            print("An exception occurred")

    def get_old_log(self, _id, _table_name):
        queryset = Log.objects.filter(field_pk=_id, table_name=_table_name)
        if not queryset.last():
            return '{}'
        return queryset.last().new_value

