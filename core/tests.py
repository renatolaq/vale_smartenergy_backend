from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest import mock
from .views import delete_file, requests
from asset_items.models import AssetItems

request_return = type('', (object,), {})()
request_return.text = "TOKEN"
request_return.META = []

class CoreTests(APITestCase):
    @mock.patch.object(requests, "get", mock.Mock(return_value=request_return))
    @mock.patch.object(requests, "post", mock.Mock(return_value=request_return))
    @mock.patch("core.views.PME_APP_HOST", "")
    @mock.patch("core.views.PME_APP_URL", "")
    def test_get_token_pme(self):
        # Ensure we can login on PME with a valid user
        data = {'UserName': "80f8c9cf4f4ccf4dc38e80f8c9cf4f4c",  # C0464545
                'AccessLevel': str(5),
                'Groups': ["Global"]}

        response = self.client.post('/core-api/get_pme_token/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertEqual(response.data, data)

    @mock.patch.object(requests, "post", mock.Mock(return_value=request_return))
    @mock.patch("core.views.PME_APP_HOST", "")
    def test_change_lang_pme(self):
        # Ensure we can change PME user language
        data = {'UserName': "80f8c9cf4f4ccf4dc38e80f8c9cf4f4c",  # C0464545
                'Language': "eng"}

        response = self.client.post('/core-api/change_lang_pme/eng', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @mock.patch.object(requests, "post", mock.Mock(return_value=request_return))
    @mock.patch("core.views.PME_APP_HOST", "")
    def test_logout_pme(self):

        # Ensure we can logout PME
        url = '/core-api/logout_pme/'
        data = {'UserName': "80f8c9cf4f4ccf4dc38e80f8c9cf4f4c"}  # C0464545

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_general_log(self):
        from .views import generic_log_search, generic_log_search_basic
        from asset_items.models import SeasonalityAssetItemCost, Seasonality, SeasonalityAssetItem, SeazonalityAssetItemDepreciation

        kwargs = {'core': AssetItems, 'core_pk': 'id_asset_items', 'core+': [],
              'child': []}
        log = generic_log_search(1, **kwargs)

        #Generate seasonality
        array = []
        kwargs = {'core': SeasonalityAssetItemCost, 'core_pk': 'id_seasonality_asset_item_cost',
                'core+': [{Seasonality: 'id_seazonality_asset'}],
                'child': []}
        for a in SeasonalityAssetItemCost.objects.filter(id_asset_items=1):
            array.append(generic_log_search(a.id_seasonality_asset_item_cost, **kwargs))

        kwargs = {'core': SeasonalityAssetItem, 'core_pk': 'id_seasonality_asset_item',
                'core+': [{Seasonality: 'id_seasonality'}],
                'child': []}
        for a in SeasonalityAssetItem.objects.filter(id_asset_items=1):
            array.append(generic_log_search(a.id_seasonality_asset_item, **kwargs))

        kwargs = {'core': SeazonalityAssetItemDepreciation, 'core_pk': 'seazonality_asset_depreciation',
                'core+': [{Seasonality: 'id_seasonality'}],
                'child': []}
        for a in SeazonalityAssetItemDepreciation.objects.filter(id_asset_items=1):
            array.append(generic_log_search(a.seazonality_asset_depreciation, **kwargs))

        kwargs = log.copy()
        new_seasonality = []    
        for index in range(len(array)):
            if 'seasonality' in array[index]:
                for intern_index in range(len(array[index]['seasonality'])):
                    new_seasonality.append(array[index]['seasonality'][intern_index])
        
        kwargs['SEASONALITY'] = new_seasonality
        
        kwargsAux=generic_log_search_basic(kwargs)
        self.assertIsNotNone(kwargsAux)    

    def test_generic_update(self):
        from .serializers import generic_update
        from agents.models import Agents, CceeDescription
        from agents.serializers import validate_status
        from SmartEnergy.auth.IAM_test import IAMTestAuthentication

        instance = Agents.objects.get(pk=10018)
        result = self.client.get("/agents-api/session_agents/10018/", format='json')
        validated_data = result.data
        
        user, userinfo = IAMTestAuthentication().authenticate(None)
        ccee_agent_data = validated_data.pop('ccee_agent')
        agent = instance.id_ccee
        validate_status(agent.pk, dict(ccee_agent_data)['status'], self)
        generic_update(CceeDescription, instance.id_ccee.pk, dict(validated_data), user)

    def test_generic_insert(self):
        from agents.models import CceeDescription, Agents
        from SmartEnergy.auth.IAM_test import IAMTestAuthentication
        from .serializers import log

        validated_data = {
            "code_ccee":"123460",
            "name_ccee":"teste",
            "type": "A/P",
            "status": "S",
            "ccee_agent":
            {
                "id_company_id": 10089,
                "vale_name_agent":"testeteste"
            }
        }
        user, userinfo = IAMTestAuthentication().authenticate(None)

        ccee_agents_data = validated_data.pop('ccee_agent')
        ccee = CceeDescription.objects.create(**validated_data)
        log(CceeDescription, ccee.id_ccee, {}, ccee, user, "", action="INSERT")
        agent = Agents.objects.create(id_ccee=ccee, **ccee_agents_data)
        log(Agents, agent.id_agents, {}, agent, user, "", action="INSERT")

        
    def test_get_peek_time(self):
        response = self.client.get('/core-api/peek_time/2020/1/1', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_validate_cceecode(self):        
        response = self.client.get('/core-api/validated_code_ccee/12345/A.P/', format='json', HTTP_ACCEPT_LANGUAGE="pt")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get('/core-api/validated_code_ccee/14755/A.P/', format='json', HTTP_ACCEPT_LANGUAGE="pt")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_file_export(self):
        response = self.client.get('/agents-api/session_agents_file/', data={"format_file": "csv"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get('/agents-api/session_agents_file/', data={"format_file": "pdf"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get('/agents-api/session_agents_file/', data={"format_file": "xlsx"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_core_virtual_meters(self):
        pass

    def test_core_meters_operations(self):
        from energy_composition.models import EnergyComposition

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

        
        energy_composition = EnergyComposition.objects.filter(id_gauge_point_destination__isnull=False, apport_energy_composition__isnull=False, point_energy_composition__isnull=False).last()

        urlGet = '/energy_composition-api/session_energy_composition/%s/' % energy_composition.pk        
        urlPut = '/energy_composition-api/session_energy_composition_put/%s/' % energy_composition.pk

        response = self.client.get(urlGet)
        response.data['kpi_formulae'] = "{'id':'326','key':'A'}+{'id':'327','key':'B'}+{'id':'327','key':'C'}-12"
        response = self.client.put(urlPut, response.data, format='json')
        self.assertTrue(status.is_success(response.status_code))

        response = self.client.get(urlGet)
        response.data['kpi_formulae'] = "{'id':'326','key':'A'}-12"
        response = self.client.put(urlPut, response.data, format='json')
        self.assertTrue(status.is_success(response.status_code))

        urlGet = '/energy_composition-api/session_energy_composition/%s/' % 71       
        urlPut = '/energy_composition-api/session_energy_composition_put/%s/' % 71

        response = self.client.get(urlGet)
        json_params=response.data
        json_params['apport_energy_composition']=[json_params['apport_energy_composition'][0], json_params['apport_energy_composition'][0] ]
        response = self.client.put(urlPut, json_params, format='json')
        self.assertTrue(status.is_success(response.status_code))
        
        urlGet = '/energy_composition-api/session_energy_composition/%s/' % energy_composition.pk        
        urlPut = '/energy_composition-api/session_energy_composition_put/%s/' % energy_composition.pk
        response = self.client.get(urlGet)
        json_params=response.data
        json_params['status']="N"
        response = self.client.put(urlPut, json_params, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_time_operations(self):
        from .serializers import is_valid_str_time, str_time_to_seconds, seconds_to_str_time

        self.assertTrue(is_valid_str_time("1:00:55"))
        self.assertFalse(is_valid_str_time("00:55"))
        self.assertFalse(is_valid_str_time("A1:A0:55"))

        self.assertEqual(str_time_to_seconds("00:00:55"), 55)

        self.assertEqual(seconds_to_str_time(55), "0:00:55")

    def test_generic_validation_changed(self):
        from .serializers import generic_validation_changed
        from company.models import Company
        from energy_composition.models import EnergyComposition
        from agents.models import Agents
        from asset_items.models import AssetItems
        from gauge_point.models import GaugePoint, GaugeEnergyDealership
        from assets.models import Assets

        request = type('', (object,), {})()
        request.META = []
        kwargs = {Agents: 'id_company'}
        self.assertNotEqual(generic_validation_changed(10089, Company, kwargs, request), "S")
        self.assertEqual(generic_validation_changed(20255, Company, kwargs, request), "S")


    def test_generic_detail_log(self):
        from .views import generic_log_search, generic_detail_log
        from agents.models import Agents, CceeDescription, Company
        kwargs = {
            'core': Agents, 
            'core_pk': 'id_agents', 
            'core+': [{CceeDescription: 'id_ccee'}],
            'child': []
        }
        kwargs2 = {
            'core': [Agents], 
            'core_pk': 'id_agents', 
            'core+': [{CceeDescription: 'id_ccee'}],
            'child': [], 
            'search': {"id_company": {Company:"id_company"}},
            'search_dependent': [{CceeDescription:"id_ccee"}]
        }
    
        generic_detail_log(kwargs2, generic_log_search(10020, **kwargs))

    def test_alter_number(self):
        from .views import alter_number

        self.assertEqual(alter_number("1001.254"), "1.001,254")
        self.assertEqual(alter_number("100.000"), "100,000")
        self.assertEqual(alter_number(""), "")

    def test_save_file(self):
        from .views import save_file
        from io import BytesIO

        file = BytesIO(b"\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x01\x01\x01")
        file.name = "memory.bin"
        save_file(file)


    def test_delete_file(self):
        from .views import save_file
        from io import BytesIO

        file = BytesIO(b"\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x01\x01\x01")
        file.name = "memory.bin"
        locate = save_file(file)

        delete_file(locate)