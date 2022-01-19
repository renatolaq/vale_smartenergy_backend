from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status

class BudgetTest(APITestCase):
    def test_get_no_filter(self):
        url = '/v1/projectedmonitoring/'

        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 20)
        self.assertEqual(response.data[0]['id'], 2)
        self.assertEqual(response.data[19]['id'], 8)
        self.assertEqual(response._headers['x-total-count'][1], '20')
        self.assertEqual(response._headers['x-total-pages'][1], '1')

    def test_get_paged(self):
        url = '/v1/projectedmonitoring/'

        response = self.client.get(url, data={"perPage": 10, "page": 2 }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 10)
        self.assertEqual(response.data[0]['id'], 17)
        self.assertEqual(response.data[9]['id'], 8)
        self.assertEqual(response._headers['x-total-count'][1], '20')
        self.assertEqual(response._headers['x-total-pages'][1], '2')

    def test_export_no_filter(self):
        url = '/v1/projectedmonitoring/export'

        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_calculate(self):
        url = '/v1/projectedmonitoring/3/calculatePlanMonitoring'
        budget_doc = {
            "monitoringData": {
                "firstYear": {},
                "secondYear": {}
            }
        }

        response = self.client.post(url, data=budget_doc, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update(self):
        url = '/v1/projectedmonitoring/3'
        doc = {
            "monitoringData": {
                "firstYear": {},
                "secondYear": {}
            },
            "comment": "test"
        }

        response = self.client.put(url, data=doc, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_get_projectedmonitoring(self):
        url = '/v1/projectedmonitoring/3'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_justify_no_exiting_alert(self):
        url = '/v1/projectedmonitoring/3/justify'

        doc = {
            "field": "realizedTotalConsumption",
            "message": "Test",
            "alert": "VALUE_DIVERGES_MORE_THAN_5_PER_OF_PLANNED",
            "month": "september",
        }

        response = self.client.post(url, data=doc, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
