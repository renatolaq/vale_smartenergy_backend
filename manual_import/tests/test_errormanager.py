import os
import requests
from enum import IntEnum

import pandas as pd
import unittest

from manual_import.utils.verifiers import verify_type
from manual_import.utils.verifiers import verify_template, verify_date_type, verify_hour_type
from manual_import.utils.verifiers import get_source_ccee, get_source_pme, get_quantity
from manual_import.utils.verifiers import verify_type_file, verify_decimal_type, verify_file_name
from manual_import.utils.verifiers import verify_data_prod_dash, verify_data_ccee, verify_data_ksb1, verify_data_fbl3n

from manual_import.views import validate_file, load_sources, validate_file_gauge, call_proc, format_dic_ima_erro


from rest_framework import status
from rest_framework.test import APITestCase

from manual_import.utils.error_manager import ErrorManager




class ErrorManagerTest(APITestCase):

    def test_has_single_errors_false(self):
        em = ErrorManager()
        self.assertFalse(em.has_single_errors())

    def test_has_multi_errors_false(self):
        em = ErrorManager()
        self.assertFalse(em.has_multi_errors())

    def test_append_no_errors(self):
        em = ErrorManager()
        self.assertDictEqual(em.get_dic_response(), {"msg": "success_ima", "errors": []})

    def test_append_single_errors_unknow(self):
        em = ErrorManager()
        em.set_single_error("test")
        self.assertDictEqual(em.get_dic_response(), {"msg": "error_ima_unknown", "errors": []})

    def test_append_single_errors_know(self):
        em = ErrorManager()
        em.set_single_error("error_ima_template")
        self.assertDictEqual(em.get_dic_response(), {"msg": "error_ima_template", "errors": []})

    def test_append_multi_errors(self):
        em = ErrorManager()
        em.append_mult_error(1, "test_label", "test_param")
        self.assertDictEqual(em.get_dic_response(), {"msg": "success_ima_errors", "errors": [
            {"error_type": "test_label", "error_param": "test_param", "lines": '1'}]})

    def test_append_multi_lines_errors(self):
        em = ErrorManager()
        em.append_mult_error(1, "test_label", "test_param")
        em.append_mult_error(2, "test_label", "test_param")
        self.assertDictEqual(em.get_dic_response(), {"msg": "success_ima_errors", "errors": [
            {"error_type": "test_label", "error_param": "test_param", "lines": '1,2'}]})

