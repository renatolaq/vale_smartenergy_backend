from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from company.models import AccountType
from django.core.management import call_command

# Create your tests here.


class BudgetTest(APITestCase):
    def test_get_no_filter(self):
        url = '/v1/budget/'

        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 20)
        self.assertEqual(response.data[0]['id'], 83)
        self.assertEqual(response.data[19]['id'], 102)
        self.assertEqual(response._headers['x-total-count'][1], '129')
        self.assertEqual(response._headers['x-total-pages'][1], '7')

    def test_get_paged(self):
        url = '/v1/budget/'

        response = self.client.get(url, data={"perPage": 10, "page": 2 }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 10)
        self.assertEqual(response.data[0]['id'], 93)
        self.assertEqual(response.data[9]['id'], 102)
        self.assertEqual(response._headers['x-total-count'][1], '129')
        self.assertEqual(response._headers['x-total-pages'][1], '13')

    def test_export_no_filter(self):
        url = '/v1/budget/export'

        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_calculate(self):
        url = '/v1/budget/calculateBudget'
        budget_doc = {
            "company": 10189,
            "year": 2021,
            "calculationMode": "Modular",
            "budget": {
                "consumptionLimit": 0.05,
                "contractUsageFactorPeak": 1,
                "contractUsageFactorOffpeak": 1,
                "firstYearBudget": {
                    "january": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": 10,
                        "estimatedOffPeakPowerDemand": 10,
                        "consumptionPeakPowerDemand": 10,
                        "consumptionOffPeakPowerDemand": 10,
                        "production": 5000,
                        "productiveStops": 0
                    },
                    "february": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": 10,
                        "estimatedOffPeakPowerDemand": 10,
                        "consumptionPeakPowerDemand": 10,
                        "consumptionOffPeakPowerDemand": 10,
                        "production": 5000,
                        "productiveStops": 0
                    },
                    "march": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": 10,
                        "estimatedOffPeakPowerDemand": 10,
                        "consumptionPeakPowerDemand": 10,
                        "consumptionOffPeakPowerDemand": 10,
                        "production": 5000,
                        "productiveStops": 0
                    },
                    "april": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": 10,
                        "estimatedOffPeakPowerDemand": 10,
                        "consumptionPeakPowerDemand": 10,
                        "consumptionOffPeakPowerDemand": 10,
                        "production": 5000,
                        "productiveStops": 0
                    },
                    "may": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": 10,
                        "estimatedOffPeakPowerDemand": 10,
                        "consumptionPeakPowerDemand": 10,
                        "consumptionOffPeakPowerDemand": 10,
                        "production": 5000,
                        "productiveStops": 0
                    },
                    "june": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": 10,
                        "estimatedOffPeakPowerDemand": 10,
                        "consumptionPeakPowerDemand": 10,
                        "consumptionOffPeakPowerDemand": 10,
                        "production": 5000,
                        "productiveStops": 0
                    },
                    "july": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": 10,
                        "estimatedOffPeakPowerDemand": 10,
                        "consumptionPeakPowerDemand": 10,
                        "consumptionOffPeakPowerDemand": 10,
                        "production": 5000,
                        "productiveStops": 0
                    },
                    "august": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": 10,
                        "estimatedOffPeakPowerDemand": 10,
                        "consumptionPeakPowerDemand": 10,
                        "consumptionOffPeakPowerDemand": 10,
                        "production": 5000,
                        "productiveStops": 0
                    },
                    "september": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": 10,
                        "estimatedOffPeakPowerDemand": 10,
                        "consumptionPeakPowerDemand": 10,
                        "consumptionOffPeakPowerDemand": 10,
                        "production": 5000,
                        "productiveStops": 0
                    },
                    "october": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": 10,
                        "estimatedOffPeakPowerDemand": 10,
                        "consumptionPeakPowerDemand": 10,
                        "consumptionOffPeakPowerDemand": 10,
                        "production": 5000,
                        "productiveStops": 0
                    },
                    "november": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": 10,
                        "estimatedOffPeakPowerDemand": 10,
                        "consumptionPeakPowerDemand": 10,
                        "consumptionOffPeakPowerDemand": 10,
                        "production": 5000,
                        "productiveStops": 0
                    },
                    "december": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": 10,
                        "estimatedOffPeakPowerDemand": 10,
                        "consumptionPeakPowerDemand": 10,
                        "consumptionOffPeakPowerDemand": 10,
                        "production": 5000,
                        "productiveStops": 0
                    },
                    "total": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": 0.8333333333333334,
                        "estimatedOffPeakPowerDemand": 0.8333333333333334,
                        "consumptionPeakPowerDemand": 10,
                        "consumptionOffPeakPowerDemand": 10,
                        "production": 5000,
                        "productiveStops": 0
                    }
                },
                "secondYearBudget": {
                    "january": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": None,
                        "estimatedOffPeakPowerDemand": None,
                        "consumptionPeakPowerDemand": None,
                        "consumptionOffPeakPowerDemand": None,
                        "production": None,
                        "productiveStops": None
                    },
                    "february": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": None,
                        "estimatedOffPeakPowerDemand": None,
                        "consumptionPeakPowerDemand": None,
                        "consumptionOffPeakPowerDemand": None,
                        "production": None,
                        "productiveStops": None
                    },
                    "march": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": None,
                        "estimatedOffPeakPowerDemand": None,
                        "consumptionPeakPowerDemand": None,
                        "consumptionOffPeakPowerDemand": None,
                        "production": None,
                        "productiveStops": None
                    },
                    "april": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": None,
                        "estimatedOffPeakPowerDemand": None,
                        "consumptionPeakPowerDemand": None,
                        "consumptionOffPeakPowerDemand": None,
                        "production": None,
                        "productiveStops": None
                    },
                    "may": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": None,
                        "estimatedOffPeakPowerDemand": None,
                        "consumptionPeakPowerDemand": None,
                        "consumptionOffPeakPowerDemand": None,
                        "production": None,
                        "productiveStops": None
                    },
                    "june": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": None,
                        "estimatedOffPeakPowerDemand": None,
                        "consumptionPeakPowerDemand": None,
                        "consumptionOffPeakPowerDemand": None,
                        "production": None,
                        "productiveStops": None
                    },
                    "july": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": None,
                        "estimatedOffPeakPowerDemand": None,
                        "consumptionPeakPowerDemand": None,
                        "consumptionOffPeakPowerDemand": None,
                        "production": None,
                        "productiveStops": None
                    },
                    "august": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": None,
                        "estimatedOffPeakPowerDemand": None,
                        "consumptionPeakPowerDemand": None,
                        "consumptionOffPeakPowerDemand": None,
                        "production": None,
                        "productiveStops": None
                    },
                    "september": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": None,
                        "estimatedOffPeakPowerDemand": None,
                        "consumptionPeakPowerDemand": None,
                        "consumptionOffPeakPowerDemand": None,
                        "production": None,
                        "productiveStops": None
                    },
                    "october": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": None,
                        "estimatedOffPeakPowerDemand": None,
                        "consumptionPeakPowerDemand": None,
                        "consumptionOffPeakPowerDemand": None,
                        "production": None,
                        "productiveStops": None
                    },
                    "november": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": None,
                        "estimatedOffPeakPowerDemand": None,
                        "consumptionPeakPowerDemand": None,
                        "consumptionOffPeakPowerDemand": None,
                        "production": None,
                        "productiveStops": None
                    },
                    "december": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": None,
                        "estimatedOffPeakPowerDemand": None,
                        "consumptionPeakPowerDemand": None,
                        "consumptionOffPeakPowerDemand": None,
                        "production": None,
                        "productiveStops": None
                    },
                    "total": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": None,
                        "estimatedOffPeakPowerDemand": None,
                        "consumptionPeakPowerDemand": None,
                        "consumptionOffPeakPowerDemand": None,
                        "production": None,
                        "productiveStops": None
                    }
                },
                "thirdYearBudget": {
                    "contractedPeakPowerDemand": 46000,
                    "contractedOffPeakPowerDemand": 48000,
                    "estimatedPeakPowerDemand": None,
                    "estimatedOffPeakPowerDemand": None,
                    "consumptionPeakPowerDemand": None,
                    "consumptionOffPeakPowerDemand": None,
                    "production": None,
                    "productiveStops": None
                },
                "fourthYearBudget": {
                    "contractedPeakPowerDemand": 46000,
                    "contractedOffPeakPowerDemand": 48000,
                    "estimatedPeakPowerDemand": None,
                    "estimatedOffPeakPowerDemand": None,
                    "consumptionPeakPowerDemand": None,
                    "consumptionOffPeakPowerDemand": None,
                    "production": None,
                    "productiveStops": None
                },
                "fifthYearBudget": {
                    "contractedPeakPowerDemand": 46000,
                    "contractedOffPeakPowerDemand": 48000,
                    "estimatedPeakPowerDemand": None,
                    "estimatedOffPeakPowerDemand": None,
                    "consumptionPeakPowerDemand": None,
                    "consumptionOffPeakPowerDemand": None,
                    "production": None,
                    "productiveStops": None
                }
            }
        }

        response = self.client.post(url, data=budget_doc, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_autofilled_fields(self):
        url = '/v1/budget/10189/2021/autofilledFields'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_budget(self):
        url = '/v1/budget/130'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_create(self):
        url = '/v1/budget/'
        budget_doc = {
            "company": 10189,
            "year": 2021,
            "baseRevision": None,
            "calculationMode": "Modular",
            "budget": {
                "consumptionLimit": 0.05,
                "contractUsageFactorPeak": 1,
                "contractUsageFactorOffpeak": 1,
                "firstYearBudget": {
                    "january": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": 10,
                        "estimatedOffPeakPowerDemand": 10,
                        "consumptionPeakPowerDemand": 10,
                        "consumptionOffPeakPowerDemand": 10,
                        "production": 5000,
                        "productiveStops": 0
                    },
                    "february": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": 10,
                        "estimatedOffPeakPowerDemand": 10,
                        "consumptionPeakPowerDemand": 10,
                        "consumptionOffPeakPowerDemand": 10,
                        "production": 5000,
                        "productiveStops": 0
                    },
                    "march": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": 10,
                        "estimatedOffPeakPowerDemand": 10,
                        "consumptionPeakPowerDemand": 10,
                        "consumptionOffPeakPowerDemand": 10,
                        "production": 5000,
                        "productiveStops": 0
                    },
                    "april": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": 10,
                        "estimatedOffPeakPowerDemand": 10,
                        "consumptionPeakPowerDemand": 10,
                        "consumptionOffPeakPowerDemand": 10,
                        "production": 5000,
                        "productiveStops": 0
                    },
                    "may": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": 10,
                        "estimatedOffPeakPowerDemand": 10,
                        "consumptionPeakPowerDemand": 10,
                        "consumptionOffPeakPowerDemand": 10,
                        "production": 5000,
                        "productiveStops": 0
                    },
                    "june": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": 10,
                        "estimatedOffPeakPowerDemand": 10,
                        "consumptionPeakPowerDemand": 10,
                        "consumptionOffPeakPowerDemand": 10,
                        "production": 5000,
                        "productiveStops": 0
                    },
                    "july": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": 10,
                        "estimatedOffPeakPowerDemand": 10,
                        "consumptionPeakPowerDemand": 10,
                        "consumptionOffPeakPowerDemand": 10,
                        "production": 5000,
                        "productiveStops": 0
                    },
                    "august": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": 10,
                        "estimatedOffPeakPowerDemand": 10,
                        "consumptionPeakPowerDemand": 10,
                        "consumptionOffPeakPowerDemand": 10,
                        "production": 5000,
                        "productiveStops": 0
                    },
                    "september": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": 10,
                        "estimatedOffPeakPowerDemand": 10,
                        "consumptionPeakPowerDemand": 10,
                        "consumptionOffPeakPowerDemand": 10,
                        "production": 5000,
                        "productiveStops": 0
                    },
                    "october": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": 10,
                        "estimatedOffPeakPowerDemand": 10,
                        "consumptionPeakPowerDemand": 10,
                        "consumptionOffPeakPowerDemand": 10,
                        "production": 5000,
                        "productiveStops": 0
                    },
                    "november": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": 10,
                        "estimatedOffPeakPowerDemand": 10,
                        "consumptionPeakPowerDemand": 10,
                        "consumptionOffPeakPowerDemand": 10,
                        "production": 5000,
                        "productiveStops": 0
                    },
                    "december": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": 10,
                        "estimatedOffPeakPowerDemand": 10,
                        "consumptionPeakPowerDemand": 10,
                        "consumptionOffPeakPowerDemand": 10,
                        "production": 5000,
                        "productiveStops": 0
                    },
                    "total": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": 10,
                        "estimatedOffPeakPowerDemand": 10,
                        "consumptionPeakPowerDemand": 120,
                        "consumptionOffPeakPowerDemand": 120,
                        "production": 60000,
                        "productiveStops": 0
                    }
                },
                "secondYearBudget": {
                    "january": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": None,
                        "estimatedOffPeakPowerDemand": None,
                        "consumptionPeakPowerDemand": None,
                        "consumptionOffPeakPowerDemand": None,
                        "production": None,
                        "productiveStops": None
                    },
                    "february": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": None,
                        "estimatedOffPeakPowerDemand": None,
                        "consumptionPeakPowerDemand": None,
                        "consumptionOffPeakPowerDemand": None,
                        "production": None,
                        "productiveStops": None
                    },
                    "march": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": None,
                        "estimatedOffPeakPowerDemand": None,
                        "consumptionPeakPowerDemand": None,
                        "consumptionOffPeakPowerDemand": None,
                        "production": None,
                        "productiveStops": None
                    },
                    "april": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": None,
                        "estimatedOffPeakPowerDemand": None,
                        "consumptionPeakPowerDemand": None,
                        "consumptionOffPeakPowerDemand": None,
                        "production": None,
                        "productiveStops": None
                    },
                    "may": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": None,
                        "estimatedOffPeakPowerDemand": None,
                        "consumptionPeakPowerDemand": None,
                        "consumptionOffPeakPowerDemand": None,
                        "production": None,
                        "productiveStops": None
                    },
                    "june": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": None,
                        "estimatedOffPeakPowerDemand": None,
                        "consumptionPeakPowerDemand": None,
                        "consumptionOffPeakPowerDemand": None,
                        "production": None,
                        "productiveStops": None
                    },
                    "july": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": None,
                        "estimatedOffPeakPowerDemand": None,
                        "consumptionPeakPowerDemand": None,
                        "consumptionOffPeakPowerDemand": None,
                        "production": None,
                        "productiveStops": None
                    },
                    "august": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": None,
                        "estimatedOffPeakPowerDemand": None,
                        "consumptionPeakPowerDemand": None,
                        "consumptionOffPeakPowerDemand": None,
                        "production": None,
                        "productiveStops": None
                    },
                    "september": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": None,
                        "estimatedOffPeakPowerDemand": None,
                        "consumptionPeakPowerDemand": None,
                        "consumptionOffPeakPowerDemand": None,
                        "production": None,
                        "productiveStops": None
                    },
                    "october": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": None,
                        "estimatedOffPeakPowerDemand": None,
                        "consumptionPeakPowerDemand": None,
                        "consumptionOffPeakPowerDemand": None,
                        "production": None,
                        "productiveStops": None
                    },
                    "november": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": None,
                        "estimatedOffPeakPowerDemand": None,
                        "consumptionPeakPowerDemand": None,
                        "consumptionOffPeakPowerDemand": None,
                        "production": None,
                        "productiveStops": None
                    },
                    "december": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": None,
                        "estimatedOffPeakPowerDemand": None,
                        "consumptionPeakPowerDemand": None,
                        "consumptionOffPeakPowerDemand": None,
                        "production": None,
                        "productiveStops": None
                    },
                    "total": {
                        "contractedPeakPowerDemand": 46000,
                        "contractedOffPeakPowerDemand": 48000,
                        "estimatedPeakPowerDemand": None,
                        "estimatedOffPeakPowerDemand": None,
                        "consumptionPeakPowerDemand": None,
                        "consumptionOffPeakPowerDemand": None,
                        "production": None,
                        "productiveStops": None
                    }
                },
                "thirdYearBudget": {
                    "contractedPeakPowerDemand": 46000,
                    "contractedOffPeakPowerDemand": 48000,
                    "estimatedPeakPowerDemand": None,
                    "estimatedOffPeakPowerDemand": None,
                    "consumptionPeakPowerDemand": None,
                    "consumptionOffPeakPowerDemand": None,
                    "production": None,
                    "productiveStops": None
                },
                "fourthYearBudget": {
                    "contractedPeakPowerDemand": 46000,
                    "contractedOffPeakPowerDemand": 48000,
                    "estimatedPeakPowerDemand": None,
                    "estimatedOffPeakPowerDemand": None,
                    "consumptionPeakPowerDemand": None,
                    "consumptionOffPeakPowerDemand": None,
                    "production": None,
                    "productiveStops": None
                },
                "fifthYearBudget": {
                    "contractedPeakPowerDemand": 46000,
                    "contractedOffPeakPowerDemand": 48000,
                    "estimatedPeakPowerDemand": None,
                    "estimatedOffPeakPowerDemand": None,
                    "consumptionPeakPowerDemand": None,
                    "consumptionOffPeakPowerDemand": None,
                    "production": None,
                    "productiveStops": None
                }
            }
        }

        response = self.client.post(url, data=budget_doc, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_workflow(self):
        url = '/v1/budget/46/releaseToAnalysis'
        response = self.client.post(url, data={"message": "Teste"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        url = '/v1/budget/46/releaseToOperationalManagerApproval'
        response = self.client.post(url, data={"message": "Teste"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


        url = '/v1/budget/46/operationalManagerApprove'
        response = self.client.post(url, data={"message": "Teste"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        url = '/v1/budget/46/energyManagerApprove'
        response = self.client.post(url, data={"message": "Teste"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        url = '/v1/budget/46/disapprove'
        response = self.client.post(url, data={"message": "Teste"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        
