from datetime import datetime, timezone
from decimal import Decimal
import simplejson as json
from django.db.models.base import ModelBase

from core.models import Log


class LogUtils(object):
    def __init__(
        self, serializer, username="Anonymous",
    ):
        self._username = username
        self._serializer = serializer

    def save_log(self, model_object: ModelBase, observation=None):
        serialized_model_data = self._serializer(model_object).data
        _str_new = json.dumps(
            serialized_model_data, encoding="utf8", ensure_ascii=False
        )
        _str_new = _str_new.replace('"', "'")

        log = Log()
        log.field_pk = model_object.id
        log.table_name = model_object._meta.db_table
        log.action_type = "CREATE"
        log.old_value = "{}"
        log.new_value = _str_new
        log.user = self._username
        log.date = datetime.now(tz=timezone.utc)
        log.observation = observation
        log.save()

    def update_log(self, updated_model_object: ModelBase, observation=None):
        table_name = updated_model_object._meta.db_table
        old_log = (
            Log.objects.filter(field_pk=updated_model_object.id, table_name=table_name)
            .order_by("-date")
            .first()
        )

        if old_log is not None:
            old_value = old_log.new_value.replace("'", '"')
            serialized_model_data = self._serializer(updated_model_object).data
            new_value = json.dumps(
                serialized_model_data, encoding="utf8", ensure_ascii=False
            )
            new_value.replace('"', "'")

            if old_value != new_value:
                log = Log()
                log.field_pk = updated_model_object.id
                log.table_name = table_name
                log.action_type = "UPDATE"
                log.old_value = old_value.replace('"', "'")
                log.new_value = new_value
                log.user = self._username
                log.date = datetime.now(tz=timezone.utc)
                log.observation = observation
                log.save()
                return True

        return False
