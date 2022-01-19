from ..repositories.global_variables_repository import (get_states_repository, get_icmss_repository,
                                                        insert_global_variable_repository, set_variable_unity_value,
                                                        is_index_repository, update_marketing_flag_value,
                                                        get_taxes_tariffs_repository,
                                                        insert_taxes_tariffs_repository,
                                                        update_taxes_tariffs_repository, get_indexes_repository,
                                                        update_index_repository,
                                                        find_index_by_variable_month_year_repository,
                                                        insert_log_repository, get_icms_logs_repository,
                                                        get_taxes_tariffs_logs_repository,
                                                        get_indexes_logs_repository,
                                                        set_value_variable_name_unity_type,
                                                        get_tax_taxes_tariffs_by_id_repository,
                                                        find_index_by_id, update_by_id_state_value,
                                                        has_variables_been_changed,
                                                        check_state_exists,
                                                        check_marketing_exists)
from rest_framework.exceptions import ValidationError
from rest_framework.status import (HTTP_201_CREATED, HTTP_400_BAD_REQUEST,
                                   HTTP_409_CONFLICT, HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_500_INTERNAL_SERVER_ERROR)
from ..components.global_variables_componet import formatted_tax_tariff_insert, formatted_tax_tariff_update, formatted_index_insert, formatted_index_update
from ..repositories.global_variables_repository import format_icms_log, get_user_username


def insert_log_service(field_pk, table_name, action_type, new_value, old_value, user, observation):
    insert_log_repository(field_pk, table_name, action_type, new_value, old_value, user, observation)


def get_states_service():
    return get_states_repository(), HTTP_200_OK


def get_icms_logs_service():
    return get_icms_logs_repository(), HTTP_200_OK


def get_taxes_tariffs_logs_service():
    return get_taxes_tariffs_logs_repository(), HTTP_200_OK


def get_indexes_logs_service():
    return get_indexes_logs_repository(), HTTP_200_OK


def get_icmss_service():
    return get_icmss_repository(), HTTP_200_OK


def create_icms_service(global_variable, request):
    user = get_user_username(request)
    try:
        if not check_marketing_exists() and global_variable.get('marketing') == 1 and global_variable.get('state') is None:
            variable, unity, status = global_variable.get('variable'), global_variable.get('unity'), global_variable.get('status')
            old_value=format_icms_log(variable, unity, status)
            new_id = insert_global_variable_repository(set_variable_unity_value(global_variable))
            new_value=format_icms_log(variable, unity, status)
            insert_log_service(field_pk=new_id, table_name='GLOBAL_VARIABLE', action_type='INSERT', new_value=new_value, old_value=old_value, user=user, observation='ICMS Global Variable')
        elif check_marketing_exists() and global_variable.get('marketing') == 1:
            return {'message': 'error_duplicate_ICMS_marketing'}, HTTP_409_CONFLICT
        elif not check_state_exists(global_variable) and global_variable.get('marketing') == 0 and global_variable.get('id') is None:
            variable, unity, status = global_variable.get('variable'), global_variable.get('unity'), global_variable.get('status')
            old_value=format_icms_log(variable, unity, status)
            new_id = insert_global_variable_repository(set_variable_unity_value(global_variable))
            new_value=format_icms_log(variable, unity, status)
            insert_log_service(field_pk=new_id, table_name='GLOBAL_VARIABLE', action_type='INSERT', new_value=new_value, old_value=old_value, user=user, observation='ICMS Global Variable')
        else:
            return {'message': 'error_insert_state_and_commercial'}, HTTP_409_CONFLICT
    except ValidationError as error:
        if 'must be unique' in str(error):
            return {'message': 'error_duplicate_ICMS_state'}, HTTP_409_CONFLICT
        else:
            print(error)
            return {'message': 'error_unexpected_problem'}, HTTP_500_INTERNAL_SERVER_ERROR
    except KeyError as error:
        print(error)
        return {'message': 'error_unexpected_problem'}, HTTP_500_INTERNAL_SERVER_ERROR
    return None, HTTP_201_CREATED


def update_icms_service(global_variable, request):
    user = get_user_username(request)
    try:
        if global_variable.get('marketing') == 1 and global_variable.get('state') is None:
            variable, unity, status = global_variable.get('variable'), global_variable.get('unity'), global_variable.get('status')
            old_value=format_icms_log(variable, unity, status)
            update_marketing_flag_value(set_variable_unity_value(global_variable))
            new_value=format_icms_log(variable, unity, status)
            insert_log_service(field_pk=global_variable.get('id'), table_name='GLOBAL_VARIABLE', action_type='UPDATE', new_value=new_value, old_value=old_value, user=user, observation='ICMS Global Variable')
        elif global_variable.get('state') is not None and global_variable.get('marketing') == 0:
            variable, unity, status = global_variable.get('variable'), global_variable.get('unity'), global_variable.get('status')
            old_value=format_icms_log(variable, unity, status)
            update_by_id_state_value(set_variable_unity_value(global_variable))
            new_value=format_icms_log(variable, unity, status)
            insert_log_service(field_pk=global_variable.get('id'), table_name='GLOBAL_VARIABLE', action_type='UPDATE', new_value=new_value, old_value=old_value, user=user, observation='ICMS Global Variable')
        else:
            return {'message': 'error_insert_state_and_commercial'}, HTTP_400_BAD_REQUEST
    except ValidationError as error:
        print(error)
        return {'message': 'error_unexpected_problem'}, HTTP_500_INTERNAL_SERVER_ERROR

    return None, HTTP_200_OK
        

def delete_icms_service(global_variable, request):
    """Method that checks whether an ICMS variable is eligible for removal and changes the status to removed"""
    user = get_user_username(request)
    try:
        if check_marketing_exists() and global_variable.get('marketing') == 1 and global_variable.get('state') is None and global_variable.get('status') == 1:
            variable, unity, status = global_variable.get('variable_name'), global_variable.get('unity_type'), global_variable.get('status')
            old_value=format_icms_log(variable, unity, status)
            global_variable['status'] = False
            global_variable['value'] = None
            update_marketing_flag_value(set_value_variable_name_unity_type(global_variable))
            new_value=format_icms_log(variable, unity, status)
            insert_log_service(field_pk=global_variable.get('id'), table_name='GLOBAL_VARIABLE', action_type='DELETE', new_value=new_value, old_value=old_value, user=user, observation='ICMS Global Variable')
        elif global_variable.get('state') is not None and global_variable.get('marketing') == 0:
            variable, unity, status = global_variable.get('variable_name'), global_variable.get('unity_type'), global_variable.get('status')
            old_value=format_icms_log(variable, unity, status)
            global_variable['status'] = False
            global_variable['value'] = None
            update_by_id_state_value(set_variable_unity_value(global_variable))
            new_value=format_icms_log(variable, unity, status)
            insert_log_service(field_pk=global_variable.get('id'), table_name='GLOBAL_VARIABLE', action_type='DELETE', new_value=new_value, old_value=old_value, user=user, observation='ICMS Global Variable')
        else:
            return {'message': 'error_simultaneously_delete_state_and_commercial'}, HTTP_400_BAD_REQUEST
    except ValidationError as error:
        print(error)
        return {'message': 'error_unexpected_problem'}, HTTP_500_INTERNAL_SERVER_ERROR
    return None, HTTP_204_NO_CONTENT


def get_taxes_tariffs_service():
    """Method that returns the values of fees and tariffs"""
    return get_taxes_tariffs_repository(), HTTP_200_OK


def create_update_taxes_tariffs_service(global_variables, request):
    """Method that creates or updates fees and tariffs"""
    user = get_user_username(request)

    if has_variables_been_changed(global_variables):
        for global_variable in global_variables:
            if global_variable.get('id') is not None:
                variable, unity = global_variable.get('variable'), global_variable.get('unity')
                set_variable_unity_value(global_variable)
                old_global_variable = get_tax_taxes_tariffs_by_id_repository(global_variable.get('id'))
                update_taxes_tariffs_repository(global_variable)
                global_variable, old_global_variable = formatted_tax_tariff_update(global_variable, old_global_variable, variable, unity)
                insert_log_service(field_pk=global_variable.get('id'), table_name='GLOBAL_VARIABLE', action_type='UPDATE', new_value=global_variable, old_value=old_global_variable, user=user, observation='Taxe and Tariff Global Variable')
            else:
                #Insert Taxes and Tariffs
                variable, unity = global_variable.get('variable'), global_variable.get('unity')
                response = insert_taxes_tariffs_repository(set_variable_unity_value(global_variable))
                if 'must be unique' in str(response):
                    return {'message': 'error_duplicate_taxes_tariffs'}, HTTP_409_CONFLICT
                else:
                    global_variable = formatted_tax_tariff_insert(global_variable, response, variable, unity)
                    insert_log_service(field_pk=response, table_name='GLOBAL_VARIABLE', action_type='INSERT', new_value=global_variable, old_value=None, user=user, observation='Taxe and Tariff Global Variable')
    else:
        return {'message': 'error_dont_altered_values'}, HTTP_409_CONFLICT
    return None, HTTP_201_CREATED


def get_indexes_service():
    return get_indexes_repository(), HTTP_200_OK


def create_index_service(global_variable, request):
    user = get_user_username(request)
    try:
        if not is_index_repository(global_variable):
            variable, unity = global_variable.get('variable'), global_variable.get('unity')
            new_id = insert_global_variable_repository(set_variable_unity_value(global_variable))
            global_variable = formatted_index_insert(global_variable, new_id, variable, unity)
            insert_log_service(field_pk=new_id, table_name='GLOBAL_VARIABLE', action_type='INSERT', new_value=global_variable, old_value=None, user=user, observation='Index Global Variable')
        else:
            return {'message': 'error_duplicate_index'}, HTTP_409_CONFLICT
    except ValidationError as error:
        print(error)
        return {'message': 'error_unexpected_problem'}, HTTP_500_INTERNAL_SERVER_ERROR
    return None, HTTP_201_CREATED


def update_index_service(global_variable, request):
    user = get_user_username(request)
    try:
        data = find_index_by_variable_month_year_repository(global_variable)
        if data:
            for index in data:
                if index.get('id') == global_variable.get('id'):
                    variable, unity = global_variable.get('variable'), global_variable.get('unity')
                    update_index_repository(set_variable_unity_value(global_variable))  
                    global_variable, old_global_variable = formatted_index_update(global_variable, index, variable, unity)
                    insert_log_service(field_pk=global_variable.get('id'), table_name='GLOBAL_VARIABLE', action_type='UPDATE', new_value=global_variable, old_value=old_global_variable, user=user, observation='Index Global Variable')
                else:
                    return {'message': 'error_duplicate_index'}, HTTP_409_CONFLICT
        else:
            variable, unity = global_variable.get('variable'), global_variable.get('unity')
            old_global_variable = find_index_by_id(global_variable)
            update_index_repository(set_variable_unity_value(global_variable)) 
            global_variable, old_global_variable = formatted_index_update(global_variable, old_global_variable, variable, unity)
            insert_log_service(field_pk=global_variable.get('id'), table_name='GLOBAL_VARIABLE', action_type='UPDATE', new_value=global_variable, old_value=old_global_variable, user=user, observation='Index Global Variable')
    except Exception as error:
        print(error)
        return {'message': 'error_unexpected_problem'}, HTTP_500_INTERNAL_SERVER_ERROR
    return None, HTTP_204_NO_CONTENT