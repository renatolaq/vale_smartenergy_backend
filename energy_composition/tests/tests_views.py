from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from django.db import transaction
from rest_framework.test import APITestCase
from energy_composition.models import EnergyComposition, ApportiomentComposition


# Create your tests here.

class EnergyTest(APITestCase):
    #loads fixtures dependencies
    fixtures = [
        # 'core/fixtures/initial_data_dxc.json', 'company/fixtures/initial_data_dxc.json',
        # 'agents/fixtures/initial_data_dxc.json', 'profiles/fixtures/initial_data_dxc.json', 
        # 'organization/fixtures/initial_data_dxc.json', 'gauge_point/fixtures/initial_data_dxc.json',
        # 'energy_composition/fixtures/initial_data_dxc.json', 'assets/fixtures/initial_data_dxc.json'
    ]


    def test_post_energy(self):
        #test create
        url = '/energy_composition-api/session_energy_composition_post/'
        
        expected={
            "composition_name": "teste unitario",
            "cost_center": "526",
            "id_company": 10089,
            "id_business": "",
            "id_director": "",
            "id_segment": "",
            "id_accountant": "",
            "kpi_formulae": "{'id':'326','key':'A'}-12",
            "profit_center": "4147",
            "composition_loss": "12.00",
            "description": "Teste",
            "id_gauge_point_destination": 10066,
            "apport_energy_composition": [
                {
                    "id_company": 10089,
                    "volume_code": "10",
                    "cost_code": ""
                },
                {
                    "id_company": 10089,
                    "volume_code": "98548",
                    "cost_code": "112"
                }
            ],
            "point_energy_composition": [
                {
                    "id_gauge": 10065
                }
            ],
            "isValidFormula": True,
            "status": "S"
        }
        response = self.client.post(url, expected, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_update_energy(self):
        # exists
        energy_composition = EnergyComposition.objects.filter().last()

        urlGet = '/energy_composition-api/session_energy_composition/%s/' % energy_composition.pk        
        urlPut = '/energy_composition-api/session_energy_composition_put/%s/' % energy_composition.pk

        response = self.client.get(urlGet)
        response = self.client.put(urlPut, response.data, format='json')
        self.assertTrue(status.is_success(response.status_code))

        urlGet = '/energy_composition-api/session_energy_composition/%s/' % 71       
        urlPut = '/energy_composition-api/session_energy_composition_put/%s/' % 71

        response = self.client.get(urlGet)
        json_params=response.data
        json_params['apport_energy_composition']=[json_params['apport_energy_composition'][0], json_params['apport_energy_composition'][0] ]
        response = self.client.put(urlPut, json_params, format='json')
        self.assertTrue(status.is_success(response.status_code))
        
        # put bad request
        response = self.client.put(urlPut,{},format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        #error status
        energy_composition = EnergyComposition.objects.filter(apport_energy_composition__isnull=False, point_energy_composition__isnull=False).last()

        urlGet = '/energy_composition-api/session_energy_composition/%s/' % energy_composition.pk        
        urlPut = '/energy_composition-api/session_energy_composition_put/%s/' % energy_composition.pk
        response = self.client.get(urlGet)
        json_params=response.data
        json_params['status']="N"
        response = self.client.put(urlPut, json_params, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        

        # not found
        url = '/energy_composition-api/session_energy_composition/%s/' % 0
        response = self.client.get(url) 
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_detail(self):
        energy_obj=EnergyComposition.objects.last()
        urlGet='/energy_composition-api/session_energy_composition/%d/'%energy_obj.pk
        response = self.client.get(urlGet, format='json')
        self.assertTrue(status.is_success(response.status_code))

    def test_find_energy(self):
        url_find = '/energy_composition-api/session_energy_composition_get_find_basic/'
        response = self.client.get(url_find, format='json')
        self.assertTrue(status.is_success(response.status_code))

        #teste Find
        url_find = '/energy_composition-api/session_energy_composition/?composition_name=Alegria&cost_center=1120134'
        response = self.client.get(url_find, format='json')
        self.assertTrue(status.is_success(response.status_code))

    def test_log_energy_composition(self):
        energy_obj=EnergyComposition.objects.filter(id_energy_composition=79).last()
        url='/energy_composition-api/session_log_basic_composition/%d/'%energy_obj.pk
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

        url='/energy_composition-api/session_log_basic_composition/%d/'%79
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

    def test_export_file(self):
        url_find = '/energy_composition-api/session_energy_composition_file/?composition_name=Alegria&cost_center=1120134&format_file=csv'
        response = self.client.get(url_find)
        self.assertTrue(status.is_success(response.status_code))

        url_find = '/energy_composition-api/session_energy_composition_file/?format_file=csv'
        response = self.client.get(url_find)
        self.assertTrue(status.is_success(response.status_code))
        url_find = '/energy_composition-api/session_energy_composition_file/?format_file=xlsx'
        response = self.client.get(url_find)
        self.assertTrue(status.is_success(response.status_code))

        #ERROR
        url_find='/energy_composition-api/session_energy_composition_file/?composition_name=Alegria&cost_center=1120134'
        response = self.client.get(url_find)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        #ERROR
        url_find='/energy_composition-api/session_energy_composition_file/?format_file=error'
        response = self.client.get(url_find)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_validate_status_none(self):
        from ..serializers import validate_status
        self.assertEqual(validate_status(None, None, None), "S")


