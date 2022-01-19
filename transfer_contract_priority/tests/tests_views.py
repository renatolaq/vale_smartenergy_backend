from rest_framework import status
from rest_framework.test import APITestCase

from transfer_contract_priority.models import TransferContractPriority


class TransferContractPriorityTest(APITestCase):
    # loads fixtures dependencies
    fixtures = [
        'core/fixtures/initial_data.json', 'company/fixtures/initial_data.json', 
        'agents/fixtures/initial_data.json', 'profiles/fixtures/initial_data.json', 
        'organization/fixtures/initial_data_dxc.json', 'gauge_point/fixtures/initial_data.json', 
        'energy_composition/fixtures/initial_data.json', 'assets/fixtures/initial_data.json', 
        'asset_items/fixtures/initial_data.json', 'energy_contract/fixtures/initial_data.json', 
        'cliq_contract/fixtures/initial_data.json', 'transfer_contract_priority/fixtures/initial_data.json'
    ]

    def test_get(self):  
        url = '/transfer_contract_priority-api/session_transfer_contract_priority/'
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

    def test_get_find(self):  
        url_find = '/transfer_contract_priority-api/session_transfer_contract_priority/?contract_name=XXX_V,V_AV_AC_Di_Df_X&code_ccee=1234567890& \
                                                                                    buyer_profile=Matheus%20M.&vendor_profile=Juliana&transaction_type=tipo%20trans& \
                                                                                    priority_number=1'
        response = self.client.get(url_find, format='json')
        self.assertTrue(status.is_success(response.status_code))

        url_find = '/transfer_contract_priority-api/session_transfer_contract_priority/?contract_name=XXX_V,V_AV_AC_Di_Df_X&code_ccee=1234567890& \
                                                                                    buyer_profile=Matheus%20M.&vendor_profile=Juliana&transaction_type=tipo%20trans& \
                                                                                    priority_number=15&ordering=priority_number'
        response = self.client.get(url_find, format='json')
        self.assertTrue(status.is_success(response.status_code))

    def test_Log_transfer(self):
        transferContractPriority = TransferContractPriority.objects.last()
        url = '/transfer_contract_priority-api/session_log_transfer_contract_priority/%s/' % transferContractPriority.pk
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

    def test_post_contract_priority_reorder(self):
        url='/transfer_contract_priority-api/session_transfer_contract_priority_reorder/'

        transfer_obj=TransferContractPriority.objects.all()

        expected={
                "id_transfer":transfer_obj[4].pk,
                "new_priority_number": int(transfer_obj[4].priority_number+1)
        }
        response = self.client.post(url, expected, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected={
                "id_transfer":transfer_obj[9].pk,
                "new_priority_number": int(transfer_obj[9].priority_number-2)
        }
        response = self.client.post(url, expected, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        #Range 
        expected={
            "id_transfer":transfer_obj[1].pk,
            "new_priority_number": int(TransferContractPriority.objects.filter(status='S').count()+3)
        }
        response = self.client.post(url, expected, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        #not found
        expected={
            "id_transfer":0,
            "new_priority_number": 3
        }
        response = self.client.post(url, expected, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_file_transfer(self):
        url_find = '/transfer_contract_priority-api/session_transfer_contract_priority_export_file/?format_file=csv'
        response = self.client.get(url_find)
        self.assertTrue(status.is_success(response.status_code))

        url_find = '/transfer_contract_priority-api/session_transfer_contract_priority_export_file/?format_file=xlsx'
        response = self.client.get(url_find)
        self.assertTrue(status.is_success(response.status_code))

        url_find = '/transfer_contract_priority-api/session_transfer_contract_priority_export_file/?contract_name=XXX_V,V_AV_AC_Di_Df_X&code_ccee=1234567890& \
                                                                                    buyer_profile=Matheus%20M.&vendor_profile=Juliana&transaction_type=tipo%20trans& \
                                                                                    priority_number=1&format_file=csv'
        response = self.client.get(url_find)
        self.assertTrue(status.is_success(response.status_code))

        url_find = '/transfer_contract_priority-api/session_transfer_contract_priority_export_file/?contract_name=XXX_V,V_AV_AC_Di_Df_X&code_ccee=1234567890& \
                                                                                    buyer_profile=Matheus%20M.&vendor_profile=Juliana&transaction_type=tipo%20trans& \
                                                                                    priority_number=15&ordering=priority_number&format_file=csv'
        response = self.client.get(url_find)
        self.assertTrue(status.is_success(response.status_code))

        #Error not Format_file
        url_find = '/transfer_contract_priority-api/session_transfer_contract_priority_export_file/'
        response = self.client.get(url_find)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        #error type format_file
        url_find = '/transfer_contract_priority-api/session_transfer_contract_priority_export_file/?format_file=error '
        response = self.client.get(url_find)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
