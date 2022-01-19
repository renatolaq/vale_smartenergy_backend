from django.test import TestCase
from django.urls import reverse
from django.db import transaction
from rest_framework import status
from rest_framework.test import APITestCase
from core.models import Log
from organization.models import Segment,Business,DirectorBoard,AccountantArea,Product, ElectricalGrouping, ProductionPhase


# Create your tests here.
class OrganizationTest(APITestCase):
    #loads fixtures dependencies
    fixtures = [
        #'core/fixtures/initial_data_dxc.json', 'organization/fixtures/initial_data_dxc.json',
        #'gauge_point/fixtures/initial_data_dxc.json', 'energy_composition/fixtures/initial_data_dxc.json'
    ]

    def test_post(self):
        url = '/organization-api/session_organization_post/'
        for item in [1,2,3,4,5,6,7]:
            expected = {
                            "model":"%s" %item,
                            "data":{
                                "description":"PostTest"
                            }
                        }
            response = self.client.post(url, expected, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)            
            if item==1:#Account
                obj=AccountantArea.objects.filter(status="s").last()
            elif item==2:#Director
                obj=DirectorBoard.objects.filter(status="s").last()
            elif item==3:#business
                obj=Business.objects.filter(status="s").last()
            elif item==4:#Product
                obj=Product.objects.filter(status="s").last()
            elif item==5:#Segment
                obj=Segment.objects.filter(status="s").last()
            elif item==6:#ElectricalGrouping
                obj=ElectricalGrouping.objects.filter(status="s").last() 
            elif item==7:#ProductionPhase
                obj=ProductionPhase.objects.filter(status="s").last() 
            expected_error = {
                "model":"%s" %item,
                "data":{
                    "description":"%s" %obj.description
                }
            }
            response = self.client.post(url, expected_error, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        #Errors post
        expected_error = {}
        response = self.client.post(url, expected_error, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_error = {
                            "model":" ",
                            "data":{
                                "description":"TesteFinalAccountantUpdate"
                            }
                        }
        response = self.client.post(url, expected_error, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get(self):
        url = '/organization-api/session_organization/'

        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

        for i in [1,2,3,4,5,6,7]:
            url='/organization-api/show_organization/%s/'%i
            response = self.client.get(url, format='json')
            self.assertTrue(status.is_success(response.status_code))

    def test_find(self):
        for item in [1,2,3,4,5,6,7]:
            url = '/organization-api/organization_find/?description=teste&status=s&model=%s' %item
            response = self.client.get(url, format='json')
            self.assertTrue(status.is_success(response.status_code))
        
        #ordering
        url='/organization-api/organization_find/?ordering=description'
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))
        url='/organization-api/organization_find/?ordering=-description'
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))
        #ordering
        url='/organization-api/organization_find/?ordering=model'
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))
        url='/organization-api/organization_find/?ordering=-model'
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))
        url='/organization-api/organization_find/?ordering=-status'
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))
        url='/organization-api/organization_find/?ordering=-status'
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

    def test_update(self):
        for item in [1,2,3,4,5,6,7]:
            if item==1:#Account
                obj=AccountantArea.objects.filter(status="s", accountant_energyComposition__isnull=True).last()
                obj_initial=AccountantArea.objects.filter(status="s").first()
            elif item==2:#Director
                obj=DirectorBoard.objects.filter(status="s", director_energyComposition__isnull=True).last()
                obj_initial=DirectorBoard.objects.filter(status="s").first()
            elif item==3:#business
                obj=Business.objects.filter(status="s", business_energyComposition__isnull=True).last()
                obj_initial=Business.objects.filter(status="s").first()
            elif item==4:#Product
                obj=Product.objects.filter(status="s").last()
                obj_initial=Product.objects.filter(status="s").first()
            elif item==5:#Segment
                obj=Segment.objects.filter(status="s", segment_energyComposition__isnull=True).last()
                obj_initial=Segment.objects.filter(status="s").first()
            elif item==6:#ElectricalGrouping
                obj=ElectricalGrouping.objects.filter(status="s", electrical_grouping_gaugePoint__isnull=True).last()
                obj_initial=ElectricalGrouping.objects.filter(status="s").first()
            elif item==7:#ElectricalGrouping
                obj=ProductionPhase.objects.filter(status="s").last()
                obj_initial=ProductionPhase.objects.filter(status="s").first()
            
            urlGet = '/organization-api/session_organization/%s/%s/' % (obj.pk, item)
            response = self.client.get(urlGet,follow = True)

            url = '/organization-api/session_organization_put/%s/%s/' % (obj.pk, item)
            expected = {
                        "model":"%s"%item,
                        "data":{
                                "description":"TestUpdateTestViews",
                                "status":"S"
                        }
                    }
            expected_status = {
                        "model":"%s"%item,
                        "data":{
                                "description":"TestUpdateTestViews",
                                "status":"N"
                        }
                    }
            expected_Error = {
                        "model":"%s"%item,
                        "data":{
                                "description":"%s"%obj_initial.description,
                                "status":"S"
                        }
                    }
            #put
            response = self.client.put(url,expected,format='json',follow = True)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            #Alter status
            response = self.client.put(url,expected_status,format='json',follow = True)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            #put bad request
            response = self.client.put(url,expected_Error,format='json',follow = True)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            # not found
            url = '/organization-api/session_organization/0/%s/'%item
            response = self.client.get(url, format='json',follow = True) 
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            
        #test error model not exist put
        url = '/organization-api/session_organization_put/1/1/'
        expected_error = {
                            "model":"0",
                            "data":{
                                "description":"TestUpdateErrorModel"
                            }
                        }
        response = self.client.put(url, expected_error, format='json',follow = True)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        #test error model or data
        expected_error = {}
        response = self.client.put(url, expected_error, format='json',follow = True)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        #error model not exist get
        url = '/organization-api/session_organization/1/0/'
        response = self.client.get(url,follow = True)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_log(self):
        for item in [1,2,3,4,5,6]:
            if item==5:#Segment
                obj=Segment.objects.all()
            elif item==3:#business
                obj=Business.objects.all()
            elif item==2:#Director
                obj=DirectorBoard.objects.all()
            elif item==1:#Account
                obj=AccountantArea.objects.all()
            elif item==4:#Product
                obj=Product.objects.all()
            elif item==6:#ElectricalGrouping
                obj=ElectricalGrouping.objects.all()
            elif item==7:#ProductionPhase
                obj=ProductionPhase.objects.all()
            if obj:
                url='/organization-api/session_log_basic_organization/%s/%s/' %(obj[0].pk, item)
                response = self.client.get(url,follow = True)
                self.assertTrue(status.is_success(response.status_code))

    def test_file_csv(self):
        for item in [1,2,3,4,5,6,7]:
            url = '/organization-api/organization_find_file/?description=teste&status=s&model=%s&format_file=csv' %item
            response = self.client.get(url)
            self.assertTrue(status.is_success(response.status_code))
        #ordering
        url='/organization-api/organization_find_file/?ordering=description&format_file=csv'
        response = self.client.get(url)
        self.assertTrue(status.is_success(response.status_code))
        url='/organization-api/organization_find_file/?ordering=-description&format_file=csv'
        response = self.client.get(url)
        self.assertTrue(status.is_success(response.status_code))
                #status
        url='/organization-api/organization_find_file/?ordering=status&format_file=csv'
        response = self.client.get(url)
        self.assertTrue(status.is_success(response.status_code))
        url='/organization-api/organization_find_file/?ordering=-status&format_file=csv'
        response = self.client.get(url)
        self.assertTrue(status.is_success(response.status_code))
                #Model
        url='/organization-api/organization_find_file/?ordering=-model&format_file=csv'
        response = self.client.get(url)
        self.assertTrue(status.is_success(response.status_code))

        

        #Error
        url='/organization-api/organization_find_file/?ordering=-description'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        url='/organization-api/organization_find_file/?ordering=-description&format_file=error'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)