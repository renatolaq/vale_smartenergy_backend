from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.db import transaction

from asset_items.models import AssetItems, SeasonalityAssetItemCost, SeasonalityAssetItem, SeazonalityAssetItemDepreciation
from core.models import CceeDescription, Seasonality
from company.models import Company
from assets.models import Assets
from energy_composition.models import EnergyComposition

# Create your tests here.

class AssetItemsTest(APITestCase):
    # loads fixtures dependencies
    fixtures = [ 
        #'core/fixtures/initial_data_dxc.json', 'company/fixtures/initial_data_dxc.json',
        #'agents/fixtures/initial_data_dxc.json', 'profiles/fixtures/initial_data_dxc.json', 
        #'organization/fixtures/initial_data_dxc.json', 'gauge_point/fixtures/initial_data_dxc.json',
        #'energy_composition/fixtures/initial_data_dxc.json', 'assets/fixtures/initial_data_dxc.json', 
        #'asset_items/fixtures/initial_data_dxc.json'
    ]

    def test_post(self): #ok
        url = '/asset-items-api/session_asset_items_post/'
        companyId=Company.objects.filter(assetitems_company__isnull=True).last()
        assetsId=Assets.objects.filter(assetitems_asset__isnull=True).last()
        energyCompositionId = EnergyComposition.objects.all().last()
        
        expected = {
            "id_assets": assetsId.pk,
            "id_company": companyId.pk,
            "status": "S",
            "id_energy_composition": energyCompositionId.pk
        }
        response = self.client.post(url, expected, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        expected_error = {
            "id_assets": assetsId.pk,
            "id_company": companyId.pk,
            "status": "S",
            "id_energy_composition": energyCompositionId.pk
        }
        response = self.client.post(url, expected_error, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get(self):
        url = '/asset-items-api/session_asset_items/'
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

        asset_obj = AssetItems.objects.all().last()
        url = '/asset-items-api/session_asset_items/%s/' %asset_obj.pk
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

        url = '/asset-items-api/session_asset_items/0/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_log(self):
        obj=AssetItems.objects.all().last()
        url= '/asset_items-api/session_log_basic_asset_items/%s/' %obj.pk
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))
    
    def test_showListGet(self):
        url='/asset-items-api/show_company/'
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))
    
        url='/asset-items-api/show_energyComposition/2/'
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

        url='/asset-items-api/show_assets_get_basic/'
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

    def test_get_find(self):
        url='/asset-items-api/session_asset_items/?company_name=BETA&cost_center=cost_center%20teste&name_ccee=TesteSIGAUpdate&composition_name=composition_view%20teste1&status=N'
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))
        url = '/asset-items-api/session_asset_items_find_basic/'
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

    def test_update(self): 
        # exists
        asset_item = AssetItems.objects.all().first()

        urlGet = '/asset-items-api/session_asset_items/%s/' % asset_item.pk
        url = '/asset-items-api/session_asset_items_put/%s/' % asset_item.pk
        response = self.client.get(urlGet)
        self.assertTrue(status.is_success(response.status_code))

        # put
        response = self.client.put(url, response.data, format='json')
        print("EROR:", response.data)
        self.assertTrue(status.is_success(response.status_code))

        # put bad request
        expected_error = {}
        response = self.client.put(url, expected_error, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # not found
        urlput = '/asset-items-api/session_asset_items_put/%s/' % 0
        response = self.client.put(urlput)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_post_seasonality_asset_item(self):
        asset_item = AssetItems.objects.all().first()
        url='/asset-items-api/session_asset_items_post_Seasonality_Asset_Item/%s/' %asset_item.id_asset_items
        expected={
                 "Seasonality_asset_item":[
                        {
                    "Seasonality":{
                        "year": 1940,
                        "measure_unity": "PU ",
                        "january": 0.991000000,
                        "february": 1.010000000,
                        "march": 0.981000000,
                        "april": 1.020000000,
                        "may": 1.030000000,
                        "june": 0.970000000,
                        "july": 0.950000000,
                        "august": 1.050000000,
                        "september": 1.040000000,
                        "october": 0.960000000,
                        "november": 1.060000000,
                        "december": 0.940000000
                     }
            }
     
        ]
        }

        response = self.client.post(url, expected, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        #Error: This asset items not exist
        url='/asset-items-api/session_asset_items_post_Seasonality_Asset_Item/3454354534/'
        expected_error= {
                 "Seasonality_asset_item":[
                        {
                    "Seasonality":{
                        "year": 2016,
                        "measure_unity": "PU ",
                        "january": 0.990000000,
                        "february": 1.010000000,
                        "march": 0.980000000,
                        "april": 1.020000000,
                        "may": 1.030000000,
                        "june": 0.970000000,
                        "july": 0.950000000,
                        "august": 1.050000000,
                        "september": 1.040000000,
                        "october": 0.960000000,
                        "november": 1.060000000,
                        "december": 0.940000000
                     }
            }
     
        ]
        }

        response = self.client.post(url, expected_error, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Years already exists: [2020]
        asset_item = AssetItems.objects.all().first()
        url='/asset-items-api/session_asset_items_post_Seasonality_Asset_Item/61/'
        expected_error={
                 "Seasonality_asset_item":[
                        {
                    "Seasonality":{
                        "year": 2020,
                        "measure_unity": "MWh",
                        "january": 200.000000000,
                        "february": 300.000000000,
                        "march": 400.000000000,
                        "april": 500.000000000,
                        "may": 600.000000000,
                        "june": 700.000000000,
                        "july": 800.000000000,
                        "august": 900.000000000,
                        "september": 110.000000000,
                        "october": 120.000000000,
                        "november": 130.000000000,
                        "december": 140.000000000
                    }
            }
     
        ]
        }
        response = self.client.post(url, expected_error, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_post_seasonality_asset_item_cost(self):#ok
        asset_item = AssetItems.objects.all().first()
        url='/asset-items-api/session_asset_items_post_Seasonality_Item_Cost/%s/' %asset_item.id_asset_items
        expected={
                  "Seasonality_asset_item_cost":[
                            {
                        "Seasonality":{
                            "year": 2027,
                            "measure_unity": "$  ",
                            "january": 21.000000000,
                            "february": 21.000000000,
                            "march": 21.000000000,
                            "april": 21.000000000,
                            "may": 21.000000000,
                            "june": 21.000000000,
                            "july": 21.000000000,
                            "august": 21.000000000,
                            "september": 21.000000000,
                            "october": 21.000000000,
                            "november": 21.000000000,
                            "december": 21.000000000
                    }
            }
     
        ]
        }
        response = self.client.post(url, expected, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Years already exists: [2020]
        asset_item = AssetItems.objects.all().first()
        url='/asset-items-api/session_asset_items_post_Seasonality_Item_Cost/60/'
        expected_error={
                "Seasonality_asset_item_cost":[
                    {
                        "Seasonality":{
                            "year": 2020,
                            "measure_unity": "$  ",
                            "january": 21.000000000,
                            "february": 21.000000000,
                            "march": 21.000000000,
                            "april": 21.000000000,
                            "may": 21.000000000,
                            "june": 21.000000000,
                            "july": 21.000000000,
                            "august": 21.000000000,
                            "september": 21.000000000,
                            "october": 21.000000000,
                            "november": 21.000000000,
                            "december": 21.000000000
                        }
                      
                    }
                ]
            }
        response = self.client.post(url, expected_error, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_post_seazonality_asset_depreciation(self):
        asset_item = AssetItems.objects.all().first()
        url='/asset-items-api/session_asset_items_post_Seasonality_Depreciation/%s/' %asset_item.id_asset_items
        expected = {
                 "Seazonality_asset_depreciation":[
                      {
                    "Seasonality":{
                        "year": 2023,
                        "measure_unity": "mwh",
                        "january": 21.000000000,
                        "february": 21.000000000,
                        "march": 21.000000000,
                        "april": 21.000000000,
                        "may": 21.000000000,
                        "june": 21.000000000,
                        "july": 21.000000000,
                        "august": 21.000000000,
                        "september": 21.000000000,
                        "october": 21.000000000,
                        "november": 21.000000000,
                        "december": 21.000000000
                    }
            }
     
        ]
        }
        response = self.client.post(url, expected, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Years already exists: [2023]
        url='/asset-items-api/session_asset_items_post_Seasonality_Depreciation/34/'
        expected_error={
                "Seazonality_asset_depreciation":[
                      {
                    "Seasonality":{
                       "year": 2020,
                        "measure_unity": "$  ",
                        "january": 21.000000000,
                        "february": 21.000000000,
                        "march": 21.000000000,
                        "april": 21.000000000,
                        "may": 21.000000000,
                        "june": 21.000000000,
                        "july": 21.000000000,
                        "august": 21.000000000,
                        "september": 21.000000000,
                        "october": 21.000000000,
                        "november": 21.000000000,
                        "december": 21.000000000

                     }
            }
     
        ]
        }
        response = self.client.post(url, expected_error, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_seasonality_asset_item(self): #ok
        
        url = '/asset-items-api/session_asset_items_put_Seasonality_Asset_Item/'
        #put
        expected={
                "Seasonality_asset_item":[
                    {
                        "id_seasonality_asset_item": "2",
                        "id_asset_items": "65",
                        "id_seasonality": "25",
                        "Seasonality":{
                                    "id_seasonality": "25",
                                    "year":2009,
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
                ]
            }
        response = self.client.put(url, expected, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        #Error save Seasonality_Asset_Item
        url='/asset-items-api/session_asset_items_put_Seasonality_Asset_Item/'
        expected_error={
                "Seasonality_asset_item":[
                    {
                        "id_seasonality_asset_item": "2",
                        "id_asset_items": "35",
                        "id_seasonality": "63",
                        "Seasonality":{
                                    "id_seasonality": "25",
                                    "year":2020, #Error equal
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
                ]
            }
        response = self.client.put(url, expected_error, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_seasonality_asset_item_cost(self):#ok
        #put
        url='/asset-items-api/session_asset_items_put_Seasonality_Item_Cost/'
        assetSeaso_obj=SeasonalityAssetItemCost.objects.all().last()
        expected={
                "Seasonality_asset_item_cost":[
                    {
                        "id_seasonality_asset_item": "%s" %assetSeaso_obj.pk,
                        "id_asset_items": "%s" %assetSeaso_obj.id_asset_items_id,
                        "id_seazonality_asset": "%s" %assetSeaso_obj.id_seazonality_asset_id,
                        "Seasonality":{
                            "id_seasonality": "%s" %assetSeaso_obj.id_seazonality_asset_id,
                            "year": "1935",
                            "measure_unity": "PU ",
                            "january": 56.000000000,
                            "february": 56.000000000,
                            "march": 21.000000000,
                            "april": 21.000000000,
                            "may": 56.000000000,
                            "june": 21.000000000,
                            "july": 21.000000000,
                            "august": 56.000000000,
                            "september": 21.000000000,
                            "october": 21.000000000,
                            "november": 21.000000000,
                            "december": 21.000000000
                        }
                    }
                ]
            }

        response = self.client.put(url, expected, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_put_Seazonality_asset_depreciation(self):#OK
        #put
        url = '/asset-items-api/session_asset_items_put_Seasonality_Depreciation/'
        expected={
                    "Seazonality_asset_depreciation":[
                        {
                            "seazonality_asset_depreciation": "5",
                            "id_asset_items": "50",
                            "id_seasonality": "25",
                            "Seasonality":{
                                    "id_seasonality": "25",
                                    "year": 2009,
                                    "measure_unity": "mwh",
                                    "january": 21.000000000,
                                    "february": 21.000000000,
                                    "march": 21.000000000,
                                    "april": 21.000000000,
                                    "may": 21.000000000,
                                    "june": 21.00000000,
                                    "july": 21.00000000,
                                    "august": 21.000000000,
                                    "september": 21.000000000,
                                    "october": 21.000000000,
                                    "november": 21.000000000,
                                    "december": 21.000000000
                                }
                        }
        
                    ]
                }
        response = self.client.put(url, expected, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        #'error':"Error save Seazonality_asset_depreciation"
        url='/asset-items-api/session_asset_items_put_Seasonality_Depreciation/'
        expected_error={
                "Seazonality_asset_depreciation":[
                    {
                        "seazonality_asset_depreciation": "2",
                        "id_asset_items": "35",
                        "id_seasonality": "65",
                        "Seasonality":{
                                "id_seasonality": "237",
                                "year": 2023, #Error
                                "measure_unity": "mwh",
                                "january": 21.000000000,
                                "february": 21.000000000,
                                "march": 21.000000000,
                                "april": 21.000000000,
                                "may": 21.000000000,
                                "june": 21.000000000,
                                "july": 21.000000000,
                                "august": 21.000000000,
                                "september": 21.000000000,
                                "october": 21.000000000,
                                "november": 21.000000000,
                                "december": 21.000000000
                        }
                    }
                ]
        }
        response = self.client.put(url, expected_error, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_export_file_csv(self):
        url = '/asset-items-api/session_asset_items_file/?company_name=BETA&ordering=company_name&format_file=csv'
        response = self.client.get(url)
        self.assertTrue(status.is_success(response.status_code))

        url = '/asset-items-api/session_asset_items_file/?format_file=csv'
        response = self.client.get(url)
        self.assertTrue(status.is_success(response.status_code))
        
        #ERROR  you need pass a format_file=csv or pdf
        url='/asset-items-api/session_asset_items_file/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        #ERROR 
        url='/asset-items-api/session_asset_items_file/?format_file=error'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_export_file_pdf(self):
        url='/asset-items-api/session_asset_items_file/?company_name=BETA&ordering=company_name&format_file=pdf'
        response = self.client.get(url)
        self.assertTrue(status.is_success(response.status_code))
        
        url='/asset-items-api/session_asset_items_file/?format_file=pdf'
        response = self.client.get(url)
        self.assertTrue(status.is_success(response.status_code))
