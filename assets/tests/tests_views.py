from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from django.db import transaction
from rest_framework.test import APITestCase

from assets.models import Assets, SeasonalityProinfa
from core.models import CceeDescription 

class AssetsTests(APITestCase):
    fixtures = [
        #'core/fixtures/initial_data_dxc.json', 'company/fixtures/initial_data_dxc.json',
        #'agents/fixtures/initial_data_dxc.json', 'profiles/fixtures/initial_data_dxc.json', 
        #'organization/fixtures/initial_data_dxc.json', 'gauge_point/fixtures/initial_data_dxc.json',
        #'energy_composition/fixtures/initial_data_dxc.json', 'assets/fixtures/initial_data_dxc.json', 
        #'asset_items/fixtures/initial_data_dxc.json'
    ]
    def test_showListGet(self):
        url='/assets-api/companyViews/'
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

        url='/assets-api/profileViews/'
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

        url='/assets-api/submarketViews/'
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

        url='/assets-api/energyCompositionViews/2/'
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

        url='/assets-api/show_assets/'
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code)) 

        url='/assets-api/get-by-profile/2/'
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code)) 

        url='/assets-api/get-by-agent/3/'
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

    def test_log_assets(self):
        obj_assets = Assets.objects.last()
        url='/assets-api/session_log_basic_assets/%s/' %obj_assets.pk
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

    def test_get(self):
        url='/assets-api/session_assets/'
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))
    
    def test_get_find(self):
        url = '/assets-api/session_assets_find_basic/'
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

        url='/assets-api/session_assets/?company_name=BETA&name_profile=Juliana&code_ccee=2020220220&show_balance=Assets&status=S&composition_name=composition_name%20teste&ordering=code_ccee'
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

    def test_get_detail(self):
        assets=Assets.objects.last()
        url='/assets-api/session_assets/%s/' %assets.pk
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

    def test_post(self):
        url='/assets-api/session_assets_post/'
        expected={
            "show_balance":"Assets",
            "status":"S",
            "id_ccee_siga":{
                "code_ccee":5003,
                "name_ccee":"TestPost",
                "type":"SIGA",
                "status":"S"
            },
            "id_company":{
                "id_company":10189
            },
            "id_profile":{
                "id_profile":29
            },
            "id_submarket":{
                "id_submarket":2
            },
            "id_ccee_proinfa":{
                "code_ccee":6002
            },
            "Assets_Composition":{
                "id_energy_composition":34,
                "status":"S"
            }
        }
        response = self.client.post(url, expected, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        #ERROR SIGA
        for value in [1,2,3,4]:
            expected_error={
                "show_balance":"Assets",
                "status":"S",
                "id_ccee_siga":{
                    "code_ccee":7464,
                    "name_ccee":"Bahia PCH I",
                    "status":"S"
                },
                "id_company":{
                    "id_company":10189
                },
                "id_profile":{
                    "id_profile":29
                },
                "id_submarket":{
                    "id_submarket":2
                },
                "id_ccee_proinfa":{
                    "code_ccee":566595985,
                    "name_ccee":"Teste",
                    "status":"S"
                },
                "Assets_Composition":{
                    "id_energy_composition":34,
                    "status":"S"
                }
            }
            if value==1: #Error SIGA negative
                expected_error['id_ccee_siga']['code_ccee']=-221212123
            elif value==2: #Error SIGA equal
                expected_error['id_ccee_siga']['code_ccee']=7464
            elif value==3: #Error SIGA null
                expected_error['id_ccee_siga']['code_ccee']=None
            elif value==4:#Error SIGA type
                expected_error['id_ccee_siga']['type']="Error"
            response = self.client.post(url, expected_error, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        #ERROR PROINFA VALUE = 2 
        for value in [1,3]:
            expected_error={
                "show_balance":"Assets",
                "status":"S",
                "id_ccee_siga":{
                    "code_ccee":675124523,
                    "name_ccee":"TestPost",
                    "status":"S"
                },
                "id_company":{
                    "id_company":10189
                },
                "id_profile":{
                    "id_profile":29
                },
                "id_submarket":{
                    "id_submarket":2
                },
                "id_ccee_proinfa":{
                    "code_ccee":7464,
                    "name_ccee":"TestPost",
                    "status":"S"
                },
                "Assets_Composition":{
                    "id_energy_composition":34,
                    "status":"S"
                }
            }
            if value==1: #Error PROINFA negative
                expected_error['id_ccee_proinfa']['code_ccee']=-3626241
            elif value==2: #Error PROINFA equal
                expected_error['id_ccee_proinfa']['code_ccee']=7464
            elif value==3: #Error PROINFA type
                expected_error['id_ccee_proinfa']['type']="Error"
            response = self.client.post(url, expected_error, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        #ERROR SHOW_BALANCE 
        expected_error={
                "show_balance":"Assets",
                "status":"S",
                "id_ccee_siga":{
                    "code_ccee":5003,
                    "name_ccee":"TestPost",
                    "status":"S"
                },
                "id_company":{
                    "id_company":10189
                },
                "id_profile":{
                    "id_profile":29
                },
                "id_submarket":{
                    "id_submarket":2
                },
                "id_ccee_proinfa":{
                    "code_ccee":62303,
                    "name_ccee":"TestPost",
                    "status":"S"
                },
                "Assets_Composition":{
                    "id_energy_composition":34,
                    "status":"S"
                }
            }
        expected_error['show_balance']="Error"
        response = self.client.post(url, expected_error, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # #ERROR id_submarket
        expected_error={
                "show_balance":"Assets",
                "status":"S",
                "id_ccee_siga":{
                    "code_ccee":5003,
                    "name_ccee":"TestPost",
                    "status":"S"
                },
                "id_company":{
                    "id_company":10189
                },
                "id_profile":{
                    "id_profile":29
                },
                "id_submarket":{
                    "id_submarket":2
                },
                "id_ccee_proinfa":{
                    "code_ccee":62303,
                    "name_ccee":"TestPost",
                    "status":"S"
                },
                "Assets_Composition":{
                    "id_energy_composition":34,
                    "status":"S"
                }
            }
        expected_error['id_submarket']['id_submarket']=0
        response = self.client.post(url, expected_error, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        #ERROR TYPE ccee
        expected_error={
                "show_balance":"Assets",
                "status":"S",
                "id_ccee_siga":{
                    "code_ccee":62365,
                    "name_ccee":"TestPost",
                    "status":"S"
                },
                "id_company":{
                    "id_company":10189
                },
                "id_profile":{
                    "id_profile":29
                },
                "id_submarket":{
                    "id_submarket":2
                },
                "id_ccee_proinfa":{
                    "code_ccee":623698,
                    "name_ccee":"TestPost",
                    "status":"S"
                },
                "Assets_Composition":{
                    "id_energy_composition":34,
                    "status":"S"
                }
            }
        expected_error['id_ccee_siga']['type']="Error"
        response = self.client.post(url, expected_error, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        #ERROR ENERGY COMPOSITION 
        expected_error={
                "show_balance":"Assets",
                "status":"S",
                "id_ccee_siga":{
                    "code_ccee":85859,
                    "name_ccee":"TestPost",
                    "status":"S"
                },
                "id_company":{
                    "id_company":10189
                },
                "id_profile":{
                    "id_profile":29
                },
                "id_submarket":{
                    "id_submarket":2
                },
                "id_ccee_proinfa":{
                    "code_ccee":95896,
                    "name_ccee":"TestPost",
                    "status":"S"
                },
                "Assets_Composition":{
                    "id_energy_composition":1,
                    "status":"S"
                }
            }
        expected_error['Assets_Composition']['id_energy_composition']=0
        response = self.client.post(url, expected_error, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_post_seasonality(self):
        assets = Assets.objects.all().first()
        url='/assets-api/session_assets_post_Seasonality/%s/' %assets.id_assets
        expected={
                "Seasonality_proinfa": {
                    "Seasonality": [
                        {
                            "measure_unity": "MWh",
                            "year": "2019",
                            "january": "10",
                            "february": "10",
                            "march": "10",
                            "april": "10",
                            "may": "10",
                            "june": "10",
                            "july": "10",
                            "august": "10",
                            "september": "10",
                            "october": "10",
                            "november": "10",
                            "december": "10"
                        },
                    ]
                }
            }

        response = self.client.post(url, expected, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        #Error assets not exist
        assets = Assets.objects.all().first()
        url='/assets-api/session_assets_post_Seasonality/0/'
        expected_error={
                "Seasonality_proinfa":{
                    "id_seasonality":{
                        "year":2012,
                        "measure_unity":"MWh",
                        "january":200.0,
                        "february":300.0,
                        "march":400.0,
                        "april":500.0,
                        "may":600.0,
                        "june":700.0,
                        "july":800.0,
                        "august":900.0,
                        "september":110.0,
                        "october":120.0,
                        "november":130.0,
                        "december":140.0
                    }
                }
            }
        response = self.client.post(url, expected_error, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        #Error 
        assets = Assets.objects.all().first()
        url='/assets-api/session_assets_post_Seasonality/%s/' %assets.id_assets
        expected_error={
                "Seasonality_proinfa":{
                    "Seasonality":[
                        {
                            "measure_unity":"sads",
                            "year":"2019"
                        }
                    ]
                }
            }
        response = self.client.post(url, expected_error, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put(self):
        assets = Assets.objects.filter(id_ccee_siga__isnull=False, id_ccee_proinfa__isnull=False).last()
        url = '/assets-api/session_assets/%s/' %assets.pk
        urlPut = '/assets-api/session_assets_put/%s/' %assets.pk
        response = self.client.get(url)
        self.assertTrue(status.is_success(response.status_code))

        #put
        cceeSiga = CceeDescription.objects.get(pk=assets.id_ccee_siga_id)
        cceeProinfa = CceeDescription.objects.get(pk=assets.id_ccee_proinfa_id)
        expected={
                    "show_balance":"Asset items",
                    "status":"S",
                    "id_ccee_siga":{
                        "code_ccee":"%s" %cceeSiga.code_ccee,
                        "name_ccee":"Gisele",
                        "status":"S"
                    },
                    "id_company":{
                        "id_company":10189
                    },
                    "id_profile":{
                        "id_profile":29
                    },
                    "id_submarket":{
                        "id_submarket":2
                    },
                    "id_ccee_proinfa":{   
                        "code_ccee":"%s" %cceeProinfa.code_ccee,
                        "name_ccee":"Gabriel",
                        "status":"S"
                    },
                    "Assets_Composition":{
                        "id_energy_composition": 34,
                        "status": "S"
                    }
                }

        response = self.client.put(urlPut, expected, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        #put com code_ccee
        url_CodeCcee = '/assets-api/session_assets_put/58/'
        expected={
                    "show_balance":"Asset items",
                    "status":"S",
                    "id_ccee_siga":{
                        "code_ccee":"307",
                        "name_ccee":"Gisele",
                        "status":"S"
                    },
                    "id_company":{
                        "id_company":10189
                    },
                    "id_profile":{
                        "id_profile":29
                    },
                    "id_submarket":{
                        "id_submarket":2
                    },
                    "id_ccee_proinfa":{   
                        "code_ccee":"1515215",
                        "name_ccee":"Gabriel",
                        "status":"S"
                    },
                    "Assets_Composition":{
                        "id_energy_composition": 34,
                        "status": "S"
                    }
                }

        response = self.client.put(url_CodeCcee, expected, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        #alter code ccee
        expected['id_ccee_siga']['code_ccee']=15155524548
        expected['id_ccee_proinfa']['code_ccee']=84945418
        response = self.client.put(urlPut, expected, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        #PUT Errors
        #put error status
        url = '/assets-api/session_assets/20/' 
        response = self.client.get(url)
        response.data['status']='N'
        response = self.client.put(urlPut, response.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        #ERROR SIGA
        for value in [1,2,3]:
            cceeSiga = CceeDescription.objects.get(pk=assets.id_ccee_siga_id)
            expected_error={
                "show_balance":"Asset items",
                "status":"S",
                "id_ccee_siga":{
                    "code_ccee":"%s" %cceeSiga.code_ccee,
                    "name_ccee":"Gisele",
                    "status":"S"
                },
                "id_company":{
                    "id_company":10189
                },
                "id_profile":{
                    "id_profile":29
                },
                "id_submarket":{
                    "id_submarket":2
                },
                "id_ccee_proinfa":{   
                    "code_ccee":"%s" %cceeProinfa.code_ccee,
                    "name_ccee":"Gabriel",
                    "status":"S"
                },
                "Assets_Composition":{
                    "id_energy_composition": 34,
                    "status": "S"
                }
            }
            if value==1: #Error SIGA negative
                expected_error['id_ccee_siga']['code_ccee']=-221212123
            elif value==2: #Error SIGA equal
                assetsNotEqual = Assets.objects.filter(id_ccee_siga__isnull=False, id_ccee_proinfa__isnull=False).exclude(pk=assets.pk).last()
                urlTestEqual = '/assets-api/session_assets_put/%s/' %assetsNotEqual.pk
                response = self.client.put(urlTestEqual, expected_error, format='json')
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            elif value==3: #Error SIGA null
                expected_error['id_ccee_siga']['code_ccee']=None

            if value != 2:
                response = self.client.put(urlPut, expected_error, format='json')
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        #ERROR PROINFA
        for value in [1,2]:
            cceeProinfa = CceeDescription.objects.get(pk=assets.id_ccee_proinfa_id)
            expected_error={
                "show_balance":"Asset items",
                "status":"S",
                "id_ccee_siga":{
                    "code_ccee":"%s" %cceeSiga.code_ccee,
                    "name_ccee":"Gisele",
                    "status":"S"
                },
                "id_company":{
                    "id_company":10189
                },
                "id_profile":{
                    "id_profile":29
                },
                "id_submarket":{
                    "id_submarket":2
                },
                "id_ccee_proinfa":{   
                    "code_ccee":"%s" %cceeProinfa.code_ccee,
                    "name_ccee":"Gabriel",
                    "status":"S"
                },
                "Assets_Composition":{
                    "id_energy_composition": 34,
                    "status": "S"
                }
            }
            if value==1: #Error PROINFA negative
                expected_error['id_ccee_proinfa']['code_ccee']=-3626241
            elif value==2: #Error PROINFA equal
                urlTestEqual = '/assets-api/session_assets_put/%s/' %assetsNotEqual.pk
                response = self.client.put(urlTestEqual, expected_error, format='json')
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            if value != 2:
                response = self.client.put(urlPut, expected_error, format='json')
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        #ERROR SHOW_BALANCE
        expected_error={
                "show_balance":"Asset items",
                "status":"S",
                "id_ccee_siga":{
                    "code_ccee":"%s" %cceeSiga.code_ccee,
                    "name_ccee":"Gisele",
                    "status":"S"
                },
                "id_company":{
                    "id_company":10189
                },
                "id_profile":{
                    "id_profile":29
                },
                "id_submarket":{
                    "id_submarket":2
                },
                "id_ccee_proinfa":{   
                    "code_ccee":"%s" %cceeProinfa.code_ccee,
                    "name_ccee":"Gabriel",
                    "status":"S"
                },
                "Assets_Composition":{
                    "id_energy_composition": 34,
                    "status": "S"
                }
            }
        expected_error['show_balance']="Error"
        response = self.client.put(urlPut, expected_error, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        #ERROR TYPE ccee
        expected_error={
                "show_balance":"Asset items",
                "status":"S",
                "id_ccee_siga":{
                    "code_ccee":"%s" %cceeSiga.code_ccee,
                    "name_ccee":"Gisele",
                    "status":"S"
                },
                "id_company":{
                    "id_company":10189
                },
                "id_profile":{
                    "id_profile":29
                },
                "id_submarket":{
                    "id_submarket":2
                },
                "id_ccee_proinfa":{   
                    "code_ccee":"%s" %cceeProinfa.code_ccee,
                    "name_ccee":"Gabriel",
                    "status":"S"
                },
                "Assets_Composition":{
                    "id_energy_composition": 34,
                    "status": "S"
                }
            }
        expected_error['id_ccee_proinfa']['type']="Error"
        response = self.client.put(urlPut, expected_error, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        #ERROR SUBMARKET
        expected_error={
                "show_balance":"Asset items",
                "status":"S",
                "id_ccee_siga":{
                    "code_ccee":"%s" %cceeSiga.code_ccee,
                    "name_ccee":"Gisele",
                    "status":"S"
                },
                "id_company":{
                    "id_company":10189
                },
                "id_profile":{
                    "id_profile":29
                },
                "id_submarket":{
                    "id_submarket":2
                },
                "id_ccee_proinfa":{   
                    "code_ccee":"%s" %cceeProinfa.code_ccee,
                    "name_ccee":"Gabriel",
                    "status":"S"
                },
                "Assets_Composition":{
                    "id_energy_composition": 34,
                    "status": "S"
                }
            }
        expected_error['id_submarket']['id_submarket']=0
        response = self.client.put(urlPut, expected_error, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        #ERROR ENERGY COMPOSITION
        expected_error={
                "show_balance":"Asset items",
                "status":"S",
                "id_ccee_siga":{
                    "code_ccee":"%s" %cceeSiga.code_ccee,
                    "name_ccee":"Gisele",
                    "status":"S"
                },
                "id_company":{
                    "id_company":10189
                },
                "id_profile":{
                    "id_profile":29
                },
                "id_submarket":{
                    "id_submarket":2
                },
                "id_ccee_proinfa":{   
                    "code_ccee":"%s" %cceeProinfa.code_ccee,
                    "name_ccee":"Gabriel",
                    "status":"S"
                },
                "Assets_Composition":{
                    "id_energy_composition": 34,
                    "status": "S"
                }
            }
        expected_error['Assets_Composition']['id_energy_composition']=0
        response = self.client.put(urlPut, expected_error, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_put_seasonality(self):
        url = '/assets-api/session_assets_put_Seasonality/'
        #put
        expected={
                "Seasonality_proinfa": {
                    "Seasonality": [
                        {
                            "id_seasonality":17,
                            "measure_unity": "MWh",
                            "year": "2019",
                            "january": "10",
                            "february": "10",
                            "march": "10",
                            "april": "10",
                            "may": "10",
                            "june": "10",
                            "july": "10",
                            "august": "10",
                            "september": "10",
                            "october": "10",
                            "november": "10",
                            "december": "10"
                        },
                    ]
                }
            }
        response = self.client.put(url, expected, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_export_file_csv(self):
        url='/assets-api/session_assets_file/?code_ccee=2020220220&ordering=code_ccee&format_file=csv'
        response = self.client.get(url)
        self.assertTrue(status.is_success(response.status_code))
        #ERROR
        url='/assets-api/session_assets_file/?code_ccee=2020220220'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_export_file_pdf(self):
        url='/assets-api/session_assets_file/?code_ccee=2020220220&format_file=pdf'
        response = self.client.get(url)
        self.assertTrue(status.is_success(response.status_code))
        #ERROR
        url='/assets-api/session_assets_file/?code_ccee=2020220220'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
        