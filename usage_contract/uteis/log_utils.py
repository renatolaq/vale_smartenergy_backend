from decimal import Decimal
import simplejson as json
from core.models import Log


class LogUtils(object):

    def __init__(self, _username='Anonymous'):

        self._log = None
        self._old_log = None
        self._username = _username

    def save_log(self, _id, _table_name, dic_new, _date_time):

        _str_new = json.dumps(dic_new, encoding='utf8', ensure_ascii=False)
        _str_new = _str_new.replace('"', "'")

        try:
            self._log = Log()
            self._log.field_pk = _id
            self._log.table_name = _table_name
            self._log.action_type = "CREATE"
            self._log.old_value = '{}'
            self._log.new_value = _str_new
            self._log.user = self._username
            self._log.date = _date_time
            self._log.save()

        except ValueError:
            print("An exception occurred")


    def change_null_value(self, dic, _null):

        if _null:
            for k in dic:
                if isinstance(dic[k], Decimal):
                    dic[k] = float(dic[k])

                if dic[k] is None:
                    dic[k] = 'null'

                if isinstance(k, dict):
                    for i in k:
                        if k[i] is None:
                            k[i] = 'null'
                        if isinstance(k[i], Decimal):
                            k[i] = float(k[i])
        else:
            for k in dic:
                if isinstance(dic[k], Decimal):
                    dic[k] = float(dic[k])

                if dic[k] == 'null':
                    dic[k] = ''

                if isinstance(k, dict):
                    for i in k:
                        if k[i] == 'null':
                            k[i] = ''
                        if isinstance(k[i], Decimal):
                            k[i] = float(k[i])

        return dic


    def update_log(self, _id, _table_name, dic_new, _date_time, _observation=''):

        make_update = False

        # Pega o ultimo log referente a mudanca realizada na tabela
        self._old_log = Log.objects.filter(field_pk=_id, table_name=_table_name).order_by('-date').first()
        if self._old_log is not None:

            _old_value = self._old_log.new_value.replace("'", '"')

            _str_new = json.dumps(dic_new, encoding='utf8', ensure_ascii=False)
            
            # Se nao for igual ao que jah existe no banco de dados, entao salva um novo log
            if _old_value != _str_new:
                try:
                    _new_value = _str_new.replace('"', "'")

                    self._log = Log()
                    self._log.field_pk = _id
                    self._log.table_name = _table_name
                    self._log.action_type = "UPDATE"
                    self._log.old_value = _old_value.replace('"', "'")
                    self._log.new_value = _new_value
                    self._log.user = self._username
                    self._log.date = _date_time
                    self._log.observation = _observation
                    self._log.save()
                    make_update = True

                except ValueError:
                    print("An exception occurred")

        return make_update
