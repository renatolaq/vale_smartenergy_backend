from io import StringIO

from organization.serializersViews import OrganizationBusinessSerializerView
from organization.models import Business
from occurrence_record.serializers import AppliedProtectionSerializer, EventSerializer, EventTypeSerializer, OccurrenceAttachmentSerializer, OccurrenceCauseSerializer, OccurrenceSerializer, OccurrenceTypeSerializer
from occurrence_record.models import AppliedProtection, EventType, Event, Occurrence, OccurrenceAttachment, OccurrenceCause, OccurrenceType
from company.serializersViews import CompanySerializerViewBasicData
from company.models import Company
from rest_framework.test import APITestCase
from rest_framework import status


class OccurrenceRecordTest(APITestCase):
    fixtures = [
        'occurrence_record/fixtures/basic_data.json',
        'occurrence_record/fixtures/automated_tests_events.json',
        'occurrence_record/fixtures/automated_tests.json',
        'occurrence_record/fixtures/automated_tests_log.json'
    ]

    def test_simple_post_attachment(self):  
        url = '/occurrence/1/attachment'
        file = StringIO("test content")
        file.name = 'test_file.txt'
        data = {
            "attachment_name": "File Test",
            "attachment_comments": "Comment",
            "attachment_revision": "1.1",
            "attachment": file,
        }
        expected = {
            "attachment_name": "File Test",
            "attachment_comments": "Comment",
            "attachment_revision": "1.1",
            "occurrence": 1
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(expected['attachment_name'],
                         response.data['attachment_name'])
        self.assertEqual(expected['attachment_comments'],
                         response.data['attachment_comments'])
        self.assertEqual(expected['attachment_revision'],
                         response.data['attachment_revision'])
        self.assertEqual(expected['occurrence'], response.data['occurrence'])
        self.assertTrue(bool(response.data['attachment_path']))

    def test_simple_post_attachment_error(self):  
        url = '/occurrence/1/attachment'
        data = {
            "attachment_name": "File Test",
            "attachment_comments": "Comment",
            "attachment_revision": "1.1",
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_simple_post(self):  
        url = '/occurrence'
        data = {"responsible": "Responsible Test",
                "phone": "123123-1231",
                "cellphone": "1231231-2321",
                "carrier": "1",
                "occurrence_date": "2020-12-14T17:18:50.757000Z",
                "occurrence_duration": 46,
                "key_circuit_breaker_identifier": "A323",
                "total_stop_time": 45,
                "description": "Teste",
                "created_date": "2020-12-14T17:18:50.757000Z",
                "status": "S",
                "situation": "draft",
                "company": {
                    "id_company": 10124
                },
                "electrical_grouping": {
                    "id_electrical_grouping": 24
                },
                "events": [
                    {
                        "id_event": 4
                    },
                    {
                        "id_event": 5
                    }
                ],
                "applied_protection": {
                    "id_applied_protection": 2
                },
                "occurrence_type": {
                    "id_occurrence_type": 2
                },
                "occurrence_cause": {
                    "id_occurrence_cause": 22
                },
                "occurrence_business": [
                    {
                        "business": {
                            "id_business": 2
                        }
                    }
                ],
                "occurrence_product": [
                    {
                        "lost_production": 12.000000001,
                        "financial_loss": 98.000000001,
                        "product": {
                            "id_product": 1
                        }
                    }
                ]
                }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.check_post_put_return(response.data, data)

    def test_post_with_manual_event(self):  
        url = '/occurrence'
        data = {"responsible": "Responsible Test",
                "phone": "123123-1231",
                "cellphone": "1231231-2321",
                "carrier": "1",
                "occurrence_date": "2020-12-14T17:18:50.757000Z",
                "occurrence_duration": 46,
                "key_circuit_breaker_identifier": "A323",
                "total_stop_time": 45,
                "description": "Teste",
                "created_date": "2020-12-14T17:18:50.757000Z",
                "status": "S",
                "situation": "draft",
                "company": {
                    "id_company": 10124
                },
                "electrical_grouping": {
                    "id_electrical_grouping": 24
                },
                "manual_events": [
                    {
                        "gauge_point": "teste 1",
                        "event_type": {"id_event_type": 1},
                        "date": '2021-01-01T00:01:02.123456Z',
                        "duration": 1,
                        "magnitude": 2 
                    },
                    {
                        "gauge_point": "teste 2",
                        "event_type": {"id_event_type": 2},
                        "date": '2021-01-01T00:02:02.123456Z',
                        "duration": 2,
                        "magnitude": 3 
                    }
                ],
                "applied_protection": {
                    "id_applied_protection": 2
                },
                "occurrence_type": {
                    "id_occurrence_type": 2
                },
                "occurrence_cause": {
                    "id_occurrence_cause": 22
                },
                "occurrence_business": [
                    {
                        "business": {
                            "id_business": 2
                        }
                    }
                ],
                "occurrence_product": [
                    {
                        "lost_production": 12.000000001,
                        "financial_loss": 98.000000001,
                        "product": {
                            "id_product": 1
                        }
                    }
                ]
                }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.check_post_put_return(response.data, data)
    
    def test_post_occurrence_cause_others(self):  
        url = '/occurrence'
        data = {"responsible": "Responsible Test",
                "phone": "123123-1231",
                "cellphone": "1231231-2321",
                "carrier": "1",
                "occurrence_date": "2020-12-14T17:18:50.757000Z",
                "occurrence_duration": 46,
                "key_circuit_breaker_identifier": "A323",
                "total_stop_time": 45,
                "description": "Teste",
                "created_date": "2020-12-14T17:18:50.757000Z",
                "status": "S",
                "situation": "consolidate",
                "additional_information": "additional information test",
                "company": {
                    "id_company": 10124
                },
                "electrical_grouping": {
                    "id_electrical_grouping": 24
                },
                "events": [
                    {
                        "id_event": 4
                    },
                    {
                        "id_event": 5
                    }
                ],
                "applied_protection": {
                    "id_applied_protection": 2
                },
                "occurrence_type": {
                    "id_occurrence_type": 2
                },
                "occurrence_cause": {
                    "id_occurrence_cause": 24
                },
                "occurrence_business": [
                    {
                        "business": {
                            "id_business": 2
                        }
                    }
                ],
                "occurrence_product": [
                    {
                        "lost_production": 12.000000001,
                        "financial_loss": 98.000000001,
                        "product": {
                            "id_product": 1
                        }
                    }
                ]
                }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.check_post_put_return(response.data, data)
    
    def test_post_occurrence_cause_others_additional_information_less_than_15_char(self):
        url = '/occurrence'
        data = {"responsible": "Responsible Test",
                "phone": "123123-1231",
                "cellphone": "1231231-2321",
                "carrier": "1",
                "occurrence_date": "2020-12-14T17:18:50.757000Z",
                "occurrence_duration": 46,
                "key_circuit_breaker_identifier": "A323",
                "total_stop_time": 45,
                "description": "Teste",
                "created_date": "2020-12-14T17:18:50.757000Z",
                "status": "S",
                "situation": "consolidate",
                "additional_information": "12345678",
                "company": {
                    "id_company": 10124
                },
                "electrical_grouping": {
                    "id_electrical_grouping": 24
                },
                "events": [
                    {
                        "id_event": 4
                    },
                    {
                        "id_event": 5
                    }
                ],
                "applied_protection": {
                    "id_applied_protection": 2
                },
                "occurrence_type": {
                    "id_occurrence_type": 2
                },
                "occurrence_cause": {
                    "id_occurrence_cause": 24
                },
                "occurrence_business": [
                    {
                        "business": {
                            "id_business": 2
                        }
                    }
                ],
                "occurrence_product": [
                    {
                        "lost_production": 12.000000001,
                        "financial_loss": 98.000000001,
                        "product": {
                            "id_product": 1
                        }
                    }
                ]
                }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_post_occurrence_cause_others_no_additional_information(self):
        url = '/occurrence'
        data = {"responsible": "Responsible Test",
                "phone": "123123-1231",
                "cellphone": "1231231-2321",
                "carrier": "1",
                "occurrence_date": "2020-12-14T17:18:50.757000Z",
                "occurrence_duration": 46,
                "key_circuit_breaker_identifier": "A323",
                "total_stop_time": 45,
                "description": "Teste",
                "created_date": "2020-12-14T17:18:50.757000Z",
                "status": "S",
                "situation": "consolidate",
                "company": {
                    "id_company": 10124
                },
                "electrical_grouping": {
                    "id_electrical_grouping": 24
                },
                "events": [
                    {
                        "id_event": 4
                    },
                    {
                        "id_event": 5
                    }
                ],
                "applied_protection": {
                    "id_applied_protection": 2
                },
                "occurrence_type": {
                    "id_occurrence_type": 2
                },
                "occurrence_cause": {
                    "id_occurrence_cause": 24
                },
                "occurrence_business": [
                    {
                        "business": {
                            "id_business": 2
                        }
                    }
                ],
                "occurrence_product": [
                    {
                        "lost_production": 12.000000001,
                        "financial_loss": 98.000000001,
                        "product": {
                            "id_product": 1
                        }
                    }
                ]
                }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_post_occurrence_type_disturbance_occurrence_duration_empty(self):
        url = '/occurrence'
        data = {"responsible": "Responsible Test",
                "phone": "123123-1231",
                "cellphone": "1231231-2321",
                "carrier": "1",
                "occurrence_date": "2020-12-14T17:18:50.757000Z",
                "occurrence_duration": None,
                "key_circuit_breaker_identifier": "A323",
                "total_stop_time": 46,
                "description": "Teste",
                "created_date": "2020-12-14T17:18:50.757000Z",
                "status": "S",
                "situation": "consolidate",
                "additional_information": "additional information test",
                "company": {
                    "id_company": 10124
                },
                "electrical_grouping": {
                    "id_electrical_grouping": 24
                },
                "events": [
                    {
                        "id_event": 4
                    },
                    {
                        "id_event": 5
                    }
                ],
                "applied_protection": {
                    "id_applied_protection": 2
                },
                "occurrence_type": {
                    "id_occurrence_type": 3
                },
                "occurrence_cause": {
                    "id_occurrence_cause": 24
                },
                "occurrence_business": [
                    {
                        "business": {
                            "id_business": 2
                        }
                    }
                ],
                "occurrence_product": [
                    {
                        "lost_production": 12.000000001,
                        "financial_loss": 98.000000001,
                        "product": {
                            "id_product": 1
                        }
                    }
                ]
                }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.check_post_put_return(response.data, data)
    
    def test_post_occurrence_type_not_disturbance_occurrence_duration_empty(self):
        url = '/occurrence'
        data = {"responsible": "Responsible Test",
                "phone": "123123-1231",
                "cellphone": "1231231-2321",
                "carrier": "1",
                "occurrence_date": "2020-12-14T17:18:50.757000Z",
                "occurrence_duration": None,
                "key_circuit_breaker_identifier": "A323",
                "total_stop_time": 50,
                "description": "Teste",
                "created_date": "2020-12-14T17:18:50.757000Z",
                "status": "S",
                "situation": "consolidate",
                "additional_information": "additional information test",
                "company": {
                    "id_company": 10124
                },
                "electrical_grouping": {
                    "id_electrical_grouping": 24
                },
                "events": [
                    {
                        "id_event": 4
                    },
                    {
                        "id_event": 5
                    }
                ],
                "applied_protection": {
                    "id_applied_protection": 2
                },
                "occurrence_type": {
                    "id_occurrence_type": 2
                },
                "occurrence_cause": {
                    "id_occurrence_cause": 24
                },
                "occurrence_business": [
                    {
                        "business": {
                            "id_business": 2
                        }
                    }
                ],
                "occurrence_product": [
                    {
                        "lost_production": 12.000000001,
                        "financial_loss": 98.000000001,
                        "product": {
                            "id_product": 1
                        }
                    }
                ]
                }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_occurrence_type_not_disturbance(self):  
        url = '/occurrence'
        data = {"responsible": "Responsible Test",
                "phone": "123123-1231",
                "cellphone": "1231231-2321",
                "carrier": "1",
                "occurrence_date": "2020-12-14T17:18:50.757000Z",
                "occurrence_duration": 46,
                "key_circuit_breaker_identifier": "A323",
                "total_stop_time": 5,
                "description": "Teste",
                "created_date": "2020-12-14T17:18:50.757000Z",
                "status": "S",
                "situation": "consolidate",
                "additional_information": "additional information test",
                "company": {
                    "id_company": 10124
                },
                "electrical_grouping": {
                    "id_electrical_grouping": 24
                },
                "events": [
                    {
                        "id_event": 4
                    },
                    {
                        "id_event": 5
                    }
                ],
                "applied_protection": {
                    "id_applied_protection": 2
                },
                "occurrence_type": {
                    "id_occurrence_type": 2
                },
                "occurrence_cause": {
                    "id_occurrence_cause": 24
                },
                "occurrence_business": [
                    {
                        "business": {
                            "id_business": 2
                        }
                    }
                ],
                "occurrence_product": [
                    {
                        "lost_production": 12.000000001,
                        "financial_loss": 98.000000001,
                        "product": {
                            "id_product": 1
                        }
                    }
                ]
                }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.check_post_put_return(response.data, data)

    def test_simple_put(self):  
        url = '/occurrence/2'
        data = {
            "responsible": "TesteAutomated1",
            "phone": "11",
            "cellphone": "11",
            "carrier": "1",
            "occurrence_date": "2020-12-22T17:18:50.757000Z",
            "occurrence_duration": 50,
            "key_circuit_breaker_identifier": "A323",
            "total_stop_time": 50,
            "description": "Teste",
            "created_date": "2020-12-14T17:18:50.757000Z",
            "status": "S",
            "situation": "draft",
            "company": {
                "id_company": 10123
            },
            "electrical_grouping": {
                "id_electrical_grouping": 24
            },
            "events": [
                {
                    "id_event": 1,
                }
            ],
            "applied_protection": {
                "id_applied_protection": 2
            },
            "occurrence_type": {
                "id_occurrence_type": 2
            },
            "occurrence_cause": {
                "id_occurrence_cause": 22
            },
            "occurrence_business": [
                {
                    "id_occurrence_business": 2,
                    "business": {
                        "id_business": 1
                    }
                }
            ],
            "occurrence_product": [
                {
                    "id_occurrence_product": 3,
                    "lost_production": 10,
                    "financial_loss": 90,
                    "product": {
                        "id_product": 2
                    }
                }
            ]
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.check_post_put_return(response.data, data)

    def test_put_remove_event(self):  
        url = '/occurrence/2'
        data = {
            "responsible": "TesteAutomated1",
            "phone": "11",
            "cellphone": "11",
            "carrier": "1",
            "occurrence_date": "2020-12-22T17:18:50.757000Z",
            "occurrence_duration": 50,
            "key_circuit_breaker_identifier": "A323",
            "total_stop_time": 50,
            "description": "Teste",
            "created_date": "2020-12-14T17:18:50.757000Z",
            "status": "S",
            "situation": "draft",
            "company": {
                "id_company": 10123
            },
            "electrical_grouping": {
                "id_electrical_grouping": 24
            },
            "events": [],
            "applied_protection": {
                "id_applied_protection": 2
            },
            "occurrence_type": {
                "id_occurrence_type": 2
            },
            "occurrence_cause": {
                "id_occurrence_cause": 22
            },
            "occurrence_business": [
                {
                    "id_occurrence_business": 2,
                    "business": {
                        "id_business": 1
                    }
                }
            ],
            "occurrence_product": [
                {
                    "id_occurrence_product": 3,
                    "lost_production": 10,
                    "financial_loss": 90,
                    "product": {
                        "id_product": 2
                    }
                }
            ]
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.check_post_put_return(response.data, data)

    def test_put_add_events(self):  
        url = '/occurrence/2'
        data = {
            "responsible": "TesteAutomated1",
            "phone": "11",
            "cellphone": "11",
            "carrier": "1",
            "occurrence_date": "2020-12-22T17:18:50.757000Z",
            "occurrence_duration": 50,
            "key_circuit_breaker_identifier": "A323",
            "total_stop_time": 50,
            "description": "Teste",
            "created_date": "2020-12-14T17:18:50.757000Z",
            "status": "S",
            "situation": "draft",
            "company": {
                "id_company": 10123
            },
            "electrical_grouping": {
                "id_electrical_grouping": 24
            },
            "events": [
                {
                    "id_event": 5
                }, {
                    "id_event": 6
                }],
            "applied_protection": {
                "id_applied_protection": 2
            },
            "occurrence_type": {
                "id_occurrence_type": 2
            },
            "occurrence_cause": {
                "id_occurrence_cause": 22
            },
            "occurrence_business": [
                {
                    "id_occurrence_business": 2,
                    "business": {
                        "id_business": 1
                    }
                }
            ],
            "occurrence_product": [
                {
                    "id_occurrence_product": 3,
                    "lost_production": 10,
                    "financial_loss": 90,
                    "product": {
                        "id_product": 2
                    }
                }
            ]
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.check_post_put_return(response.data, data)

    def test_put_add_and_remove_events(self):  
        url = '/occurrence/3'
        data = {
            "responsible": "TesteAutomated1",
            "phone": "11",
            "cellphone": "11",
            "carrier": "1",
            "occurrence_date": "2020-12-22T17:18:50.757000Z",
            "occurrence_duration": 50,
            "key_circuit_breaker_identifier": "A323",
            "total_stop_time": 50,
            "description": "Teste",
            "created_date": "2020-12-14T17:18:50.757000Z",
            "status": "S",
            "situation": "draft",
            "company": {
                "id_company": 10123
            },
            "electrical_grouping": {
                "id_electrical_grouping": 24
            },
            "events": [
                {
                    "id_event": 2,
                },
                {
                    "id_event": 4,
                },
                {
                    "id_event": 5,
                }
            ],
            "applied_protection": {
                "id_applied_protection": 2
            },
            "occurrence_type": {
                "id_occurrence_type": 2
            },
            "occurrence_cause": {
                "id_occurrence_cause": 22
            },
            "occurrence_business": [
                {
                    "id_occurrence_business": 2,
                    "business": {
                        "id_business": 1
                    }
                }
            ],
            "occurrence_product": [
                {
                    "id_occurrence_product": 3,
                    "lost_production": 10,
                    "financial_loss": 90,
                    "product": {
                        "id_product": 2
                    }
                }
            ]
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.check_post_put_return(response.data, data)
    
    def test_get_event_list_page1(self):  
        url = '/occurrence/event?page_size=2&page=1'

        def assets(data):
            self.assertEqual(len(data['results']), 2)
            self.assertEqual(data['count'], 10)
            self.assertEqual(data['results'], self.get_events()[:2])
        self.simple_get_test_lambda(url, status.HTTP_200_OK, assets)

    def test_get_event_list_page2(self):  
        url = '/occurrence/event?page_size=2&page=2'

        def assets(data):
            self.assertEqual(len(data['results']), 2)
            self.assertEqual(data['count'], 10)
            self.assertEqual(data['results'], self.get_events()[2:4])
        self.simple_get_test_lambda(url, status.HTTP_200_OK, assets)

    def test_get_occurence_list_page1(self):  
        url = '/occurrence?page_size=2&page=1'

        def assets(data):
            self.assertEqual(len(data['results']), 2)
            self.assertEqual(data['count'], 3)
            self.assertEqual(data['results'], self.get_occurrences()[:2])
        self.simple_get_test_lambda(url, status.HTTP_200_OK, assets)

    def test_get_occurence_list_page2(self):  
        url = '/occurrence?page_size=2&page=2'

        def assets(data):
            self.assertEqual(len(data['results']), 1)
            self.assertEqual(data['count'], 3)
            self.assertEqual(data['results'], self.get_occurrences()[2:4])
        self.simple_get_test_lambda(url, status.HTTP_200_OK, assets)

    def test_get_occurence_1(self):  
        url = '/occurrence/1'
        self.simple_get_test(url, status.HTTP_200_OK,
                             self.get_occurrences()[0])

    def test_get_occurence_2(self):  
        url = '/occurrence/2'
        self.simple_get_test(url, status.HTTP_200_OK,
                             self.get_occurrences()[1])

    def test_get_occurence_with_error(self):  
        url = '/occurrence/34'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_attachment(self):  
        url = '/occurrence/2/attachment'
        attach = list(
            filter(lambda x: x['occurrence'] == 2, self.get_attachment()))
        self.simple_get_test(url, status.HTTP_200_OK, attach)

    def test_get_report(self):
        url = '/occurrence/report?format_file=pdf'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        url = '/occurrence/report?format_file=xlsx'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        url = '/occurrence/report?format_file=csv'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_report_with_incorrect_format(self):
        url = '/occurrence/report?format_file=jpeg'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["errors"]
                         [0]["code"], "ERROR_FORMAT_FILE")

    def test_get_report_without_format(self):
        url = '/occurrence/report?format_file='
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["errors"]
                         [0]["code"], "ERROR_FORMAT_FILE")

    def test_get_log(self):  
        url = '/occurrence/1/log'

        def assets(data):
            self.assertEqual(len(data['logs']), 1)
            self.assertEqual(len(data['static_relateds']), 7)
        self.simple_get_test_lambda(url, status.HTTP_200_OK, assets)

    def test_get_company_with_sepp_participation(self):  
        url = '/occurrence/company/withSEPP'
        self.simple_get_test(url, status.HTTP_200_OK, self.get_companies())

    def test_get_cause(self):  
        url = '/occurrence/cause'
        self.simple_get_test(url, status.HTTP_200_OK, self.get_causes())

    def test_get_type(self):  
        url = '/occurrence/type'
        self.simple_get_test(url, status.HTTP_200_OK, self.get_types())

    def test_get_applied_protection(self):  
        url = '/occurrence/appliedProtection'
        self.simple_get_test(url, status.HTTP_200_OK,
                             self.get_applied_protections())

    def test_get_event_type(self):  
        url = '/occurrence/event/type'
        self.simple_get_test(url, status.HTTP_200_OK, self.get_event_types())

    def test_get_event_valid_business(self):  
        url = '/occurrence/event/validBusiness?id_events=2'
        self.simple_get_test(url, status.HTTP_200_OK,
                             self.get_event_valid_business())

    def test_dashboard(self):
        url = '/occurrence/dashboard'
        # self.simple_get_test(url, status.HTTP_200_OK, self.post_dashboard())
        for num in [1, 2, 3, 4]:
            json_dashBoard = {
                "period": {
                    "start": "2020-01-01T17:00:00.757000Z",
                    "end":  "2020-12-10T17:18:00.757000Z"
                },
                "chartOptionQuantityOccurrence": {
                    "parametrization": {
                        "checked": True,
                        "type": "0",
                        "grouping": "%s" % num,
                        "stackUpOccurrenceType": {
                            "1": True,
                            "2": True,
                            "3": True
                        }
                    },
                    "byGeneratorFact": {
                        "checked": True,
                        "type": "1"
                    }
                },
                "chartOptionTimeStopProduction": {
                    "parametrization": {
                        "checked": True,
                        "type": "0",
                        "grouping": "%s" % num,
                        "stackUpOccurrenceType": {
                            "1": True,
                            "2": True,
                            "3": True
                        }
                    },
                    "byGeneratorFact": {
                        "checked": True,
                        "type": "1"
                    }
                }
            }
            response = self.client.post(url, json_dashBoard, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def simple_get_test(self, url, expected_status_code, expected_response):
        response = self.client.get(url)
        self.assertEqual(response.status_code, expected_status_code)
        self.assertEqual(response.data, expected_response)
        return response

    def simple_get_test_lambda(self, url, expected_status_code, test_callback):
        response = self.client.get(url)
        self.assertEqual(response.status_code, expected_status_code)
        test_callback(response.data)
        return response

    def check_post_put_return(self, response_data, send_data):

        self.assertEqual(send_data['responsible'],
                         response_data['responsible'])
        self.assertEqual(send_data['phone'], response_data['phone'])
        self.assertEqual(send_data['cellphone'], response_data['cellphone'])
        self.assertEqual(send_data['carrier'], response_data['carrier'])
        self.assertEqual(send_data['occurrence_date'],
                         response_data['occurrence_date'])
        self.assertEqual(send_data['occurrence_duration'],
                         response_data['occurrence_duration'])
        self.assertEqual(send_data['key_circuit_breaker_identifier'],
                         response_data['key_circuit_breaker_identifier'])
        self.assertEqual(send_data.get('total_stop_time'),
                         response_data.get('total_stop_time'))
        self.assertEqual(send_data['description'],
                         response_data['description'])
        self.assertEqual(send_data['status'], response_data['status'])
        self.assertEqual(send_data['situation'], response_data['situation'])
        self.assertEqual(send_data.get('additional_information'),
                         response_data.get('additional_information'))
        self.assertEqual(send_data['company']['id_company'],
                         response_data['company']['id_company'])
        self.assertEqual(send_data['electrical_grouping']['id_electrical_grouping'],
                         response_data['electrical_grouping']['id_electrical_grouping'])
        self.assertEqual(send_data['applied_protection']['id_applied_protection'],
                         response_data['applied_protection']['id_applied_protection'])
        self.assertEqual(send_data['occurrence_type']['id_occurrence_type'],
                         response_data['occurrence_type']['id_occurrence_type'])
        self.assertEqual(send_data['occurrence_cause']['id_occurrence_cause'],
                         response_data['occurrence_cause']['id_occurrence_cause'])
        self.assertEqual(len(send_data.get('events') or []),
                         len(response_data.get('events') or []))
        self.assertEqual(len(send_data.get('manual_events') or []),
                         len(response_data.get('manual_events') or []))
        self.assertEqual(len(send_data['occurrence_business']), len(
            response_data['occurrence_business']))
        self.assertEqual(len(send_data['occurrence_product']), len(
            response_data['occurrence_product']))

        for event_send in send_data.get('events') or []:
            event_response = next(filter(
                lambda x: x['id_event'] == event_send['id_event'], response_data['events']))
            self.assertIsNotNone(event_response)

        for i, event_send in enumerate(send_data.get('manual_events') or []):
            event_response = response_data['manual_events'][i]
            self.assertIsNotNone(event_response)
            self.assertEqual(
                event_send['gauge_point'], event_response['gauge_point'])
            self.assertEqual(
                event_send['event_type']['id_event_type'], event_response['event_type']['id_event_type'])
            self.assertEqual(
                event_send['date'], event_response['date'])
            self.assertEqual(
                event_send['duration'], event_response['duration'])
            self.assertEqual(
                event_send['magnitude'], event_response['magnitude'])

        for business_send in response_data['occurrence_business']:
            business_response = next(filter(
                lambda x: x['business']['id_business'] == business_send['business']['id_business'], response_data['occurrence_business']))
            self.assertIsNotNone(business_response)

        for product_send in response_data['occurrence_product']:
            product_response = next(filter(
                lambda x: x['product']['id_product'] == product_send['product']['id_product'], response_data['occurrence_product']))
            self.assertIsNotNone(product_response)
            self.assertEqual(
                product_send['lost_production'], product_response['lost_production'])
            self.assertEqual(
                product_send['financial_loss'], product_response['financial_loss'])

    def get_events(self):
        query = Event.objects.all()
        return EventSerializer(query, many=True).data

    def get_occurrences(self):
        query = Occurrence.objects.all()
        return OccurrenceSerializer(query, many=True).data

    def get_companies(self):
        query = Company.objects.filter(
            gauge_company__participation_sepp='S',
            gauge_company__status='S').order_by('company_name').distinct()
        return CompanySerializerViewBasicData(query, many=True).data

    def get_causes(self):
        query = OccurrenceCause.objects.all().order_by('description')
        return OccurrenceCauseSerializer(query, many=True).data

    def get_types(self):
        query = OccurrenceType.objects.all().order_by('description')
        return OccurrenceTypeSerializer(query, many=True).data

    def get_applied_protections(self):
        query = AppliedProtection.objects.all().order_by('description')
        return AppliedProtectionSerializer(query, many=True).data

    def get_event_types(self):
        query = EventType.objects.all().order_by('name_event_type')
        return EventTypeSerializer(query, many=True).data

    def get_event_valid_business(self):
        query = Business.objects.filter(
            business_energyComposition__id_company__gauge_company__gaugePoint_pqEvents=2)
        return OrganizationBusinessSerializerView(query, many=True).data

    def get_attachment(self):
        query = OccurrenceAttachment.objects.all()
        return OccurrenceAttachmentSerializer(query, many=True).data
