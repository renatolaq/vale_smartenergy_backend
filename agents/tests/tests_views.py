from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.db import transaction
from agents.serializers import CCEESerializerAgents
from agents.models import Agents, CceeDescription


# Create your tests here.
class AgentsTest(APITestCase):

    #loads fixtures dependencies
    fixtures = [
        #'core/fixtures/initial_data_dxc.json','company/fixtures/initial_data_dxc.json',
        #'agents/fixtures/initial_data_dxc.json','profiles/fixtures/initial_data_dxc.json'
    ]

    def test_post(self):#OK

        url = '/agents-api/session_agents_post/'
        expected = {
            "code_ccee": 10165,
            "type": "A/P",
            "name_ccee": "Vale Energia",
            "status": "S",
            "ccee_agent": {
                "id_company": 10166,
                "vale_name_agent": "Vale Energia",
                "status": "S"
            }
        }
        response = self.client.post(url, expected, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        #error code_ccee
        expected = {
            "code_ccee": 10165,
            "type": "A/P",
            "name_ccee": "Vale Energia",
            "status": "S",
            "ccee_agent": {
                "id_company": 10166,
                "vale_name_agent": "Vale Energia",
                "status": "S"
            }
        }
        response = self.client.post(url, expected, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        #error code_ccee
        expected = {
            "code_ccee": -121589,
            "type": "A/P",
            "name_ccee": "Vale Energia",
            "status": "S",
            "ccee_agent": {
                "id_company": 10166,
                "vale_name_agent": "Vale Energia",
                "status": "S"
            }
        }
        response = self.client.post(url, expected, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        #error type
        expected = {
            "code_ccee": 6121589,
            "type": "METER",
            "name_ccee": "Vale Energia",
            "status": "S",
            "ccee_agent": {
                "id_company": 10166,
                "vale_name_agent": "Vale Energia",
                "status": "S"
            }
        }
        response = self.client.post(url, expected, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        expected_error = {}
        response = self.client.post(url, expected_error, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get(self):
        urls = ['/agents-api/session_agents/', '/agents-api/session_agents_find_basic/']
        for url in urls:
            response = self.client.get(url, format='json')
            self.assertTrue(status.is_success(response.status_code))

    def test_update(self): #ok
        # exists
        agent = Agents.objects.filter(id_ccee__type='A/P').last()
        url = '/agents-api/session_agents/%s/' % agent.pk
        urlPut = '/agents-api/session_agents_put/%s/' % agent.pk

        expected_error = {}
        response = self.client.get(url)
        self.assertTrue(status.is_success(response.status_code))

        # put
        response = self.client.put(urlPut, response.data, format='json')
        self.assertTrue(status.is_success(response.status_code))

        # put bad request status
        agentRelated=Agents.objects.filter(profile_agent__isnull=False).last()
        urlAgentRelated = '/agents-api/session_agents/%s/' % agentRelated.pk
        response = self.client.get(urlAgentRelated)
        response.data['ccee_agent']['status']='N'
        response.data['observation_log']='Teste'
        response = self.client.put(urlPut, response.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # # put bad request code_ccee
        # response = self.client.get(url)
        # response.data['code_ccee']='-11A1111111'
        # response = self.client.put(urlPut, response.data, format='json')
        # self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


        # put bad request
        response = self.client.put(urlPut, expected_error, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # not found
        url = '/agents-api/session_agents/%s/' % 0
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        urlPut = '/agents-api/session_agents_put/%s/' % 0
        response = self.client.put(urlPut)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_data_agents(self):
        urls = ['/agents-api/get_data_agents/', '/agents-api/get_data_agents_basic/']
        for url in urls:
            response = self.client.get(url, format='json')
            self.assertTrue(status.is_success(response.status_code))


    def test_session_agents_file(self):
        #csv
        url = '/agents-api/session_agents_file/?format_file=csv'
        response = self.client.get(url)
        self.assertTrue(status.is_success(response.status_code))

        #error
        url = '/agents-api/session_agents_file/?format_file=error'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        #error
        url ='/agents-api/session_agents_file/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_log(self):
        agent = Agents.objects.all().last()

        url='/agents-api/session_log_basic_agents/%s/' %agent.pk
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))
    
