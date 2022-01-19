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

class VerifiersTest(unittest.TestCase):

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # def verify_template(_df, template_name, is_prod_dash)

    def test_verify_template_false(self):
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('manual_import', '')
        file_path_template = os.path.join(BASE_DIR, 'uploads', 'templates', 'template_CCEE.xlsx')
        _df = pd.read_excel(file_path_template, 'Dados')
        self.assertFalse(verify_template(_df, 'template_KSB1.xlsx', True))

    def test_verify_template_true(self):
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('manual_import', '')
        file_path_template = os.path.join(BASE_DIR, 'uploads', 'templates', 'template_CCEE.xlsx')
        _df = pd.read_excel(file_path_template, 'Dados')
        self.assertTrue(verify_template(_df, 'template_CCEE.xlsx', True))

    def test_verify_template_prod_dash_false(self):
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('manual_import', '')
        file_path_template = os.path.join(BASE_DIR, 'uploads', 'templates', 'template_KSB1.xlsx')
        _df = pd.read_excel(file_path_template, 'Dados')
        self.assertTrue(verify_template(_df, 'template_KSB1.xlsx', False))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # def test_verify_date_type(_value)

    def test_verify_date_type(self):
        from datetime import datetime
        now = datetime.now()
        self.assertEqual(verify_date_type(now), now)

    def test_verify_date_type_str(self):
        from datetime import datetime
        _date = '01/01/2020'
        self.assertEqual(verify_date_type(_date), datetime.strptime(_date, '%d/%m/%Y'))

    def test_verify_date_type_none(self):
        self.assertIsNone(verify_date_type('teste'))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # def verify_hour_type(_value)

    def test_verify_hour_type_int(self):
        self.assertTrue(verify_hour_type(1))

    def test_verify_hour_type_str(self):
        self.assertTrue(verify_hour_type('1'))

    def test_verify_hour_type_error(self):
        self.assertIsNone(verify_hour_type('teste'))

    def test_verify_hour_type_none(self):
        self.assertIsNone(verify_hour_type(100.0))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # def verify_type(_type, _value)

    def test_verify_type_text(self):
        self.assertTrue(verify_type('texto', 'test'))

    def test_verify_type_data(self):
        from datetime import datetime
        now = datetime.now()
        self.assertTrue(verify_type('data', now))

    def test_verify_type_hora(self):
        from datetime import time
        _time = time(3, 45, 12)
        self.assertTrue(verify_type('hora', _time))

    def test_verify_type_inteiro(self):
        self.assertTrue(verify_type('inteiro', 1))

    def test_verify_type_inteiro2(self):
        self.assertTrue(verify_type('inteiro', 1.0))

    def test_verify_type_decimal(self):
        self.assertTrue(verify_type('decimal', 1.1))

    def test_verify_type_decimal2(self):
        self.assertTrue(verify_type('decimal', 1.0))

    def test_verify_type_decimal3(self):
        self.assertTrue(verify_type('decimal', 1))

    def test_verify_type_error(self):
        self.assertFalse(verify_type('teste', 0))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # def verify_decimal_type(_value)

    def test_verify_decimal_type_int(self):
        self.assertEqual(verify_decimal_type(1), float(1))

    def test_verify_decimal_type_float(self):
        self.assertEqual(verify_decimal_type(1.0), 1.0)

    def test_verify_decimal_type_str1(self):
        self.assertEqual(verify_decimal_type('123.321'), 123.321)

    def test_verify_decimal_type_str2(self):
        self.assertEqual(verify_decimal_type('123,321'), 123.321)

    def test_verify_decimal_type_str3(self):
        self.assertEqual(verify_decimal_type('2,123.321'), 2123.321)

    def test_verify_decimal_type_str4(self):
        self.assertEqual(verify_decimal_type('2.123,321'), 2123.321)

    def test_verify_decimal_type_str5(self):
        self.assertIsNone(verify_decimal_type('teste'))

    def test_verify_decimal_type_str6(self):
        self.assertEqual(verify_decimal_type('1'), float('1'))

    def test_verify_decimal_type_none(self):
        from datetime import datetime
        self.assertIsNone(verify_decimal_type(datetime.now()))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # def verify_type_file(file_path, file_type)

    def test_verify_type_file_ksb1(self):
        file_path = '/teste/ksb1_.xlsx'
        file_type = 'ksb1'
        self.assertTrue(verify_type_file(file_path, file_type))

    def test_verify_type_file_fbl3n(self):
        file_path = '/teste/fbl3n_.xlsx'
        file_type = 'fbl3'
        self.assertTrue(verify_type_file(file_path, file_type))

    def test_verify_type_file_ccee(self):
        file_path = '/teste/ccee_.xlsx'
        file_type = 'ccee'
        self.assertTrue(verify_type_file(file_path, file_type))

    def test_verify_type_file_producao(self):
        file_path = '/teste/producao_.xlsx'
        file_type = 'producao'
        self.assertTrue(verify_type_file(file_path, file_type))

    def test_verify_type_file_dashboard(self):
        file_path = '/teste/dashboards_.xlsx'
        file_type = 'dashboards'
        self.assertTrue(verify_type_file(file_path, file_type))

    def test_verify_type_file_error(self):
        file_path = '/teste/teste.xlsx'
        file_type = 'teste'
        self.assertFalse(verify_type_file(file_path, file_type))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # def verify_file_name(file_name)

    def test_verify_file_name_ksb1(self):
        file_name = '/teste/ksb1_.xlsx'
        self.assertTrue(verify_file_name(file_name))

    def test_verify_file_name_fbl3(self):
        file_name = '/teste/fbl3n_.xlsx'
        self.assertTrue(verify_file_name(file_name))

    def test_verify_file_name_dash(self):
        file_name = '/teste/dashboards_.xlsx'
        self.assertTrue(verify_file_name(file_name))

    def test_verify_file_name_prod(self):
        file_name = '/teste/producao_.xlsx'
        self.assertTrue(verify_file_name(file_name))

    def test_verify_file_name_ccee(self):
        file_name = '/teste/ccee_.xlsx'
        self.assertTrue(verify_file_name(file_name))

    def test_verify_file_name_error(self):
        file_name = '/teste/teste_.xlsx'
        self.assertIsNone(verify_file_name(file_name))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # def get_source_ccee(df)

    def test_get_source_ccee_nat(self):
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path_template = os.path.join(BASE_DIR, 'tests', 'arquivos', 'ccee_vazio.xlsx')
        _df = pd.read_excel(file_path_template, 'Dados')
        self.assertDictEqual(get_source_ccee(_df), {'vazio': {"error_type": "error_ima_required", "error_param": "Medidor"}})

    def test_get_source_ccee_wrong(self):
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path_template = os.path.join(BASE_DIR, 'tests', 'arquivos', 'ccee_errado.xlsx')
        _df = pd.read_excel(file_path_template, 'Dados')
        self.assertDictEqual(get_source_ccee(_df),  {'Teste 1': {'error_type': 'error_ima_source', 'error_param': 'Teste'}})

    def test_get_source_ccee_meter(self):
        _meter = 'teste'
        _list = [_meter]
        _df = pd.DataFrame(_list)
        self.assertDictEqual(get_source_ccee(_df), {'teste': {'error_type': 'error_ima_source', 'error_param': 'teste'}})

    def test_get_source_ccee(self):
        _list = ['BACTG-04L2-15']
        _df = pd.DataFrame(_list)
        self.assertDictEqual(get_source_ccee(_df), {'BACTG-04L2-15': {'id_gauge': 10070}})

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # def get_quantity(df)

    def test_get_quantity(self):
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path_template = os.path.join(BASE_DIR, 'tests', 'arquivos', 'dashboards_dados.xlsx')
        _df = pd.read_excel(file_path_template, 'Dados')
        self.assertDictEqual(get_quantity(_df), {'Consumo Orçado (MWm)': {'id_measurements': 13}})

    def test_get_quantity_empty(self):
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path_template = os.path.join(BASE_DIR, 'tests', 'arquivos', 'dashboards_vazio.xlsx')
        _df = pd.read_excel(file_path_template, 'Dados')
        self.assertDictEqual(get_quantity(_df), {'vazio': {'error_type': 'error_ima_required', 'error_param': 'Grandeza'}})

    def test_get_quantity_wrong(self):
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path_template = os.path.join(BASE_DIR, 'tests', 'arquivos', 'dashboards_dados_errados.xlsx')
        _df = pd.read_excel(file_path_template, 'Dados')
        self.assertDictEqual(get_quantity(_df), {'Gasto Encargos Real2': {"error_type": "error_ima_quantity", "error_param" : 'Gasto Encargos Real2'}})

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # def get_source_pme(df)

    def test_get_source_pme_data(self):
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path_template = os.path.join(BASE_DIR, 'tests', 'arquivos', 'dashboards_dados.xlsx')
        _df = pd.read_excel(file_path_template, 'Dados')
        self.assertDictEqual(get_source_pme(_df), {'BR_ALEGRIA.FRONTEIRA': {'id_gauge': 10071}})

    def test_get_source_pme_empty(self):
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path_template = os.path.join(BASE_DIR, 'tests', 'arquivos', 'dashboards_source_vazio.xlsx')
        _df = pd.read_excel(file_path_template, 'Dados')
        self.assertDictEqual(get_source_pme(_df), {'vazio': {'error_type': 'error_ima_required', 'error_param': 'TAG do ponto de medição'}})

    def test_get_source_pme_data_wrong(self):
        _meter = 'teste 1'
        _list = [_meter]
        _df = pd.DataFrame(_list)
        self.assertDictEqual(get_source_pme(_df), {'teste 1': {'error_type': 'error_ima_source', 'error_param': 'teste'}})

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # def verify_data_prod_dash(df, _utc, file_path, em)

    def test_verify_data_prod_dash_empty(self):
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _file_path = os.path.join(BASE_DIR, 'tests', 'arquivos', 'dashboards_vazio.xlsx')
        _df = pd.read_excel(_file_path, 'Dados')

        from datetime import datetime
        _utc = datetime.now()
        em = ErrorManager()

        list_out, em_aux = verify_data_prod_dash(_df, _utc, _file_path, em)
        self.assertEqual(list_out, [])

    def test_verify_data_prod_dash(self):
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _file_path = os.path.join(BASE_DIR, 'tests', 'arquivos', 'dashboards_dados.xlsx')
        _df = pd.read_excel(_file_path, 'Dados')

        from datetime import datetime
        _utc = datetime.now()
        em = ErrorManager()

        list_out, em_aux = verify_data_prod_dash(_df, _utc, _file_path, em)
        self.assertEqual(list_out, list_out)

    def test_verify_data_prod_dash_template(self):

        _df = pd.DataFrame(['teste'])
        from datetime import datetime
        _utc = datetime.now()

        _file_path = 'ksb1_.xlsx'
        em = ErrorManager()

        list_out, em_aux = verify_data_prod_dash(_df, _utc, _file_path, em)
        self.assertEqual(list_out, [])

    def test_verify_data_prod_wrong(self):
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _file_path = os.path.join(BASE_DIR, 'tests', 'arquivos', 'producao_dados_errados.xlsx')
        _df = pd.read_excel(_file_path, 'Dados')

        from datetime import datetime
        _utc = datetime.now()

        em = ErrorManager()

        list_out, em_aux = verify_data_prod_dash(_df, _utc, _file_path, em)
        self.assertEqual(list_out, [])

    def test_verify_data_prod_quantity_empty(self):
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _file_path = os.path.join(BASE_DIR, 'tests', 'arquivos', 'producao_quantity_vazio.xlsx')
        _df = pd.read_excel(_file_path, 'Dados')

        from datetime import datetime
        _utc = datetime.now()
        em = ErrorManager()

        list_out, em_aux = verify_data_prod_dash(_df, _utc, _file_path, em)
        self.assertEqual(list_out, [])

    def test_verify_data_prod_source_empty(self):
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _file_path = os.path.join(BASE_DIR, 'tests', 'arquivos', 'producao_source_vazio.xlsx')
        _df = pd.read_excel(_file_path, 'Dados')

        from datetime import datetime
        _utc = datetime.now()

        em = ErrorManager()

        list_out, em_aux = verify_data_prod_dash(_df, _utc, _file_path, em)
        self.assertEqual(list_out, [])

    def test_verify_data_prod_value_empty(self):
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _file_path = os.path.join(BASE_DIR, 'tests', 'arquivos', 'producao_valor_vazio.xlsx')
        _df = pd.read_excel(_file_path, 'Dados')

        from datetime import datetime
        _utc = datetime.now()
        em = ErrorManager()

        list_out, em_aux = verify_data_prod_dash(_df, _utc, _file_path, em)
        self.assertEqual(list_out, [])

    def test_verify_data_prod_wrong_values(self):
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _file_path = os.path.join(BASE_DIR, 'tests', 'arquivos', 'producao_valores_errados.xlsx')
        _df = pd.read_excel(_file_path, 'Dados')

        from datetime import datetime
        _utc = datetime.now()
        em = ErrorManager()

        list_out, em_aux = verify_data_prod_dash(_df, _utc, _file_path, em)
        self.assertEqual(list_out, [])

    def test_verify_data_dash_wrong_values(self):
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _file_path = os.path.join(BASE_DIR, 'tests', 'arquivos', 'dashboards_valores_errados.xlsx')
        _df = pd.read_excel(_file_path, 'Dados')

        from datetime import datetime
        _utc = datetime.now()
        em = ErrorManager()

        list_out, em_aux = verify_data_prod_dash(_df, _utc, _file_path, em)
        self.assertEqual(list_out, list_out)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # def verify_data_ccee(df, _utc, em, csv=False)

    def test_verify_data_ccee_empty(self):
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _file_path = os.path.join(BASE_DIR, 'tests', 'arquivos', 'ccee_vazio.xlsx')
        _df = pd.read_excel(_file_path, 'Dados')

        from datetime import datetime
        _utc = datetime.now()
        em = ErrorManager()

        list_out, em_aux = verify_data_ccee(_df, _utc, em)
        self.assertEqual(list_out, [])

    # def test_verify_data_ccee_csv(self):
    #     BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    #     _file_path = os.path.join(BASE_DIR, 'tests', 'arquivos', 'ccee_dados.csv')
    #     _df = pd.read_csv(_file_path, encoding="ISO-8859-1", error_bad_lines=False, sep=',', usecols=[1, 2, 3])
    #
    #     from datetime import datetime
    #     _utc = datetime.now()
    #     em = ErrorManager()
    #
    #     list_out, em_aux = verify_data_ccee(_df, _utc, em, True)
    #     self.assertEqual(list_out, [])

    def test_verify_data_ccee_template(self):

        _df = pd.DataFrame(['teste'])
        from datetime import datetime
        _utc = datetime.now()

        _file_path = 'ksb1_.xlsx'
        em = ErrorManager()

        list_out, em_aux = verify_data_ccee(_df, _utc, em)
        self.assertEqual(list_out, [])

    def test_verify_data_ccee_wrong_values(self):

        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _file_path = os.path.join(BASE_DIR, 'tests', 'arquivos', 'ccee_valores_errados.xlsx')
        _df = pd.read_excel(_file_path, 'Dados')

        from datetime import datetime
        _utc = datetime.now()
        em = ErrorManager()

        list_out, em_aux = verify_data_ccee(_df, _utc, em)
        self.assertEqual(list_out, list_out)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # def verify_data_ksb1(df, em)

    def test_verify_data_ksb1_wrong_values(self):

        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _file_path = os.path.join(BASE_DIR, 'tests', 'arquivos', 'ksb1_dados.xlsx')
        _df = pd.read_excel(_file_path, 'Dados')

        list_out, em_aux = verify_data_ksb1(_df, ErrorManager())
        self.assertEqual(list_out, list_out)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # def verify_data_fbl3n(df, em)

    def test_verify_data_fbl3n_wrong_values(self):

        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _file_path = os.path.join(BASE_DIR, 'tests', 'arquivos', 'fbl3n_dados.xlsx')
        _df = pd.read_excel(_file_path, 'Dados')

        list_out, em_aux = verify_data_fbl3n(_df, ErrorManager())
        self.assertEqual(list_out, list_out)

