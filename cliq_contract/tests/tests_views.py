from rest_framework import status
from rest_framework.test import APITestCase
from energy_contract.models import EnergyContract
from cliq_contract.models import CliqContract, Seasonality, SeasonalityCliq

def transform_data_requestGet_in_requestPut(requestGet):
    json_formated={}
    json_formated['cliqcontract']=requestGet['id_contract']
    json_formated['cliqcontract']['id_vendor_profile']= requestGet['id_vendor_profile']['id_profile']
    json_formated['cliqcontract']['id_buyer_profile']= requestGet['id_buyer_profile']['id_profile']
    json_formated['cliqcontract']['id_submarket']= requestGet['id_submarket']['id_submarket']
    array_seasonality=[]
    for item_json in requestGet['seasonality_cliq_details']:
        array_seasonality.append(item_json['seasonality_detail'])
    json_formated['seasonality']=array_seasonality

    requestGet.pop('id_contract')
    requestGet.pop('id_submarket')
    requestGet.pop('seasonality_cliq_details')
    requestGet.pop('id_vendor_profile')
    requestGet.pop('id_buyer_profile')

    json_formated['cliqcontract'].update(requestGet)
    return json_formated

class CliqContractTest(APITestCase):
    # loads fixtures dependencies
    # fixtures = [
    #     'core/fixtures/initial_data_dxc.json', 'company/fixtures/initial_data_dxc.json',
    #     'agents/fixtures/initial_data_dxc.json', 'profiles/fixtures/initial_data_dxc.json', 
    #     'organization/fixtures/initial_data_dxc.json', 'gauge_point/fixtures/initial_data_dxc.json',
    #     'energy_composition/fixtures/initial_data_dxc.json', 'assets/fixtures/initial_data_dxc.json', 
    #     'asset_items/fixtures/initial_data_dxc.json', 'energy_contract/fixtures/initial_data_dxc.json', 
    #     'cliq_contract/fixtures/initial_data_dxc.json'
    # ]

    def test_get(self):
        url = '/cliq_contract-api/session_cliq_contract/'
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

        cliq_obj=CliqContract.objects.last()
        url='/cliq_contract-api/session_view_max_value_contract/%s/'%cliq_obj.id_contract_id
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))
        
    def test_get_find(self):
        url_find = '/cliq_contract-api/session_cliq_contract/?page_size=2'
        response = self.client.get(url_find, format='json')
        self.assertTrue(status.is_success(response.status_code))

        url_find = '/cliq_contract-api/session_cliq_contract/?page_size=25&ordering=transaction_type'
        response = self.client.get(url_find, format='json')
        self.assertTrue(status.is_success(response.status_code))

        url_find = '/cliq_contract-api/session_cliq_contract/?contract_name=XXX_V,V_AV_AC_Di_Df_Z&cliq_contract=123456&    \
                                                            buyer_profile=Juliana&vendor_profile=Matheus%20M.&transaction_type=prdd'
        response = self.client.get(url_find, format='json')
        self.assertTrue(status.is_success(response.status_code))                                                        

    def test_get_detail(self):
        cliq_contract = CliqContract.objects.all().first()
        url = '/cliq_contract-api/session_cliq_contract/%s/' % cliq_contract.pk
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))
        # not found
        url = '/cliq_contract-api/session_cliq_contract/%s/' % 0
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_log_cliq(self):
        cliq_contract = CliqContract.objects.filter(seasonalityCliq_cliqContract__isnull=False).last()
        url = '/cliq_contract-api/session_log_basic_cliq_contract/%s/' % cliq_contract.pk
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

        cliq_contract = CliqContract.objects.filter(id_buyer_asset_items__isnull=False).last()
        url = '/cliq_contract-api/session_log_basic_cliq_contract/%s/' % cliq_contract.pk
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

        cliq_contract = CliqContract.objects.filter(id_buyer_assets__isnull=False).last()
        url = '/cliq_contract-api/session_log_basic_cliq_contract/%s/' % cliq_contract.pk
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

    def test_file_csv(self):
        url_find = '/cliq_contract-api/session_cliq_contract_export_file/?format_file=csv'
        response = self.client.get(url_find)
        self.assertTrue(status.is_success(response.status_code))

        url_find = '/cliq_contract-api/session_cliq_contract_export_file/?format_file=xlsx'
        response = self.client.get(url_find)
        self.assertTrue(status.is_success(response.status_code))


        url_find = '/cliq_contract-api/session_cliq_contract_export_file/?contract_name=XXX_V,V_AV_AC_Di_Df_Z&cliq_contract=123456&    \
                                                            buyer_profile=Juliana&vendor_profile=Matheus%20M.&transaction_type=prdd&format_file=csv'
        response = self.client.get(url_find)
        self.assertTrue(status.is_success(response.status_code))

        #ERROR
        url_find = '/cliq_contract-api/session_cliq_contract_export_file/'
        response = self.client.get(url_find)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        url_find = '/cliq_contract-api/session_cliq_contract_export_file/?format_file=error'
        response = self.client.get(url_find)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post(self):
        urlPost='/cliq_contract-api/session_cliq_contract_post/'
        energyContract_obj = EnergyContract.objects.filter(volume_mwm__gt=1, cliq_contract__isnull=True).last()
        json_params={
            "cliqcontract": {
                "id_ccee": {
                    "code_ccee": "52818518188"
                },
                "id_buyer_profile_validator": 161,
                "buyer_consumer_index_validator": "",
                "cliqsVolume": 1,
                "maxVolume": 122222,
                "modality": "Longo Prazo",
                "mwm_volume": 1,
                "ccee_type_contract": "CCEAL",
                "transaction_type": "BALANCEADO",
                "id_buyer_profile": 161,
                "id_vendor_profile": 206,
                "contractual_loss": "285.0000",
                "id_submarket": 6,
                "id_contract": energyContract_obj.pk,
                "id_buyer_assets": None,
                "id_buyer_asset_items": None,
                "status": "S"
            },
            "seasonality": [
                {
                    "year": "2012",
                    "measure_unity": "PU",
                    "january": "12.000000",
                    "february": 0,
                    "march": 0,
                    "april": 0,
                    "may": 0,
                    "june": 0,
                    "july": 0,
                    "august": 0,
                    "september": 0,
                    "october": 0,
                    "november": 0,
                    "december": "0.000000",
                    "total": 12
                },
                {
                    "year": "2013",
                    "measure_unity": "PU",
                    "january": 0,
                    "february": 0,
                    "march": 0,
                    "april": 0,
                    "may": 0,
                    "june": 0,
                    "july": 0,
                    "august": 0,
                    "september": 0,
                    "october": 0,
                    "november": 0,
                    "december": "12.000000",
                    "total": 12
                }
            ]
        }
        response = self.client.post(urlPost, json_params, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        ##############modality = Transferencia
        energyContract_obj = EnergyContract.objects.filter(modality="Transferencia", volume_mwm__gt=1, cliq_contract__isnull=True, flexib_energy_contract__isnull=False).last()
        json_params={
            "cliqcontract": {
                "id_ccee": {
                    "code_ccee": "8416514"
                },
                "id_buyer_profile_validator": 161,
                "buyer_consumer_index_validator": "",
                "cliqsVolume": 1,
                "maxVolume": 122222,
                "modality": "Longo Prazo",
                "mwm_volume": 1,
                "ccee_type_contract": "CCEAL",
                "transaction_type": "BALANCEADO",
                "id_buyer_profile": 161,
                "id_vendor_profile": 206,
                "contractual_loss": "285.0000",
                "id_submarket": 6,
                "id_contract": energyContract_obj.pk,
                "id_buyer_assets": None,
                "id_buyer_asset_items": None,
                "status": "S"
            },
            "seasonality": []
        }
        response = self.client.post(urlPost, json_params, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_post_error(self):
        ####Error year duplicate
        urlPost='/cliq_contract-api/session_cliq_contract_post/'
        energyContract_obj = EnergyContract.objects.filter(volume_mwm__gt=1, cliq_contract__isnull=True).last()
        json_params={
            "cliqcontract": {
                "id_ccee": {
                    "code_ccee": "52818518188"
                },
                "id_buyer_profile_validator": 161,
                "buyer_consumer_index_validator": "",
                "cliqsVolume": 1,
                "maxVolume": 122222,
                "modality": "Longo Prazo",
                "mwm_volume": 1,
                "ccee_type_contract": "CCEAL",
                "transaction_type": "BALANCEADO",
                "id_buyer_profile": 161,
                "id_vendor_profile": 206,
                "contractual_loss": "285.0000",
                "id_submarket": 6,
                "id_contract": energyContract_obj.pk,
                "id_buyer_assets": None,
                "id_buyer_asset_items": None,
                "status": "S"
            },
            "seasonality": [
                {
                    "year": "2012",
                    "measure_unity": "PU",
                    "january": "12.000000",
                    "february": 0,
                    "march": 0,
                    "april": 0,
                    "may": 0,
                    "june": 0,
                    "july": 0,
                    "august": 0,
                    "september": 0,
                    "october": 0,
                    "november": 0,
                    "december": "0.000000",
                    "total": 12
                },
                {
                    "year": "2012",
                    "measure_unity": "PU",
                    "january": 0,
                    "february": 0,
                    "march": 0,
                    "april": 0,
                    "may": 0,
                    "june": 0,
                    "july": 0,
                    "august": 0,
                    "september": 0,
                    "october": 0,
                    "november": 0,
                    "december": "12.000000",
                    "total": 12
                }
            ]
        }
        response = self.client.post(urlPost, json_params, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


        energyContract_obj = EnergyContract.objects.filter(volume_mwm__gt=1, cliq_contract__isnull=False).last()
        json_params={
            "cliqcontract": {
                "id_ccee": {
                    "code_ccee": "52818518188"
                },
                "id_buyer_profile_validator": 161,
                "buyer_consumer_index_validator": "",
                "cliqsVolume": 1,
                "maxVolume": 122222,
                "modality": "Longo Prazo",
                "mwm_volume": energyContract_obj.volume_mwm*100000,
                "ccee_type_contract": "CCEAL",
                "transaction_type": "BALANCEADO",
                "id_buyer_profile": 161,
                "id_vendor_profile": 206,
                "contractual_loss": "285.0000",
                "id_submarket": 6,
                "id_contract": energyContract_obj.pk,
                "id_buyer_assets": None,
                "id_buyer_asset_items": None,
                "status": "S"
            },
            "seasonality": []
        }
        response = self.client.post(urlPost, json_params, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put(self):
        cliq_contract= CliqContract.objects.filter(seasonalityCliq_cliqContract__isnull=False).select_related('id_contract').last()
        urlGet = '/cliq_contract-api/session_cliq_contract/%s/' %cliq_contract.pk
        urlPut = '/cliq_contract-api/session_cliq_contract_put/%s/' %cliq_contract.pk

        response = self.client.get(urlGet, format='json')
        json_params=transform_data_requestGet_in_requestPut(response.data)
        json_params['seasonality'].append( {
            "year": 1968,
            "measure_unity": "PU",
            "january": "1.000000000",
            "february": "1.000000000",
            "march": "1.000000000",
            "april": "1.000000000",
            "may": "1.000000000",
            "june": "1.000000000",
            "july": "1.000000000",
            "august": "1.000000000",
            "september": "1.000000000",
            "october": "1.000000000",
            "november": "1.000000000",
            "december": "1.000000000",
            "total": 12
        } )
        json_params['seasonality'].append( {
            "id_seasonality":0,
            "year": 1969,
            "measure_unity": "PU",
            "january": "1.000000000",
            "february": "1.000000000",
            "march": "1.000000000",
            "april": "1.000000000",
            "may": "1.000000000",
            "june": "1.000000000",
            "july": "1.000000000",
            "august": "1.000000000",
            "september": "1.000000000",
            "october": "1.000000000",
            "november": "1.000000000",
            "december": "1.000000000",
            "total": 12
        } )
        response = self.client.put(urlPut, json_params, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)



        response = self.client.get(urlGet, format='json')
        json_params=transform_data_requestGet_in_requestPut(response.data)
        json_params['seasonality']=[]
        response = self.client.put(urlPut, json_params, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)



        cliq_contract= CliqContract.objects.filter(seasonalityCliq_cliqContract__isnull=False, id_contract__modality="Transferencia").select_related('id_contract').last()
        urlGet = '/cliq_contract-api/session_cliq_contract/%s/' %cliq_contract.pk
        urlPut = '/cliq_contract-api/session_cliq_contract_put/%s/' %cliq_contract.pk

        response = self.client.get(urlGet, format='json')
        json_params=transform_data_requestGet_in_requestPut(response.data)
        json_params['cliqcontract']['submarket']=True
        response = self.client.put(urlPut, json_params, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(urlGet, format='json')
        json_params=transform_data_requestGet_in_requestPut(response.data)
        json_params['cliqcontract']['status']="N"
        response = self.client.put(urlPut, json_params, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_put_error(self):
        cliq_contract= CliqContract.objects.filter(seasonalityCliq_cliqContract__isnull=False).select_related('id_contract').last()
        urlGet = '/cliq_contract-api/session_cliq_contract/%s/' %cliq_contract.pk
        urlPut = '/cliq_contract-api/session_cliq_contract_put/%s/' %cliq_contract.pk

        response = self.client.get(urlGet, format='json')
        json_params=transform_data_requestGet_in_requestPut(response.data)
        json_params['cliqcontract']['mwm_volume']= cliq_contract.id_contract.volume_mwm*100000
        response = self.client.put(urlPut, json_params, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        ###---error year duplicate
        response = self.client.get(urlGet, format='json')
        json_params=transform_data_requestGet_in_requestPut(response.data)
        json_params['seasonality'].append( json_params['seasonality'][0] )
        response = self.client.put(urlPut, json_params, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)



        urlPut = '/cliq_contract-api/session_cliq_contract_put/%s/' %0
        response = self.client.put(urlPut, json_params, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # print("\n\n\n")
        # print(response.data)
        # print("\n\n\n")

    def test_download_template(self):
        url = '/cliq_contract-api/session_cliq_contract_modulation_template'
        response = self.client.get(url)
        self.assertTrue(status.is_success(response.status_code))