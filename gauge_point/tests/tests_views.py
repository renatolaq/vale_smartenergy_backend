from rest_framework import status
from rest_framework.test import APITestCase

from company.models import Company
from core.models import CceeDescription
from gauge_point.models import GaugePoint, UpstreamMeter, GaugeEnergyDealership, SourcePme

def id_source_valid(meterType):
    return (SourcePme.objects.filter(id_meter_type=meterType).first()).pk

class Gauge_PointTest(APITestCase):
    # loads fixtures dependencies
    fixtures = [
        #'core/fixtures/initial_data_dxc.json', 'company/fixtures/initial_data_dxc.json',
        #'agents/fixtures/initial_data_dxc.json', 'profiles/fixtures/initial_data_dxc.json', 
        #'organization/fixtures/initial_data_dxc.json', 'gauge_point/fixtures/initial_data_dxc.json',
        #'energy_composition/fixtures/initial_data_dxc.json', 'occurrence_record/fixtures/initial_data_dxc.json'
    ]
    def test_post_passed(self):
        urlPost='/gauge_point-api/session_gauge_point_post/' 
        jsonBasic={
            "id_source": "%d" %id_source_valid(1),  #Equal id_meter_type
            "id_company": 10090,
            "id_gauge_type": 1,
            "id_meter_type": 1, 
            "id_electrical_grouping": 6,
            "upstream": [
                {
                    "id_upstream_meter": 10084
                },
                {
                    "id_upstream_meter": 10085
                }
            ],
            "connection_point": "TesteUnitario",
            "gauge_dealership": {
                "id_dealership": 10093
            },
            "participation_sepp": "S",
            "ccee_gauge": {
                "code_ccee": "52959184"
            },
            "id_gauge": "",
            "errors": [],
            "gauge_type": "fronteira",
            "status": "S"
        }

        response = self.client.post(urlPost, jsonBasic, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_post_error(self):
        urlPost='/gauge_point-api/session_gauge_point_post/'
            ################################# Error, id_source null ####################################
        jsonBasic={
            "id_source": None, #Here error
            "id_company": 10090,
            "id_gauge_type": 1,
            "id_meter_type": 1, 
            "id_electrical_grouping": 6,
            "upstream": [
                {
                    "id_upstream_meter": 424
                },
                {
                    "id_upstream_meter": 476
                }
            ],
            "connection_point": "TesteUnitario",
            "gauge_dealership": {
                "id_dealership": 350
            },
            "participation_sepp": "S",
            "ccee_gauge": {
                "code_ccee": "52959184"
            },
            "id_gauge": "",
            "errors": [],
            "gauge_type": "fronteira",
            "status": "S"
        }
        response = self.client.post(urlPost, jsonBasic, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            
            ################################# Error, ccee disable ####################################
        jsonBasic={
            "id_source": "%d" %id_source_valid(1),  #Equal id_meter_type
            "id_company": 10090,
            "id_gauge_type": 2,
            "id_meter_type": 1,
            "id_electrical_grouping": 14,
            "upstream": [
                {
                    "id_upstream_meter": 424
                },
                {
                    "id_upstream_meter": 476
                }
            ],
            "connection_point": "TesteUnitario",
            "gauge_dealership": {
                "id_dealership": ""
            },
            "participation_sepp": "S",
            "ccee_gauge": {
                "code_ccee": "98418185" ##Error, code cce disable
            },
            "id_gauge": "",
            "errors": [],
            "gauge_type": "principal",
            "status": "S"
        }
        response = self.client.post(urlPost, jsonBasic, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            ################################# Error, upstream error ####################################
        jsonBasic={
            "id_source": "%d" %id_source_valid(1),  #Equal id_meter_type
            "id_company": 10090,
            "id_gauge_type": 1,
            "id_meter_type": 1, 
            "id_electrical_grouping": 6,
            "upstream": [
                {
                    "id_upstream_meter": 424
                },
                {
                    "id_upstream_meter": 476,
                    "testeUnitario": 'true' ##Error defined
                }
            ],
            "connection_point": "TesteUnitario",
            "gauge_dealership": {
                "id_dealership": 350
            },
            "participation_sepp": "S",
            "ccee_gauge": {
                "code_ccee": "52947184"
            },
            "id_gauge": "",
            "errors": [],
            "gauge_type": "fronteira",
            "status": "S"
        }
        response = self.client.post(urlPost, jsonBasic, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            ################################# Error, gauge point for disable ccee ####################################
        jsonBasic={
            "id_source": "%d" %id_source_valid(1),  #Equal id_meter_type
            "id_company": 10090,
            "id_gauge_type": 1,
            "id_meter_type": 1,
            "id_electrical_grouping": 14,
            "upstream": [
                {
                    "id_upstream_meter": 424
                },
                {
                    "id_upstream_meter": 476
                }
            ],
            "connection_point": "TesteUnitario",
            "gauge_dealership": {
                "id_dealership": ""
            },
            "participation_sepp": "S",
            "ccee_gauge": {
                "code_ccee": "59458849"
            },
            "id_gauge": "",
            "errors": [],
            "gauge_type": "", #Error, gauge type not blank
            "status": "S"
        }
        response = self.client.post(urlPost, jsonBasic, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_error(self):
            #####Gauge not exist
        urlPut='/gauge_point-api/session_gauge_point_put/%d/' %0
        response = self.client.put(urlPut, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

            ##Codigo CCEE invalid
        gauge_obj=(GaugePoint.objects.filter(status='S').last())
        urlGet = '/gauge_point-api/session_gauge_point/%d/' %gauge_obj.pk
        urlPut='/gauge_point-api/session_gauge_point_put/%d/' %gauge_obj.pk
        response_json = self.client.get(urlGet)
        json_params=response_json.data
        json_params['ccee_gauge']['code_ccee']="MGMONLALIMP03"
        response = self.client.put(urlPut, json_params, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put(self):
        gauge_obj=(GaugePoint.objects.filter(status='S').exclude(id_ccee__code_ccee="").last())
        
        urlGet = '/gauge_point-api/session_gauge_point/%d/' %gauge_obj.pk
        urlPut='/gauge_point-api/session_gauge_point_put/%d/' %gauge_obj.pk
        response_json = self.client.get(urlGet)
        json_params=response_json.data
        
        response = self.client.put(urlPut, json_params, format='json')
        self.assertTrue(status.is_success(response.status_code))

    def test_gauge_export_file(self):
        urlGet='/gauge_point-api/session_gauge_point_file/?format_file=csv'
        response = self.client.get(urlGet)
        self.assertTrue(status.is_success(response.status_code))

        urlGet='/gauge_point-api/session_gauge_point_file/?format_file=xlsx'
        response = self.client.get(urlGet)
        self.assertTrue(status.is_success(response.status_code))

        urlGet='/gauge_point-api/session_gauge_point_file/'
        response = self.client.get(urlGet)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_lists_gauge(self):
        urlGet='/gauge_point-api/session_show_gauge_type/'
        response = self.client.get(urlGet, format='json')
        self.assertTrue(status.is_success(response.status_code))

        urlGet='/gauge_point-api/session_show_meter_type/'
        response = self.client.get(urlGet, format='json')
        self.assertTrue(status.is_success(response.status_code))

        urlGet='/gauge_point-api/session_gauge_company/'
        response = self.client.get(urlGet, format='json')
        self.assertTrue(status.is_success(response.status_code))

        urlGet='/gauge_point-api/get_data_source_pme/'
        response = self.client.get(urlGet, format='json')
        self.assertTrue(status.is_success(response.status_code))

        gaugePk=(GaugePoint.objects.filter(id_source__isnull=False).last()).pk
        urlGet='/gauge_point-api/get_data_source_pme/?id_gauge=%d'%gaugePk
        response = self.client.get(urlGet, format='json')
        self.assertTrue(status.is_success(response.status_code))

        gaugePk=(GaugePoint.objects.filter(gauge_dad__isnull=False).last()).pk
        urlGet='/gauge_point-api/validate_gauge_using/%d/'%gaugePk
        response = self.client.get(urlGet, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        gaugePk=(GaugePoint.objects.filter(gauge_dad__isnull=True).last()).pk
        urlGet='/gauge_point-api/validate_gauge_using/%d/'%gaugePk
        response = self.client.get(urlGet, format='json')
        self.assertTrue(status.is_success(response.status_code))

    def test_get_find(self):
        urlGet = '/gauge_point-api/session_gauge_point_find_basic/'
        response = self.client.get(urlGet, format='json')
        self.assertTrue(status.is_success(response.status_code))
        
        urlGet = '/gauge_point-api/session_gauge_point/?id_gauge_type=2'
        response = self.client.get(urlGet, format='json')
        self.assertTrue(status.is_success(response.status_code))

    def test_get_detail(self):
        gauge = GaugePoint.objects.all().last()
        urlGet = '/gauge_point-api/session_gauge_point/%s/' % gauge.pk
        response = self.client.get(urlGet, format='json')
        self.assertTrue(status.is_success(response.status_code))
        #not found
        urlGet = '/gauge_point-api/session_gauge_point/0/'
        response = self.client.get(urlGet)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_log_gauge(self):
        urlGet = '/gauge_point-api/session_log_basic_gauge_point/%s/' %10065
        response = self.client.get(urlGet, format='json')
        self.assertTrue(status.is_success(response.status_code))