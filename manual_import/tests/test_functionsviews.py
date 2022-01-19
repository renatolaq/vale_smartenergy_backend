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


class ManualImport(IntEnum):
    PRODUCAO = 0
    DASHBOARD = 1
    CCEE = 2
    KSB1 = 3
    FBL34N = 4
    CCEE_CSV = 5


class NewRequest:
    META = {'HTTP_ACCEPT_LANGUAGE': ''}


# validate_file, load_sources, validate_file_gauge, call_proc
class FunctionsViewsTest(unittest.TestCase):

    def test_validate_file_ksb1(self):

        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _file_path = os.path.join(BASE_DIR, 'tests', 'arquivos', 'ksb1_dados.xlsx')
        _df = pd.read_excel(_file_path, 'Dados')

        em_aux = validate_file(_df, ManualImport.KSB1)
        self.assertEqual(em_aux, em_aux)

    def test_validate_file_fbl3n(self):

        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _file_path = os.path.join(BASE_DIR, 'tests', 'arquivos', 'fbl3n_dados.xlsx')
        _df = pd.read_excel(_file_path, 'Dados')

        em_aux = validate_file(_df, ManualImport.FBL34N)
        self.assertEqual(em_aux, em_aux)

    def test_validate_file_gauge_dash(self):

        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _file_path = os.path.join(BASE_DIR, 'tests', 'arquivos', 'dashboards_dados.xlsx')
        _df = pd.read_excel(_file_path, 'Dados')

        from datetime import datetime
        _utc = datetime.now()

        em_aux = validate_file_gauge(_df, _file_path, _utc, ManualImport.DASHBOARD)
        self.assertEqual(em_aux, em_aux)

    def test_validate_file_gauge_prod(self):

        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _file_path = os.path.join(BASE_DIR, 'tests', 'arquivos', 'producao_dados.xlsx')
        _df = pd.read_excel(_file_path, 'Dados')

        from datetime import datetime
        _utc = datetime.now()

        em_aux = validate_file_gauge(_df, _file_path, _utc, ManualImport.PRODUCAO)
        self.assertEqual(em_aux, em_aux)

    def test_validate_file_gauge_ccee(self):

        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _file_path = os.path.join(BASE_DIR, 'tests', 'arquivos', 'ccee_valores_errados.xlsx')
        _df = pd.read_excel(_file_path, 'Dados')

        from datetime import datetime
        _utc = datetime.now()

        em_aux = validate_file_gauge(_df, _file_path, _utc, ManualImport.CCEE)
        self.assertEqual(em_aux, em_aux)

    def test_load_sources(self):

        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('manual_import', '')
        _file_path = os.path.join(BASE_DIR, 'uploads', 'templates/')

        full_path = load_sources(_file_path, '_PDCT', '_username')
        self.assertEqual(full_path, full_path)

    def test_call_proc(self):
        from datetime import datetime
        _utc = datetime.now()

        em = call_proc(_utc, ErrorManager())
        self.assertEqual(em, em)

    def test_format_dic_ima_erro_request(self):
        r = NewRequest()
        dic = format_dic_ima_erro({'errors': [{'lines': '1, 2, 3', 'error_type': '', 'error_param':''}]}, r)
        self.assertEqual(dic, dic)
