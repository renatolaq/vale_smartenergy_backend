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

class UploadFileTest(APITestCase):

    def test_get_list(self):
        url_get = '/manual_import/upload-list/'
        json_basic = {
            "count": 2,
            "next": None,
            "previous": None,
            "results": [
                {
                    "id": 1,
                    "user_name": "C0464545 - Rutvik Krushnakumar Pensionwar_CONTR",
                    "date_upload": "2020-07-07 18:05:22:000",
                    "file_name": "CCEE_template_001.xlsx",
                    "file_path": "need_process/1594145122075949_C0464545_CCEE.xlsx",
                    "file_type": "CCEE",
                    "send_status": 1,
                    "msg": "{\"msg\": \"success_ima\", \"errors\": []}"
                },
                {
                    "id": 2,
                    "user_name": "C0464545 - Rutvik Krushnakumar Pensionwar_CONTR",
                    "date_upload": "2020-07-07 22:20:06:000",
                    "file_name": "CCEE_template_001.xlsx",
                    "file_path": "need_process/1594160406721247_C0464545_CCEE.xlsx",
                    "file_type": "CCEE",
                    "send_status": 1,
                    "msg": "{\"msg\": \"success_ima\", \"errors\": []}"
                },
                {
                    "id": 3,
                    "user_name": "C0464545 - Rutvik Krushnakumar Pensionwar_CONTR",
                    "date_upload": "2020-07-07 22:33:24:000",
                    "file_name": "CCEE_template_001.xlsx",
                    "file_path": "need_process/159416120417905_C0464545_CCEE.xlsx",
                    "file_type": "CCEE",
                    "send_status": 1,
                    "msg": "{\"msg\": \"success_ima\", \"errors\": []}"
                }
            ]
        }

        response = self.client.get(url_get, json_basic, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # def test_get_msg(self):
    #     url_get = '/manual_import/get_ima_log/1/'
    #     json_basic = {"msg": "Importado com sucesso e sem erros.", "errors": []}
    #     response = self.client.get(url_get, json_basic, format='json')
    #     self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_template(self):
        url_get = '/manual_import/upload-list/0/get_file_upload/?page=DSHB'
        response = self.client.get(url_get, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
