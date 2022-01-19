from django.test import TestCase
from datetime import datetime
from dateutil.parser import isoparse
from random import randrange
import json
from .models import State, Country, Log, GlobalVariable, Variable, VariableType, Unity, LogEntity
from .serializers import StateSerializer, LogSerializer
from .services.global_variables_service import insert_log_service, get_states_service, get_icms_logs_service, \
    get_icmss_service, get_indexes_logs_service, get_taxes_tariffs_logs_service, create_icms_service, \
    get_taxes_tariffs_service, update_icms_service, delete_icms_service, get_indexes_service, \
    create_update_taxes_tariffs_service, create_index_service, update_index_service
from .repositories.global_variables_repository import get_variable_by_id, get_unity_by_id, set_value_variable_name_unity_type
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_409_CONFLICT, HTTP_204_NO_CONTENT
from .views import *


class GlobalVariableModelTest(TestCase):
    """
        First Step: run db-init.sql, changing name SmartEnergy to SmartEnergyTest
        After this: python ./manage.py test --keepdb .\global_variables\ 
    """
    icms_mock = {}
    marketing_mock = {}
    mock_request = {}
    request = lambda: None
    setattr(request, 'auth', mock_request)
    taxes_tariffs = []
    index_month_year = {}

    def setUp(self):
        self.icms_mock = {
            'marketing': False,
            'status': True,
            'variable': 'ICMS',
            'unity': 'PERCENTUAL',
            'id': None,
            'value': '12.0000',
            'state': 8
        }
        self.marketing_mock = {
            'marketing': True,
            'status': True,
            'variable': 'ICMS',
            'unity': 'PERCENTUAL',
            'id': None,
            'value': '11.0000',
            'state': None
        }
        self.mock_request = {
            'cn': 'C00000000',
            'UserFullName': 'UserTest'
        }
        self.taxes_tariffs = [
            {
                'id': None,
                'variable': 'COFINS',
                'value': '8.0000',
                'unity': 'PERCENTUAL'
            },
            {
                'id': None,
                'variable': 'COTAÇÃO DO DÓLAR',
                'value': '6.0000',
                'unity': 'MONETÁRIO'
            },
            {
                'id': None,
                'variable': 'PIS',
                'value': '9',
                'unity': 'PERCENTUAL'
            },
            {
                'id': None,
                'variable': 'TARIFA FIXA DE RATEIO',
                'value': '12.0000',
                'unity': 'MONETÁRIO'
            }
        ]
        self.index_month_year = {
            'variable': 'IPCA2',
            'unity': 'PERCENTUAL',
            'value': '11.0000',
            'month': '01',
            'year': 2015,
            'state': None
        }

    def test_state_model(self):
        country = Country.objects.create(name='Brasil', initials='BRA')
        state = State.objects.create(country=country, name='Acre', initials='AC')

        state_created = StateSerializer(state).data
        state_saved = StateSerializer(State.objects.filter(name=state.name).latest('id')).data
        state_saved['country'] = int(state_saved['country'])

        # check records
        self.assertEquals(state_created, state_saved)
        self.assertIsInstance(state_created, type(state_saved))

        # remove all
        state.delete()
        country.delete()

    def test_model_log(self):
        mock_values = {
            'field_pk': 1,
            'table_name': None,
            'action_type': None,
            'old_value': 'test_old_value',
            'new_value': 'test_new_value',
            'observation': 'test_observation',
            'date': datetime(2020,12,12,12,0,0,0).date(),
            'user': 'test_user'
        }

        log = Log.objects.create(**mock_values)
        log.save()

        test_log = Log.objects.get(user=mock_values['user'])
        log_serialized = LogSerializer(test_log).data

        del log_serialized['id']
        log_serialized['field_pk'] = int(log_serialized['field_pk'])
        log_serialized['date'] =  mock_values['date']
        
        self.assertEquals(mock_values, log_serialized)
        self.assertIsInstance(log_serialized, type(mock_values))

    def test_variable_global(self):
        today = datetime.today()
        country = Country.objects.create(name='Brasil', initials='BRA')
        state = State.objects.create(country=country, name='Acre', initials='AC')
        variable_type = VariableType.objects.create(name='Test')
        variable = Variable.objects.create(type=variable_type, name='tesstee')
        unity = Unity.objects.create(name='test_unit', description='test_description')
        variable_global = GlobalVariable.objects.create(
            variable=variable,  # receive FK
            unity=unity,  # receive FK
            state=state,  # receive FK
            value=randrange(1, 1800000),
            month=today.month,
            year=today.year,
            marketing=True,
            status=True)

        # read
        get_last_insert = GlobalVariable.objects.get(id=variable_global.id)

        binary_to_bool = lambda value: int(value) == 1 if True else False

        # compare last insert with model.
        self.assertEquals(get_last_insert.id, variable_global.id)
        self.assertEquals(get_last_insert.variable, variable_global.variable)
        self.assertEquals(get_last_insert.unity, variable_global.unity)
        self.assertEquals(get_last_insert.state, variable_global.state)
        self.assertEquals(get_last_insert.value, variable_global.value)
        self.assertEquals(get_last_insert.month, variable_global.month)
        self.assertEquals(get_last_insert.year, variable_global.year)
        self.assertEquals(binary_to_bool(get_last_insert.marketing), binary_to_bool(variable_global.marketing))
        self.assertEquals(binary_to_bool(get_last_insert.status), binary_to_bool(variable_global.status))

        # update.
        new_value = 666
        get_last_insert.value = new_value
        get_last_insert.marketing = False
        get_last_insert.status = False
        get_last_insert.save()

        get_item_updated = GlobalVariable.objects.get(id=get_last_insert.id)

        self.assertEquals(get_item_updated.value, new_value)
        self.assertEquals(binary_to_bool(get_item_updated.marketing), False)
        self.assertEquals(binary_to_bool(get_item_updated.status), False)

        # delete.
        get_item_updated.delete()

        check_if_deleted = GlobalVariable.objects.filter(id=get_last_insert.id).exists()
        self.assertEquals(check_if_deleted, False)

        # remove all
        variable_global.delete()
        unity.delete()
        variable.delete()
        variable_type.delete()
        state.delete()
        country.delete()

    def test_insert_log_service(self):
        insert_log_service(1, 'TABLE_TEST', 'action_type', 'new_value', 'old_value', 'user', 'observation')
        log = Log.objects.latest('id')
        self.assertEquals(1, log.field_pk)
        log.delete()

    def test_get_states_service(self):
        response, status = get_states_service()
        self.assertEquals(status, HTTP_200_OK)

    def test_get_icms_logs_service(self):
        response, status = get_icms_logs_service()
        self.assertEquals(status, HTTP_200_OK)

    def test_get_taxes_tariffs_logs_service(self):
        response, status = get_taxes_tariffs_logs_service()
        self.assertEquals(status, HTTP_200_OK)

    def test_get_indexes_logs_service(self):
        response, status = get_indexes_logs_service()
        self.assertEquals(status, HTTP_200_OK)

    def test_get_icmss_service(self):
        response, status = get_icmss_service()
        self.assertEquals(status, HTTP_200_OK)

    def test_get_indexes_service(self):
        response, status = get_indexes_service()
        self.assertEquals(status, HTTP_200_OK)

    def test_create_icms_service(self):
        response, status = create_icms_service(self.icms_mock, self.request)
        self.assertEquals(status, HTTP_201_CREATED)
        response, status = create_icms_service(self.icms_mock, self.request)
        self.assertEquals(status, HTTP_409_CONFLICT)

        response, status = create_icms_service(self.marketing_mock, self.request)
        self.assertEquals(status, HTTP_201_CREATED)
        response, status = create_icms_service(self.marketing_mock, self.request)
        self.assertEquals(status, HTTP_409_CONFLICT)


        response, status = update_icms_service(self.icms_mock, self.request)
        self.assertEquals(status, HTTP_200_OK)

        response, status = update_icms_service(self.marketing_mock, self.request)
        self.assertEquals(status, HTTP_200_OK)


        response, status = delete_icms_service(self.icms_mock, self.request)
        self.assertEquals(status, HTTP_204_NO_CONTENT)

        response, status = delete_icms_service(self.marketing_mock, self.request)
        self.assertEquals(status, HTTP_204_NO_CONTENT)

    def test_get_taxes_tariffs_service(self):
        response, status = get_taxes_tariffs_service()
        self.assertEquals(status, HTTP_200_OK)

    def test_create_update_taxes_tariffs_service(self):
        taxes_tariffs = GlobalVariable.objects.filter(
            status=True,
            variable_id__name__in=['COFINS', 'COTAÇÃO DO DÓLAR', 'PIS', 'TARIFA FIXA DE RATEIO']
        )
        for item in taxes_tariffs:
            item.status = False
            item.save()

        response, status = create_update_taxes_tariffs_service(self.taxes_tariffs, self.request)
        self.assertEquals(status, HTTP_201_CREATED)

        taxes_tariffs = GlobalVariable.objects.filter(
            status=True,
            variable_id__name__in=['COFINS', 'COTAÇÃO DO DÓLAR', 'PIS', 'TARIFA FIXA DE RATEIO']
        ).order_by('variable_id__name')

        for model_item, mock_item in zip(taxes_tariffs, self.taxes_tariffs):
            mock_item['id'] = model_item.id
            mock_item['value'] = 1

        response, status = create_update_taxes_tariffs_service(self.taxes_tariffs, self.request)
        self.assertEquals(status, HTTP_201_CREATED)

        response, status = create_update_taxes_tariffs_service(self.taxes_tariffs, self.request)
        self.assertEquals(status, HTTP_409_CONFLICT)

    def test_create_index_service(self):
        response, status = create_index_service(self.index_month_year, self.request)
        self.assertEquals(status, HTTP_201_CREATED)

        response, status = create_index_service(self.index_month_year, self.request)
        self.assertEquals(status, HTTP_409_CONFLICT)

    def test_update_index_service(self):
        index_variable = GlobalVariable.objects.filter(
            status=True,
            variable_id__name__in=['IGP-M', 'IPCA']).latest('id')
        self.index_month_year = index_variable.__dict__
        self.index_month_year['state'] = None
        self.index_month_year['variable'] = index_variable.variable.name
        self.index_month_year['unity'] = index_variable.unity_id
        month = self.index_month_year['month']
        year = self.index_month_year['year']
        response, status = update_index_service(self.index_month_year, self.request)
        self.assertEquals(status, HTTP_204_NO_CONTENT)

        self.index_month_year['id'] = index_variable.id
        self.index_month_year['state'] = None
        response, status = update_index_service(self.index_month_year, self.request)
        self.assertEquals(status, HTTP_204_NO_CONTENT)

        self.index_month_year['month'] = 0
        self.index_month_year['year'] = 0
        response, status = update_index_service(self.index_month_year, self.request)
        self.assertEquals(status, 500)

        self.index_month_year['id'] = 0
        self.index_month_year['month'] = month
        self.index_month_year['year'] = year
        response, status = update_index_service(self.index_month_year, self.request)
        self.assertEquals(status, 500)

    def test_icms_aliquot(self):
        url = '/global-variables-api/icms-aliquot/'

        response_post = self.client.post(url, data=json.dumps(self.icms_mock), content_type='application/json')
        self.assertTrue(status.is_success(response_post.status_code))

        response_get = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response_get.status_code))

        mock_icms_put = self.icms_mock
        mock_icms_put['value'] = 6
        response_put = self.client.put(url, data=json.dumps(mock_icms_put), content_type='application/json')
        self.assertTrue(status.is_success(response_put.status_code))

        response_delete = self.client.delete(url, data=json.dumps(mock_icms_put), content_type='application/json')
        self.assertTrue(status.is_success(response_put.status_code))
    
    def test_icms_logs(self):
        url = '/global-variables-api/indexes/logs'
        response = self.client.get(url, format='json')
        self.assertTrue(status.is_success(response.status_code))

    def test_get_states(self):
        url = '/global-variables-api/states/'

        response = self.client.get(url, content_type='application/json')
        self.assertTrue(status.is_success(response.status_code))
    
    def test_indexes(self):
        url = '/global-variables-api/indexes/'

        response_post = self.client.post(url, data=json.dumps(self.index_month_year), content_type='application/json')
        print(response_post.status_code)
        self.assertTrue(status.is_success(response_post.status_code))

        response_get = self.client.get(url, content_type='application/json')
        self.assertTrue(status.is_success(response_get.status_code))

        new_id = int(response_get.data[-1]['id'])
        index_mock = self.index_month_year
        index_mock['id'] = new_id
        response_put = self.client.put(url, data=json.dumps(index_mock), content_type='application/json')
        self.assertTrue(status.is_success(response_put.status_code))

    def test_get_variable_by_id(self):
        variable = get_variable_by_id(1)
        self.assertEquals(variable, 'IGP-M')

    def test_get_unity_by_id(self):
        unity = get_unity_by_id(1)
        self.assertEquals(unity, 'MONETÁRIO')

    def test_set_value_variable_name_unity_type(self):
        mock = {}
        mock['value'] = 1
        mock['variable'] = 'variable_test'
        mock['unity'] = 'unity_test'
        response = set_value_variable_name_unity_type(mock)
        self.assertEquals(response['value'], mock['value'])
        self.assertEquals(response['variable'], mock['variable'])
        self.assertEquals(response['unity'], mock['unity'])

    def test_log_entity(self):
        log_entity = LogEntity(
            field_pk=1,
            table_name='teste',
            action_type='test',
            new_value='111',
            old_value='000',
            observation='just a test',
            date=datetime.now(),
            user='Test'
        )
        self.assertEquals(log_entity.field_pk, 1)


