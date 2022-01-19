
def formatted_index_insert(global_variable, new_id, variable, unity):
    del global_variable['variable']
    del global_variable['unity']
    global_variable['variable'] = variable
    global_variable['unity'] = unity
    global_variable['id'] = int(new_id)
    global_variable['status'] = True

    return global_variable


def formatted_index_update(global_variable, old_global_variable, variable, unity):
    del global_variable['variable']
    del global_variable['unity']
    del global_variable['state']
    global_variable['variable'] = variable
    global_variable['unity'] = unity
    global_variable['status'] = True
    if old_global_variable.get('state') is not None:
        old_global_variable['state'] = int(old_global_variable.get('state'))
    old_global_variable['value'] = float(old_global_variable.get('value'))
    del old_global_variable['variable']
    old_global_variable['variable'] = old_global_variable.get('variable_name')
    old_global_variable['unity'] = old_global_variable.get('unity_type')
    del old_global_variable['state']
    del old_global_variable['variable_name']
    del old_global_variable['unity_type']
    del old_global_variable['state_name']
    del old_global_variable['marketing']
    del old_global_variable['formated_value']
    old_global_variable['status'] = True

    return global_variable, dict(old_global_variable)


def formatted_tax_tariff_insert(global_variable, new_id, variable, unity):
    del global_variable['variable']
    del global_variable['unity']
    global_variable['variable'] = variable
    global_variable['unity'] = unity
    global_variable['id'] = int(new_id)
    global_variable['status'] = True

    return global_variable


def formatted_tax_tariff_update(global_variable, old_global_variable, variable, unity):
    del global_variable['variable']
    del global_variable['unity']
    global_variable['variable'] = variable
    global_variable['unity'] = unity
    global_variable['status'] = True
    if old_global_variable.get('state') is not None:
        old_global_variable['state'] = int(old_global_variable.get('state'))
    old_global_variable['value'] = float(old_global_variable.get('value'))
    del old_global_variable['state']
    del old_global_variable['marketing']

    return global_variable, old_global_variable
