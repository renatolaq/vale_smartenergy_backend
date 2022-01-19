from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from django.db import transaction
from django.db.models import Q
from rest_framework.test import APITestCase

from company.models import Company



class CompanyTest(APITestCase):
    # loads fixtures dependencies
    fixtures = [
        #'core/fixtures/initial_data_dxc.json', 'company/fixtures/initial_data_dxc.json',
        #'agents/fixtures/initial_data_dxc.json', 'profiles/fixtures/initial_data_dxc.json', 
        #'assets/fixtures/initial_data_dxc.json', 'asset_items/fixtures/initial_data_dxc.json',
        #'organization/fixtures/initial_data_dxc.json', 'gauge_point/fixtures/initial_data_dxc.json',
        #'energy_composition/fixtures/initial_data_dxc.json'
    ]
    

    def test_post(self):
        url = '/company-api/session_company_post/'
        expected = {
            "street": "Teste Logradouro",
            "number": "123",
            "zip_code": "11111-111",
            "type": None,
            "id_city": 27,
            "neighborhood": "Teste Bairro",
            "id_state": 2,
            "id_endereco": None,
            "address_company": {
                "company_name": "Teste",
                "legal_name": "Teste",
                "registered_number": "11111111",
                "type": "E",
                "state_number": "11.111.111/1111-11",
                "nationality": "BRA",
                "id_sap": "15501223",
                "id_endereco": None,
                "characteristics": None,
                "eletric_utility": {
                    "instaled_capacity": None,
                    "guaranteed_power": None,
                    "regulatory_act": None,
                    "internal_loss": None,
                    "transmission_loss": None
                },
                "bank_account": [
                    {
                        "id_bank": None,
                        "bank": "BB",
                        "account_type": 1,
                        "account_number": "123",
                        "bank_agency": "12",
                        "main_account": "N",
                        "other": "Adicional"
                    }
                ],
                "company_contacts": [
                    {
                        "id_contacts": None,
                        "responsible": "Teste Nome ",
                        "email": "a@a.com",
                        "phone": "(11) 1111-1111",
                        "cellphone": "(11) 11111-1111",
                        "type": "Financeiro"
                    }
                ],
                "transmission_loss": None,
                "internal_loss": None,
                "regulatory_act": None,
                "guaranteed_power": None,
                "instaled_capacity": None,
                "status": "S"
            },
            "complement": "Teste Complemento"
        }

        response = self.client.post(url, expected, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        expected_error = {
            "address_company": {
                "company_name": "ABC",
                "company_contacts":[]
            },
            "number":" "
        }
        headers = {"Accept-Language": "en-US,en;q=0.5"}
        response = self.client.post(url, expected_error, format='json', META=headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get(self):
        url = '/company-api/session_company/'
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

        urls = [
            '/company-api/company_find/',
            '/company-api/company_find_basic/'
        ]
        for url_find in urls:
            response = self.client.get(url_find, format='json')
            self.assertTrue(status.is_success(response.status_code))


        url_find = '/company-api/company_find_basic/?registered_number=38810859' \
                        '&company_name=cann&page_size=5&state_number=1&country=Brasil'
        response = self.client.get(url_find, format='json')
        self.assertTrue(status.is_success(response.status_code))


        # url_find = '/company-api/get_energy_composition_company/2/'
        # response = self.client.get(url_find, format='json')
        # self.assertTrue(status.is_success(response.status_code))

        url_find = '/company-api/get_state_by_country/?id_country=1'
        response = self.client.get(url_find, format='json')
        self.assertTrue(status.is_success(response.status_code))

        url_find = '/company-api/get_cities_by_state/?id_state=1'
        response = self.client.get(url_find, format='json')
        self.assertTrue(status.is_success(response.status_code))

        url = '/company-api/session_basic_log/20255/'
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

    def test_update(self):  
        # exists
        company = Company.objects.last()

        url = '/company-api/session_company/%s/' %company.pk
        urlPut='/company-api/session_company_put/%s/' %company.pk

        expected_error = {"address_company": {
            "id_company": company.pk,
            "company_name": "ABC",
            "company_contacts":[]
            },
            "number":" "
        }

        response = self.client.get(url)
        self.assertTrue(status.is_success(response.status_code))

        # put
        response = self.client.put(urlPut, response.data, format='json')
        self.assertTrue(status.is_success(response.status_code))

        # put
        response = self.client.get(url)
        bad = response.data
        bad['company_name'] = None
        response = self.client.put(urlPut, bad, format='json')
        self.assertTrue(status.is_success(response.status_code))

        #put status
        company = Company.objects.filter(
            energyComposition_company__isnull=True, 
            agents_company__isnull=True,
            assetitems_company__isnull=True,
            gauge_company__isnull=True,
            assets_company__isnull=True,
            company_dealership__isnull=True
        ).last()
        url = '/company-api/session_company/%s/' %company.pk
        urlPut='/company-api/session_company_put/%s/' %company.pk

        response = self.client.get(url)
        response.data['status']='N'
        response = self.client.put(urlPut, response.data, format='json')
        self.assertTrue(status.is_success(response.status_code))

        #put status - BAD REQUEST
        company = Company.objects.filter(
            Q(energyComposition_company__isnull=False) | 
            Q(agents_company__isnull=False) |
            Q(assetitems_company__isnull=False) |
            Q(gauge_company__isnull=False) |
            Q(assets_company__isnull=False) |
            Q(company_dealership__isnull=False)
        ).last()
        url = '/company-api/session_company/%s/' %company.pk
        urlPut='/company-api/session_company_put/%s/' %company.pk

        response = self.client.get(url)
        response.data['status']='N'
        response = self.client.put(urlPut, response.data, format='json')
        self.assertTrue(status.is_success(response.status_code))


        # put bad request
        response = self.client.put(urlPut, expected_error, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        expected_error = {
            "address_company": {
                "id_company":0,
                "company_name": "ABC",
                "company_contacts":[]
            },
            "number":" "
        }

        response = self.client.put(urlPut, expected_error, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # not found
        url = '/company-api/session_company/%s/' % 0
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_valid_sap(self):
        url = '/company-api/validated_sap/99659595/'
        response = self.client.get(url)
        self.assertTrue(status.is_success(response.status_code))
        #Error
        url = '/company-api/validated_sap/90034437/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_company_find_file_pdf(self):

        url_find = '/company-api/company_find_file/?format_file=pdf&' \
                   'registered_number=38810859' \
                   '&company_name=cann&page_size=5&ordering=create_date&city_name' \
                   '=arara&status=a&sap=1111111107&type=f&state=Paulo&' \
                   'date_creation_start=2019-09-05&date_creation_end=2019-09-15'

        response = self.client.get(url_find)
        self.assertTrue(status.is_success(response.status_code))

        url_find = '/company-api/company_find_file/?format_file=pdf&' \
                   'registered_number=38810859' \
                   '&company_name=cann&page_size=5&state_number=1&country=Brasil'

        response = self.client.get(url_find)
        self.assertTrue(status.is_success(response.status_code))

        url_find = '/company-api/company_find_file/?format_file=pdf'

        response = self.client.get(url_find)
        self.assertTrue(status.is_success(response.status_code))

    
    def test_company_find_file_csv(self):

        url_find = '/company-api/company_find_file/?format_file=csv&' \
                   'registered_number=38810859' \
                   '&company_name=cann&page_size=5&ordering=create_date&city_name' \
                   '=arara&status=a&sap=1111111107&type=f&state=Paulo&' \
                   'date_creation_start=2019-09-05&date_creation_end=2019-09-15'

        response = self.client.get(url_find)
        self.assertTrue(status.is_success(response.status_code))

        url_find = '/company-api/company_find_file/?format_file=csv&' \
                   'registered_number=38810859' \
                   '&company_name=cann&page_size=5&state_number=1&country=Brasil'

        response = self.client.get(url_find)
        self.assertTrue(status.is_success(response.status_code))

        url_find = '/company-api/company_find_file/?format_file=csv'

        response = self.client.get(url_find)
        self.assertTrue(status.is_success(response.status_code))
