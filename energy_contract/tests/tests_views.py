from rest_framework import status
from rest_framework.test import APITestCase
from energy_contract.models import EnergyContract

# Create your tests here.


class EnergyContractTest(APITestCase):
    # loads fixtures dependencies
    # fixtures = [
    #     'core/fixtures/initial_data_dxc.json', 'company/fixtures/initial_data_dxc.json',
    #     'agents/fixtures/initial_data_dxc.json', 'profiles/fixtures/initial_data_dxc.json', 
    #     'organization/fixtures/initial_data_dxc.json', 'gauge_point/fixtures/initial_data_dxc.json',
    #     'energy_composition/fixtures/initial_data_dxc.json', 'assets/fixtures/initial_data_dxc.json', 
    #     'asset_items/fixtures/initial_data_dxc.json', 'energy_contract/fixtures/initial_data_dxc.json', 
    #     'cliq_contract/fixtures/initial_data_dxc.json'
    # ]


    def test_valid_contract(self):
        url = '/energy-contract-api/session_valid_contract_name/CCI_1.0_2411300 AG VALE REP CONS_2411300 AG VALE REP CONS_1021/' #ok nunca criado
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

        url = '/energy-contract-api/session_valid_contract_name/CCE_0,0_VALE ENERGIA_VALE_0119_1221_7/'# ok (Dois depois)
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

        energy_obj = EnergyContract.objects.filter(contract_name__isnull=False,status="S").exclude(contract_name="").last()
        url = '/energy-contract-api/session_valid_contract_name/%s/?id_contract=%d' %(energy_obj.contract_name, energy_obj.pk)# ok (entre dois existentes)
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))
        
        #Error
        url = '/energy-contract-api/session_valid_contract_name/CVE_1,0_VALE_ENERGISA COM_0521_2/'##Dois depois do nunca criado
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        url = '/energy-contract-api/session_valid_contract_name/CVE_1,0_VALE_ENERGISA COM_0520/'#equal
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        url = '/energy-contract-api/session_valid_contract_name/CVE_1,0_VALE_ENERGISA COM_0520_4/'#Dois depois
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get(self):
        url = '/energy-contract-api/session_energy_contract/'
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

        url = '/energy-contract-api/session_energy_contract_find_basic/'
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

        url = '/energy-contract-api/get_data_agents_basic/'
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

        url = '/energy-contract-api/get_data_profile_basic/'
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

        url = '/energy-contract-api/list_energy_contract/'
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

        url = '/energy-contract-api/session_energy_contract/?modality=Lon'
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

        url = '/energy-contract-api/get_energy_product/'

        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

        url='/energy-contract-api/show_variable/'
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

        url='/energy-contract-api/session_energy_contract_attachment/'
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

    def test_log(self):
        energy_obj=EnergyContract.objects.filter(id_contract=84).last()
        url = '/energy-contract-api/session_log_basic_energy_contract/%d/' %energy_obj.pk
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

        energy_obj=EnergyContract.objects.filter(id_buyer_profile__isnull=False).last()
        url = '/energy-contract-api/session_log_basic_energy_contract/%d/' %energy_obj.pk
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))
        energy_obj=EnergyContract.objects.filter(id_seller_profile__isnull=False).last()
        url = '/energy-contract-api/session_log_basic_energy_contract/%d/' %energy_obj.pk
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

    def test_file_energy_Contract_csv(self):
        url='/energy-contract-api/session_energy_contract_file/?modality=Curto%20Prazo&sap_contract=5546368184519452&type=C&buyer_agents=Jackeline&seller_agents=Matheus&status=S&format_file=csv'
        response = self.client.get(url)
        self.assertTrue(status.is_success(response.status_code))
        url='/energy-contract-api/session_energy_contract_file/?format_file=csv'
        response = self.client.get(url)
        self.assertTrue(status.is_success(response.status_code))
        url='/energy-contract-api/session_energy_contract_file/?format_file=xlsx'
        response = self.client.get(url)
        self.assertTrue(status.is_success(response.status_code))
        #ERROR
        url='/energy-contract-api/session_energy_contract_file/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        url='/energy-contract-api/session_energy_contract_file/?format_file=error'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post(self):
        url = '/energy-contract-api/session_energy_contract_post/'
        expected = {
            "id_buyer_agents": 10055,
            "id_seller_agents": 10055,
            "id_buyer_profile": "",
            "id_seller_profile": "",
            "id_energy_product": 1,
            "modality": "Longo Prazo",
            "type": "C",
            "start_supply": "01/07/2020",
            "end_supply": "31/07/2020",
            "contract_status": "AS",
            "signing_data": "01/01/2020",
            "volume_mwm": "10.000000",
            "volume_mwh": "7440.000",
            "contract_name": "CCE_10,0_AMERICA_AMERICA_0720_0720",
            "buyer_agents_detail": {
                "id_agents": "",
                "vale_name_agent": ""
            },
            "seller_agents_detail": {
                "id_agents": "",
                "vale_name_agent": ""
            },
            "buyer_profile_detail": {
                "id_profile": "",
                "name_profile": ""
            },
            "seller_profile_detail": {
                "id_profile": "",
                "name_profile": ""
            },
            "product": {
                "id_energy_product": "",
                "description": ""
            },
            "precif_energy_contract": {
                "id_variable": 1,
                "active_price_mwh": "100.0000",
                "base_price_mwh": "100.0000",
                "base_price_date": "01/07/2020",
                "birthday_date": "01/07/2020",
                "retusd": None
            },
            "flexib_energy_contract": {
                "flexibility_type": "Flat",
                "id_flexibilization_type": 1,
                "min_flexibility_pu_peak": None,
                "max_flexibility_pu_peak": None,
                "min_flexibility_pu_offpeak": None,
                "max_flexibility_pu_offpeak": None,
                "proinfa_flexibility": "N"
            },
            "modulation_energy_contract": {
                "modulation_type": "Flat",
                "min_modulation_pu": None,
                "max_modulation_pu": None
            },
            "season_energy_contract": {
                "type_seasonality": "Flat",
                "season_min_pu": None,
                "season_max_pu": None
            },
            "guaran_energy_contract": {
                "month_hour": "1",
                "guaranteed_value": "1.0000",
                "emission_date": "01/01/2020",
                "effective_date": "01/01/2020"
            },
            "file_toUpload": [

            ],
            "market": True,
            "activeStep": 0,
            "edit": True,
            "validation": {
                "touched": {
                    "id_buyer_agents": True,
                    "id_seller_agents": True,
                    "id_buyer_profile": True,
                    "id_seller_profile": True,
                    "id_energy_product": True,
                    "modality": True,
                    "type": True,
                    "start_supply": True,
                    "end_supply": True,
                    "contract_status": True,
                    "signing_data": True,
                    "volume_mwm": True,
                    "volume_mwh": True,
                    "contract_name": True,
                    "buyer_agents_detail": {
                        "id_agents": True,
                        "vale_name_agent": True
                    },
                    "seller_agents_detail": {
                        "id_agents": True,
                        "vale_name_agent": True
                    },
                    "buyer_profile_detail": {
                        "id_profile": True,
                        "name_profile": True
                    },
                    "seller_profile_detail": {
                        "id_profile": True,
                        "name_profile": True
                    },
                    "product": {
                        "id_energy_product": True,
                        "description": True
                    },
                    "precif_energy_contract": {
                        "id_variable": True,
                        "active_price_mwh": True,
                        "base_price_mwh": True,
                        "base_price_date": True,
                        "birthday_date": True,
                        "retusd": True
                    },
                    "flexib_energy_contract": {
                        "flexibility_type": True,
                        "id_flexibilization_type": True,
                        "min_flexibility_pu_peak": True,
                        "max_flexibility_pu_peak": True,
                        "min_flexibility_pu_offpeak": True,
                        "max_flexibility_pu_offpeak": True,
                        "proinfa_flexibility": True
                    },
                    "modulation_energy_contract": {
                        "modulation_type": True,
                        "min_modulation_pu": True,
                        "max_modulation_pu": True
                    },
                    "season_energy_contract": {
                        "type_seasonality": True,
                        "season_min_pu": True,
                        "season_max_pu": True
                    },
                    "guaran_energy_contract": {
                        "month_hour": True,
                        "guaranteed_value": True,
                        "emission_date": True,
                        "effective_date": True
                    },
                    "file_toUpload": [

                    ],
                    "market": True,
                    "activeStep": True,
                    "edit": True,
                    "validation": {
                        "touched": {
                            "modality": True,
                            "id_buyer_agents": True,
                            "type": True,
                            "id_seller_agents": True,
                            "start_supply": True,
                            "end_supply": True,
                            "volume_mwm": True,
                            "id_energy_product": True,
                            "contract_name": True,
                            "contract_status": True,
                            "signing_data": True,
                            "precif_energy_contract": {
                                "base_price_mwh": True,
                                "base_price_date": True,
                                "birthday_date": True,
                                "id_variable": True,
                                "active_price_mwh": True
                            },
                            "flexib_energy_contract": {
                                "flexibility_type": True
                            },
                            "modulation_energy_contract": {
                                "modulation_type": True
                            },
                            "season_energy_contract": {
                                "type_seasonality": True
                            },
                            "guaran_energy_contract": {
                                "month_hour": True,
                                "guaranteed_value": True,
                                "emission_date": True,
                                "effective_date": True
                            }
                        },
                        "errors": {

                        }
                    },
                    "sap_contract": True,
                    "contract_base_value": True
                },
                "errors": {

                }
            },
            "sap_contract": "1234567890",
            "contract_base_value": "744000.0000"
        }
        response = self.client.post(url, expected, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        #BAD_REQUEST data de assinatura
        expected = {
            "id_buyer_agents": 10055,
            "id_seller_agents": 10055,
            "id_buyer_profile": "",
            "id_seller_profile": "",
            "id_energy_product": 1,
            "modality": "Longo Prazo",
            "type": "C",
            "start_supply": "01/07/2020",
            "end_supply": "31/07/2020",
            "contract_status": "AS",
            "signing_data": None,
            "volume_mwm": "10.000000",
            "volume_mwh": "7440.000",
            "contract_name": "CCE_10,0_AMERICA_AMERICA_0720_0720_001",
            "buyer_agents_detail": {
                "id_agents": "",
                "vale_name_agent": ""
            },
            "seller_agents_detail": {
                "id_agents": "",
                "vale_name_agent": ""
            },
            "buyer_profile_detail": {
                "id_profile": "",
                "name_profile": ""
            },
            "seller_profile_detail": {
                "id_profile": "",
                "name_profile": ""
            },
            "product": {
                "id_energy_product": "",
                "description": ""
            },
            "precif_energy_contract": {
                "id_variable": 1,
                "active_price_mwh": "100.0000",
                "base_price_mwh": "100.0000",
                "base_price_date": "01/07/2020",
                "birthday_date": "01/07/2020",
                "retusd": None
            },
            "flexib_energy_contract": {
                "flexibility_type": "Flat",
                "id_flexibilization_type": 1,
                "min_flexibility_pu_peak": None,
                "max_flexibility_pu_peak": None,
                "min_flexibility_pu_offpeak": None,
                "max_flexibility_pu_offpeak": None,
                "proinfa_flexibility": "N"
            },
            "modulation_energy_contract": {
                "modulation_type": "Flat",
                "min_modulation_pu": None,
                "max_modulation_pu": None
            },
            "season_energy_contract": {
                "type_seasonality": "Flat",
                "season_min_pu": None,
                "season_max_pu": None
            },
            "guaran_energy_contract": {
                "month_hour": "1",
                "guaranteed_value": "1.0000",
                "emission_date": "01/01/2020",
                "effective_date": "01/01/2020"
            },
            "file_toUpload": [

            ],
            "market": True,
            "activeStep": 0,
            "edit": True,
            "validation": {
                "touched": {
                    "id_buyer_agents": True,
                    "id_seller_agents": True,
                    "id_buyer_profile": True,
                    "id_seller_profile": True,
                    "id_energy_product": True,
                    "modality": True,
                    "type": True,
                    "start_supply": True,
                    "end_supply": True,
                    "contract_status": True,
                    "signing_data": True,
                    "volume_mwm": True,
                    "volume_mwh": True,
                    "contract_name": True,
                    "buyer_agents_detail": {
                        "id_agents": True,
                        "vale_name_agent": True
                    },
                    "seller_agents_detail": {
                        "id_agents": True,
                        "vale_name_agent": True
                    },
                    "buyer_profile_detail": {
                        "id_profile": True,
                        "name_profile": True
                    },
                    "seller_profile_detail": {
                        "id_profile": True,
                        "name_profile": True
                    },
                    "product": {
                        "id_energy_product": True,
                        "description": True
                    },
                    "precif_energy_contract": {
                        "id_variable": True,
                        "active_price_mwh": True,
                        "base_price_mwh": True,
                        "base_price_date": True,
                        "birthday_date": True,
                        "retusd": True
                    },
                    "flexib_energy_contract": {
                        "flexibility_type": True,
                        "id_flexibilization_type": True,
                        "min_flexibility_pu_peak": True,
                        "max_flexibility_pu_peak": True,
                        "min_flexibility_pu_offpeak": True,
                        "max_flexibility_pu_offpeak": True,
                        "proinfa_flexibility": True
                    },
                    "modulation_energy_contract": {
                        "modulation_type": True,
                        "min_modulation_pu": True,
                        "max_modulation_pu": True
                    },
                    "season_energy_contract": {
                        "type_seasonality": True,
                        "season_min_pu": True,
                        "season_max_pu": True
                    },
                    "guaran_energy_contract": {
                        "month_hour": True,
                        "guaranteed_value": True,
                        "emission_date": True,
                        "effective_date": True
                    },
                    "file_toUpload": [

                    ],
                    "market": True,
                    "activeStep": True,
                    "edit": True,
                    "validation": {
                        "touched": {
                            "modality": True,
                            "id_buyer_agents": True,
                            "type": True,
                            "id_seller_agents": True,
                            "start_supply": True,
                            "end_supply": True,
                            "volume_mwm": True,
                            "id_energy_product": True,
                            "contract_name": True,
                            "contract_status": True,
                            "signing_data": True,
                            "precif_energy_contract": {
                                "base_price_mwh": True,
                                "base_price_date": True,
                                "birthday_date": True,
                                "id_variable": True,
                                "active_price_mwh": True
                            },
                            "flexib_energy_contract": {
                                "flexibility_type": True
                            },
                            "modulation_energy_contract": {
                                "modulation_type": True
                            },
                            "season_energy_contract": {
                                "type_seasonality": True
                            },
                            "guaran_energy_contract": {
                                "month_hour": True,
                                "guaranteed_value": True,
                                "emission_date": True,
                                "effective_date": True
                            }
                        },
                        "errors": {

                        }
                    },
                    "sap_contract": True,
                    "contract_base_value": True
                },
                "errors": {

                }
            },
            "sap_contract": "1234567890",
            "contract_base_value": "744000.0000"
        }
        response = self.client.post(url, expected, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        #BAD_REQUEST contract name fora de ordem
        expected = {
            "id_buyer_agents": 10055,
            "id_seller_agents": 10055,
            "id_buyer_profile": "",
            "id_seller_profile": "",
            "id_energy_product": 1,
            "modality": "Longo Prazo",
            "type": "C",
            "start_supply": "01/07/2020",
            "end_supply": "31/07/2020",
            "contract_status": "AS",
            "signing_data": "01/01/2020",
            "volume_mwm": "10.000000",
            "volume_mwh": "7440.000",
            "contract_name": "CCE_10,0_AMERICA_AMERICA_0720_0720_005",
            "buyer_agents_detail": {
                "id_agents": "",
                "vale_name_agent": ""
            },
            "seller_agents_detail": {
                "id_agents": "",
                "vale_name_agent": ""
            },
            "buyer_profile_detail": {
                "id_profile": "",
                "name_profile": ""
            },
            "seller_profile_detail": {
                "id_profile": "",
                "name_profile": ""
            },
            "product": {
                "id_energy_product": "",
                "description": ""
            },
            "precif_energy_contract": {
                "id_variable": 1,
                "active_price_mwh": "100.0000",
                "base_price_mwh": "100.0000",
                "base_price_date": "01/07/2020",
                "birthday_date": "01/07/2020",
                "retusd": None
            },
            "flexib_energy_contract": {
                "flexibility_type": "Flat",
                "id_flexibilization_type": 1,
                "min_flexibility_pu_peak": None,
                "max_flexibility_pu_peak": None,
                "min_flexibility_pu_offpeak": None,
                "max_flexibility_pu_offpeak": None,
                "proinfa_flexibility": "N"
            },
            "modulation_energy_contract": {
                "modulation_type": "Flat",
                "min_modulation_pu": None,
                "max_modulation_pu": None
            },
            "season_energy_contract": {
                "type_seasonality": "Flat",
                "season_min_pu": None,
                "season_max_pu": None
            },
            "guaran_energy_contract": {
                "month_hour": "1",
                "guaranteed_value": "1.0000",
                "emission_date": "01/01/2020",
                "effective_date": "01/01/2020"
            },
            "file_toUpload": [

            ],
            "market": True,
            "activeStep": 0,
            "edit": True,
            "validation": {
                "touched": {
                    "id_buyer_agents": True,
                    "id_seller_agents": True,
                    "id_buyer_profile": True,
                    "id_seller_profile": True,
                    "id_energy_product": True,
                    "modality": True,
                    "type": True,
                    "start_supply": True,
                    "end_supply": True,
                    "contract_status": True,
                    "signing_data": True,
                    "volume_mwm": True,
                    "volume_mwh": True,
                    "contract_name": True,
                    "buyer_agents_detail": {
                        "id_agents": True,
                        "vale_name_agent": True
                    },
                    "seller_agents_detail": {
                        "id_agents": True,
                        "vale_name_agent": True
                    },
                    "buyer_profile_detail": {
                        "id_profile": True,
                        "name_profile": True
                    },
                    "seller_profile_detail": {
                        "id_profile": True,
                        "name_profile": True
                    },
                    "product": {
                        "id_energy_product": True,
                        "description": True
                    },
                    "precif_energy_contract": {
                        "id_variable": True,
                        "active_price_mwh": True,
                        "base_price_mwh": True,
                        "base_price_date": True,
                        "birthday_date": True,
                        "retusd": True
                    },
                    "flexib_energy_contract": {
                        "flexibility_type": True,
                        "id_flexibilization_type": True,
                        "min_flexibility_pu_peak": True,
                        "max_flexibility_pu_peak": True,
                        "min_flexibility_pu_offpeak": True,
                        "max_flexibility_pu_offpeak": True,
                        "proinfa_flexibility": True
                    },
                    "modulation_energy_contract": {
                        "modulation_type": True,
                        "min_modulation_pu": True,
                        "max_modulation_pu": True
                    },
                    "season_energy_contract": {
                        "type_seasonality": True,
                        "season_min_pu": True,
                        "season_max_pu": True
                    },
                    "guaran_energy_contract": {
                        "month_hour": True,
                        "guaranteed_value": True,
                        "emission_date": True,
                        "effective_date": True
                    },
                    "file_toUpload": [

                    ],
                    "market": True,
                    "activeStep": True,
                    "edit": True,
                    "validation": {
                        "touched": {
                            "modality": True,
                            "id_buyer_agents": True,
                            "type": True,
                            "id_seller_agents": True,
                            "start_supply": True,
                            "end_supply": True,
                            "volume_mwm": True,
                            "id_energy_product": True,
                            "contract_name": True,
                            "contract_status": True,
                            "signing_data": True,
                            "precif_energy_contract": {
                                "base_price_mwh": True,
                                "base_price_date": True,
                                "birthday_date": True,
                                "id_variable": True,
                                "active_price_mwh": True
                            },
                            "flexib_energy_contract": {
                                "flexibility_type": True
                            },
                            "modulation_energy_contract": {
                                "modulation_type": True
                            },
                            "season_energy_contract": {
                                "type_seasonality": True
                            },
                            "guaran_energy_contract": {
                                "month_hour": True,
                                "guaranteed_value": True,
                                "emission_date": True,
                                "effective_date": True
                            }
                        },
                        "errors": {

                        }
                    },
                    "sap_contract": True,
                    "contract_base_value": True
                },
                "errors": {

                }
            },
            "sap_contract": "1234567890",
            "contract_base_value": "744000.0000"
        }
        response = self.client.post(url, expected, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        #BAD_REQUEST contract name equal
        expected = {
            "id_buyer_agents": 10055,
            "id_seller_agents": 10055,
            "id_buyer_profile": "",
            "id_seller_profile": "",
            "id_energy_product": 1,
            "modality": "Longo Prazo",
            "type": "C",
            "start_supply": "01/07/2020",
            "end_supply": "31/07/2020",
            "contract_status": "AS",
            "signing_data": "01/01/2020",
            "volume_mwm": "10.000000",
            "volume_mwh": "7440.000",
            "contract_name": "CCE_10,0_AMERICA_AMERICA_0720_0720",
            "buyer_agents_detail": {
                "id_agents": "",
                "vale_name_agent": ""
            },
            "seller_agents_detail": {
                "id_agents": "",
                "vale_name_agent": ""
            },
            "buyer_profile_detail": {
                "id_profile": "",
                "name_profile": ""
            },
            "seller_profile_detail": {
                "id_profile": "",
                "name_profile": ""
            },
            "product": {
                "id_energy_product": "",
                "description": ""
            },
            "precif_energy_contract": {
                "id_variable": 1,
                "active_price_mwh": "100.0000",
                "base_price_mwh": "100.0000",
                "base_price_date": "01/07/2020",
                "birthday_date": "01/07/2020",
                "retusd": None
            },
            "flexib_energy_contract": {
                "flexibility_type": "Flat",
                "id_flexibilization_type": 1,
                "min_flexibility_pu_peak": None,
                "max_flexibility_pu_peak": None,
                "min_flexibility_pu_offpeak": None,
                "max_flexibility_pu_offpeak": None,
                "proinfa_flexibility": "N"
            },
            "modulation_energy_contract": {
                "modulation_type": "Flat",
                "min_modulation_pu": None,
                "max_modulation_pu": None
            },
            "season_energy_contract": {
                "type_seasonality": "Flat",
                "season_min_pu": None,
                "season_max_pu": None
            },
            "guaran_energy_contract": {
                "month_hour": "1",
                "guaranteed_value": "1.0000",
                "emission_date": "01/01/2020",
                "effective_date": "01/01/2020"
            },
            "file_toUpload": [

            ],
            "market": True,
            "activeStep": 0,
            "edit": True,
            "validation": {
                "touched": {
                    "id_buyer_agents": True,
                    "id_seller_agents": True,
                    "id_buyer_profile": True,
                    "id_seller_profile": True,
                    "id_energy_product": True,
                    "modality": True,
                    "type": True,
                    "start_supply": True,
                    "end_supply": True,
                    "contract_status": True,
                    "signing_data": True,
                    "volume_mwm": True,
                    "volume_mwh": True,
                    "contract_name": True,
                    "buyer_agents_detail": {
                        "id_agents": True,
                        "vale_name_agent": True
                    },
                    "seller_agents_detail": {
                        "id_agents": True,
                        "vale_name_agent": True
                    },
                    "buyer_profile_detail": {
                        "id_profile": True,
                        "name_profile": True
                    },
                    "seller_profile_detail": {
                        "id_profile": True,
                        "name_profile": True
                    },
                    "product": {
                        "id_energy_product": True,
                        "description": True
                    },
                    "precif_energy_contract": {
                        "id_variable": True,
                        "active_price_mwh": True,
                        "base_price_mwh": True,
                        "base_price_date": True,
                        "birthday_date": True,
                        "retusd": True
                    },
                    "flexib_energy_contract": {
                        "flexibility_type": True,
                        "id_flexibilization_type": True,
                        "min_flexibility_pu_peak": True,
                        "max_flexibility_pu_peak": True,
                        "min_flexibility_pu_offpeak": True,
                        "max_flexibility_pu_offpeak": True,
                        "proinfa_flexibility": True
                    },
                    "modulation_energy_contract": {
                        "modulation_type": True,
                        "min_modulation_pu": True,
                        "max_modulation_pu": True
                    },
                    "season_energy_contract": {
                        "type_seasonality": True,
                        "season_min_pu": True,
                        "season_max_pu": True
                    },
                    "guaran_energy_contract": {
                        "month_hour": True,
                        "guaranteed_value": True,
                        "emission_date": True,
                        "effective_date": True
                    },
                    "file_toUpload": [

                    ],
                    "market": True,
                    "activeStep": True,
                    "edit": True,
                    "validation": {
                        "touched": {
                            "modality": True,
                            "id_buyer_agents": True,
                            "type": True,
                            "id_seller_agents": True,
                            "start_supply": True,
                            "end_supply": True,
                            "volume_mwm": True,
                            "id_energy_product": True,
                            "contract_name": True,
                            "contract_status": True,
                            "signing_data": True,
                            "precif_energy_contract": {
                                "base_price_mwh": True,
                                "base_price_date": True,
                                "birthday_date": True,
                                "id_variable": True,
                                "active_price_mwh": True
                            },
                            "flexib_energy_contract": {
                                "flexibility_type": True
                            },
                            "modulation_energy_contract": {
                                "modulation_type": True
                            },
                            "season_energy_contract": {
                                "type_seasonality": True
                            },
                            "guaran_energy_contract": {
                                "month_hour": True,
                                "guaranteed_value": True,
                                "emission_date": True,
                                "effective_date": True
                            }
                        },
                        "errors": {

                        }
                    },
                    "sap_contract": True,
                    "contract_base_value": True
                },
                "errors": {

                }
            },
            "sap_contract": "1234567890",
            "contract_base_value": "744000.0000"
        }
        response = self.client.post(url, expected, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update(self):
        # exists
        energy = EnergyContract.objects.last()

        urlGet = '/energy-contract-api/session_energy_contract/%s/' % energy.pk
        urlPut = '/energy-contract-api/session_energy_contract_put/%s/' % energy.pk

        # put
        response = self.client.get(urlGet)
        response = self.client.put(urlPut, response.data, format='json')
        self.assertTrue(status.is_success(response.status_code))

        #put
        response = self.client.get(urlGet)
        response.data['contract_status']="EA"
        response = self.client.put(urlPut, response.data, format='json')
        self.assertTrue(status.is_success(response.status_code))

        #put
        response = self.client.get(urlGet)
        response.data['contract_status']="AS"
        response.data['signing_data']="24/09/2019"
        response = self.client.put(urlPut, response.data, format='json')
        self.assertTrue(status.is_success(response.status_code))

        #Passando Null
        response = self.client.get(urlGet)
        response.data['precif_energy_contract']=None
        response.data['flexib_energy_contract']=None
        response.data['modulation_energy_contract']=None
        response.data['season_energy_contract']=None
        response.data['guaran_energy_contract']=None
        response = self.client.put(urlPut, response.data, format='json')
        self.assertTrue(status.is_success(response.status_code))

        #Sem valor
        response = self.client.get(urlGet)
        response.data.pop('precif_energy_contract')
        response.data.pop('flexib_energy_contract')
        response.data.pop('modulation_energy_contract')
        response.data.pop('season_energy_contract')
        response.data.pop('guaran_energy_contract')
        response = self.client.put(urlPut, response.data, format='json')
        self.assertTrue(status.is_success(response.status_code))

        #bad request
        response = self.client.get(urlGet)
        response.data['contract_status']="AS"
        response.data['signing_data']=None
        response = self.client.put(urlPut, response.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # #Passando Null
        # for i in [1,2,3,4,5]:
        #     response = self.client.get(urlGet)   
        #     if i==1: response.data['precif_energy_contract']={'id_contract':None}
        #     elif i==2: response.data['flexib_energy_contract']={'id_contract':None}
        #     elif i==3: response.data['modulation_energy_contract']={'id_contract':None}
        #     elif i==4: response.data['season_energy_contract']={'id_contract':None}
        #     elif i==5: response.data['guaran_energy_contract']={'id_contract':None}
        #     response = self.client.put(urlPut, response.data, format='json')
        #     self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # not found
        urlGet = '/energy-contract-api/session_energy_contract/%s/' % 0
        response = self.client.get(urlGet)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_post_session_energy_contract_attachment(self):
        url='/energy-contract-api/session_energy_contract_attachment_post/'
        expected={
            "name": "ARQ TRANSF teste",
            "revision": "7",
            "comments": "TwRF",
            "path": "media/media/824d7ad4-cf07-4d7b-bfda-9788f7008dbc/doc teste2.docx",
            "id_contract": 84
        }
        
        response = self.client.post(url, expected, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_put_session_energy_contract_attachment(self):
        urlGet='/energy-contract-api/session_energy_contract_attachment/?id_contract=84'
        urlPut='/energy-contract-api/session_energy_contract_attachment_put/5/'
        
        response = self.client.get(urlGet)
        response.data['results'][0]['comments']="Teste Update"
        response = self.client.put(urlPut, response.data['results'][0], format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_current_price_energy_contract(self):
        url='/energy-contract-api/update_current_price_energy_contract/'
        expected_response = {
            "updateds": [
                {"id_contract": 1},
                {"id_contract": 2}
            ],
            "not_updateds": [
                {
                    "id_contract": 4,
                    "reason": "indexes_do_not_exists"
                },
                {
                    "id_contract": 5,
                    "reason": "division_by_zero_in_base_price_index_number"
                },
                {
                    "id_contract": 6,
                    "reason": "errors",
                    "errors": []
                }
            ]
        }
        
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
