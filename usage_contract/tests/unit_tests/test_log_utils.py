from datetime import date
from unittest import mock

from django.test import SimpleTestCase

from usage_contract.uteis.error import return_linked_budgets, generate_delete_msg
from usage_contract.tests.lib import usage_contract_mock, DateMock, HttpRequestMock
from usage_contract.uteis import log_utils
from datetime import datetime, date
import simplejson as json


class TestUsageContractUteisLog(SimpleTestCase):
    def test_logutils_constructor(self):
        log_util_obj = log_utils.LogUtils("user")
        self.assertEqual(log_util_obj._log, None)
        self.assertEqual(log_util_obj._old_log, None)
        self.assertEqual(log_util_obj._username, "user")

    @mock.patch("core.models.Log.save", return_value=mock.Mock())
    def test_save_log(self, log_save):
        date_string = "21 June, 2018"
        date_object = datetime.strptime(date_string, "%d %B, %Y")

        log_util_obj = log_utils.LogUtils("user")
        log_util_obj.save_log(1, "table", {"dic": "mock"}, date_object)

        _str_new = json.dumps({"dic": "mock"}, encoding="utf8", ensure_ascii=False)
        _str_new = _str_new.replace('"', "'")

        self.assertEqual(log_util_obj._log.new_value, _str_new)
        self.assertTrue(log_save.called)

    @mock.patch("core.models.Log.save", return_value=mock.Mock())
    @mock.patch("core.models.Log.objects.filter",)
    def test_update_log(self, log_save, log_filter):

        order_by_mock = mock.Mock()
        order_by_mock.order_by.return_value = 'obs'

        log_filter.return_value = order_by_mock

        date_string = "21 June, 2018"
        date_object = datetime.strptime(date_string, "%d %B, %Y")

        log_util_obj = log_utils.LogUtils("user")
        log_util_obj.update_log(1, "table", {"dic": "mock"}, date_object, 'obs')

        _str_new = json.dumps({"dic": "mock"}, encoding="utf8", ensure_ascii=False)
        _str_new = _str_new.replace('"', "'")

        self.assertEqual(log_util_obj._log.new_value, _str_new)
        self.assertTrue(log_save.called)

    
