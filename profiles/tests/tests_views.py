from rest_framework import status
from rest_framework.test import APITestCase
from profiles.models import Profile


# Create your tests here.

class ProfilesTest(APITestCase):
    # loads fixtures dependencies
    fixtures = [
        # 'core/fixtures/initial_data.json', 'company/fixtures/initial_data.json',
        # 'agents/fixtures/initial_data.json', 'profiles/fixtures/initial_data.json',
        # 'organization/fixtures/initial_data_dxc.json', 'gauge_point/fixtures/initial_data_dxc.json',
        # 'energy_composition/fixtures/initial_data_dxc.json', 'assets/fixtures/initial_data_dxc.json',
    ]

    def test_find_profiles(self):
        # teste find
        url_find = '/profile-api/session_profile/?name_profile=Alianca Comerc'

        response = self.client.get(url_find, format='json')
        self.assertTrue(status.is_success(response.status_code))

    def test_get_profiles(self):
        # test get
        url = url = '/profile-api/session_profile/'

        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

    def test_post_profile(self):
        # test create
        url = '/profile-api/session_profile_post/'
        expected = {
            "code_ccee": "1597346",
            "type": "A/P",
            "name_ccee": "CoverageTest",
            "status": "S",
            "profile_ccee": {
                "id_agents": 10046,
                "encouraged_energy": False,
                "name_profile": "TesteCoverage",
                "alpha": "N",
                "status": "S"
            }
        }
        response = self.client.post(url, expected, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_error = {
            "profile_ccee": {
                "alpha": "N"
            }
        }
        response = self.client.post(url, expected_error, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        expected_error = {
            "code_ccee": "1234567881",
            "type": "sla",
            "name_ccee": "Guilia",
            "status": "S",
            "profile_ccee": {
                "id_agents": 2.0,
                "name_profile": "Matheus M.",
                "alpha": "N",
                "status": "S"
            }
        }
        response = self.client.post(url, expected_error, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_profile(self):
        # exists
        profile = Profile.objects.last()

        urlGet = '/profile-api/session_profile/%s/' % profile.pk
        urlPut = '/profile-api/session_profile_put/%s/' % profile.pk

        response = self.client.get(urlGet)
        self.assertTrue(status.is_success(response.status_code))

        # put
        response = self.client.put(urlPut, response.data, format='json')
        self.assertTrue(status.is_success(response.status_code))

        response = self.client.get(urlGet)
        response.data['profile_ccee']['alpha'] = "S"
        response = self.client.put(urlPut, response.data, format='json')
        self.assertTrue(status.is_success(response.status_code))

        response = self.client.get(urlGet)
        response.data['profile_ccee']['alpha'] = "N"
        response.data['profile_ccee']['id_ccee'] = None
        response.data['id_ccee'] = None
        response.data['code_ccee'] = "33215"
        response.data['type'] = "A/P"
        response.data['name_ccee'] = "tesate"
        response = self.client.put(urlPut, response.data, format='json')
        self.assertTrue(status.is_success(response.status_code))

    def test_get_profile_detail(self):
        # test detail
        profile = Profile.objects.all().first()

        url = '/profile-api/session_profile/%s/' % profile.pk
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

    def test_file_csv(self):
        url_find = '/profile-api/session_profile_file/?format_file=csv'
        response = self.client.get(url_find)
        self.assertTrue(status.is_success(response.status_code))

        # error
        url_find = '/profile-api/session_profile_file/?name_profile=Matheus&format_file=error'
        response = self.client.get(url_find)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # error
        url_find = '/profile-api/session_profile_file/?name_profile=Coverage'
        response = self.client.get(url_find)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_log_profile(self):
        url = '/profile-api/session_log_basic_profile/%s/' % 73
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))


if __name__ == '__main__':
    unittest.main()
