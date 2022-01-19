import os
import re
import math
import pandas as pd
import numpy as np
import datetime

from datetime import datetime, timedelta, time
from core.models import CceeDescription
from gauge_point.models import GaugePoint, Measurements, ImportSource
from manual_import.models import GaugeDataTemp
from consumption_metering_reports.models import SourcePme
from SmartEnergy.settings import BASE_DIR

from .ksb1 import ksb1_list
from .fbl3n import fbl3n_list

type_data = {1: 'texto', 2: 'inteiro', 3: 'decimal', 4: 'data', 5: 'hora'}


def verify_template(_df, _template, is_prod_dsh_ccee=False):

    file_path_template = os.path.join(BASE_DIR, 'uploads', 'templates', _template)

    _template_columns = []
    if os.path.isfile(file_path_template):
        df_template = pd.read_excel(file_path_template, 'Dados')
        _template_columns = list(df_template.columns.values)

    if is_prod_dsh_ccee:
        # Pega soh as 4 primeiras colunas
        _columns = list(_df.columns.values)[:4]
    else:
        # Pega todas as colunas
        _columns = list(_df.columns.values)

    # Valida se o arquivo tem as colunas do banco de dados mapeadas corretamente
    return set(_template_columns) == set(_columns)


def verify_date_type(_date):

    if verify_type('data', _date):
        return _date
    if isinstance(_date, str):
        # Verifica se o padrao de data esta correto
        match = re.search("^(0[1-9]|[12][0-9]|3[01])[/](0[1-9]|1[012])[/](19[0-9][0-9]|20[0-9][0-9])$", _date)
        if match:
            _date_obj = datetime.strptime(_date, '%d/%m/%Y')
            if verify_type('data', _date_obj):
                return _date_obj
        return None


def verify_hour_type(_hour):

    if isinstance(_hour, int):
        return _hour
    else:
        try:
            aux = int(_hour)
            if 0 <= aux <= 24:
                return aux
            return None
        except Exception as e:
            print(e.args)
            return None


def verify_decimal_type(_value):
    try:
        if isinstance(_value, float):
            return _value

        if isinstance(_value, int):
            return float(_value)

        if isinstance(_value, str):

            # 123.321
            match = re.search("^([0-9]+)[.]([0-9]+)$", _value)
            if match:
                return float(_value)

            # 123,321
            match = re.search("^([0-9]+)[,]([0-9]+)$", _value)
            if match:
                _aux = _value.replace(',', '.')
                _value_f = float(_aux)
                return _value_f

            # 2,123.321
            match = re.search("^([0-9]+)[,]([0-9]+)[.]([0-9]+)$", _value)
            if match:
                _aux = _value.replace(',', '')
                _value_f = float(_aux)
                return _value_f

            # 2.123,321
            match = re.search("^([0-9]+)[.]([0-9]+)[,]([0-9]+)$", _value)
            if match:
                _aux = _value.replace('.', '').replace(',', '.')
                _value_f = float(_aux)
                return _value_f

            _aux = float(int(_value))
            return _aux

        return None
    except Exception as e:
        print(e.args)
        return None


def get_source_ccee(df):

    # Pega a lista de medidores unicos
    meter_list = df[df.columns[0]].unique()

    source_dic = {}
    for meter in meter_list:

        # Adiciona cada medidor como uma chave do dicionario e seu ID como o valor desta chave
        if meter not in source_dic:

            if pd.isna(meter):
                # Arquivo faltando dados obrigatorios
                source_dic['vazio'] = {"error_type": "error_ima_required", "error_param": "Medidor"}
                continue

            # Nome do medidor com espacos, pega a primeira parte
            _meter = meter
            if ' ' in meter:
                _meter = meter.split(' ')[0]

            # Pega o valor da coluna MEDIDOR do template e pega um objeto CCEEDescription
            ccee_desc = CceeDescription.objects.filter(code_ccee=_meter).first()
            if not ccee_desc:
                # Existem medidores que ainda nao foram cadastrados
                source_dic[meter] = {"error_type": "error_ima_source", "error_param": _meter}
                continue

            # Se o medidor tem um ID entao associamos ele ao dicionario
            gauge_obj = GaugePoint.objects.filter(id_ccee=ccee_desc.id_ccee).first()
            if not gauge_obj:
                # Existem medidores que ainda nao possuem pontos de medicao
                source_dic[meter] = {"error_type": "error_ima_source_gauge", "error_param": _meter}
            else:
                source_dic[meter] = {"id_gauge": gauge_obj.id_gauge}

    return source_dic


def get_source_pme(df):

    source_dic = {}
    # Pega a lista de medidores unicos
    meter_list = df[df.columns[0]].unique()

    # Cria o dicionario de medidores com seus ids
    for meter in meter_list:

        # Adiciona cada medidor como uma chave do dicionario e seu ID como o valor desta chave
        if meter not in source_dic:

            if pd.isna(meter):
                # Arquivo faltando dados obrigatorios
                source_dic['vazio'] = {"error_type": "error_ima_required", "error_param": "TAG do ponto de medição"}
                continue

            _meter = meter.strip()
            if ' ' in meter:
                _meter = meter.split(' ')[0]

            source_pme = SourcePme.objects.filter(display_name=_meter).first()
            if not source_pme:
                # Existem medidores que ainda nao foram cadastrados
                source_dic[meter] = {"error_type": "error_ima_source", "error_param": _meter}
                continue

            gauge_obj = GaugePoint.objects.filter(id_source=source_pme.id_source).first()
            if not gauge_obj:
                # Existem medidores que ainda nao possuem pontos de medicao
                source_dic[meter] = {"error_type": "error_ima_source_gauge", "error_param": _meter}
            else:
                source_dic[meter] = {"id_gauge": gauge_obj.id_gauge}

    return source_dic


def get_quantity(df):

    quantity_dic = {}
    # Pega a lista de medidores unicos
    quantity_list = df[df.columns[1]].unique()

    # Cria o dicionario de quantitys com seus objetos
    for q in quantity_list:

        # Adiciona cada medidor como uma chave do dicionario e seu ID como o valor desta chave
        if pd.isna(q):
            # Arquivo faltando dados obrigatorios
            quantity_dic['vazio'] = {"error_type": "error_ima_required", "error_param": "Grandeza"}
            continue

        # Nome do medidor com espacos, pega a primeira parte
        _quantity = q
        if '(' in _quantity:
            _quantity = _quantity.split('(')[0].strip()

        measurements = Measurements.objects.filter(measurement_name=_quantity).first()
        if not measurements:
            # Existem medidores no arquivo que ainda nao foram cadastrados
            quantity_dic[q] = {"error_type": "error_ima_quantity", "error_param": _quantity}
        else:
            quantity_dic[q] = {"id_measurements": measurements.id_measurements}

    return quantity_dic


# Este método pode verificar os dados dos arquivos KSB1 e FBL34N
def verify_data_prod_dash(df, _utc, file_path, em):

    prod = True
    _template = 'template_PDCT.xlsx'

    if 'dashboard' in str(file_path).lower():
        prod = False
        _template = 'template_DSHB.xlsx'

    # Valida se o arquivo tem as colunas do banco de dados mapeadas corretamente
    if not verify_template(df, _template, True):
        # Nome das colunas do arquivo não corresponde as colunas do template.
        em.set_single_error("error_ima_template_wrong")
        return [], em

    _ima = ImportSource.objects.filter(import_type='Manual').first()
    if not _ima:
        # Verifica se na tabela ImportSource existe o tipo Manual (Importe Manual)
        em.set_single_error("error_ima_database_IMA")
        return [], em
    
    source_dic = get_source_pme(df)
    quantity_dic = get_quantity(df)

    line_count = 2
    list_data = []
    for line in df.values:

        # print(line[1])
        _error = False

        # TAG do ponto de medicao
        if pd.isna(line[0]):
            _source = {'error_type': 'error_ima_required', 'error_param': 'TAG do ponto de medição'}
        else:
            _source = source_dic[line[0]]

        # Grandeza
        if pd.isna(line[1]):
            _quantity = {'error_type': 'error_ima_required', 'error_param': 'Grandeza'}
        else:
            _quantity = quantity_dic[line[1]]

        _value = line[2]  # Valor
        _data = line[3]  # Data

        # Pula as linhas que não tem valores
        if pd.isna(_value):
            line_count = line_count + 1
            continue

        if "error_type" in _source:
            em.append_mult_error(line_count, _source["error_type"], _source["error_param"])
            _error = True

        if "error_type" in _quantity:
            em.append_mult_error(line_count, _quantity["error_type"], _quantity["error_param"])
            _error = True

        # Se _value eh do tipo string, entao transformamos o numero em decimal
        if isinstance(_value, str):
            _value = verify_decimal_type(_value)
        if not verify_type('decimal', _value):
            coluna = "Valor"  # Dashboards
            if prod:
                coluna = "Valor (kt)"  # Producao
            em.append_mult_error(line_count, "error_ima_column", coluna)
            _error = True

        # Arquivo faltando dados obrigatorios
        if pd.isna(_data):
            em.append_mult_error(line_count, "error_ima_required", "Data")
            _error = True
        else:
            _data = verify_date_type(_data)
            if not _data:
                em.append_mult_error(line_count, "error_ima_column", "Data")
                _error = True
            else:
                # Pega datetime da medicao
                _data = _data + timedelta(hours=3, minutes=15)

        if not _error:
            try:
                gauge_data = GaugeDataTemp()
                gauge_data.value = _value
                gauge_data.utc_gauge = _data
                gauge_data.utc_creation = _utc
                gauge_data.id_measurements = _quantity['id_measurements']
                gauge_data.id_import_source = _ima.id_import_source
                gauge_data.id_gauge = _source['id_gauge']
                list_data.append(gauge_data)
            except Exception as e:
                print(e.args)
                em.append_mult_error(line_count, "error_ima_column_obj", 'grande')

        line_count = line_count + 1
    return list_data, em


# Este método pode verificar os dados dos arquivos ccee, producao e dashboards
def verify_data_ccee(df, _utc, em, csv=False):

    # Soh verifica o template se o arquivo nao for do tipo csv
    if not csv:
        # Valida se o arquivo tem as colunas do banco de dados mapeadas corretamente
        if not verify_template(df, 'template_CCEE.xlsx'):
            # Nome das colunas no template esta fora do padrao permitido.
            em.set_single_error("error_ima_template_wrong")
            return [], em

    _measurement = Measurements.objects.filter(measurement_name="Active Energy CCEE").first()
    if not _measurement:
        em.set_single_error("error_ima_database_MEASURE")
        return [], em

    _ima = ImportSource.objects.filter(import_type='Manual').first()
    if not _ima:
        # Verifica se na tabela ImportSource existe o tipo Manual (Importe Manual)
        em.set_single_error("error_ima_database_IMA")
        return [], em

    source_dic = get_source_ccee(df)

    line_count = 2
    if csv:
        line_count = 5

    list_data = []
    for line in df.values:

        _error = False

        if pd.isna(line[0]):
            _source = {'error_type': 'error_ima_required', 'error_param': 'Medidor'}
        else:
            _source = source_dic[line[0]]  # Medidor

        _data = line[1]  # Data
        _hour = line[2]  # Hora
        _value = line[3]  # Energia Ativa CCEE

        # Pula as linhas que não tem valores
        if pd.isna(_value):
            line_count = line_count + 1
            continue

        if "error_type" in _source:
            em.append_mult_error(line_count, _source["error_type"], _source["error_param"])
            _error = True

        # Arquivo faltando dados obrigatorios
        if pd.isna(_data):
            em.append_mult_error(line_count, "error_ima_required", "Data")
            _error = True
        else:
            _data = verify_date_type(_data)
            if not _data:
                em.append_mult_error(line_count, "error_ima_column", "Data")
                _error = True
            else:
                # Arquivo faltando dados obrigatorios
                if pd.isna(_hour):
                    em.append_mult_error(line_count, "error_ima_required", "Hora")
                    _error = True
                else:
                    _hour = verify_hour_type(_hour)
                    if not _hour:
                        em.append_mult_error(line_count, "error_ima_column", "Hora")
                        _error = True
                    else:
                        # Pega datetime da medicao
                        _data = _data + timedelta(hours=_hour+3)

        # Se _value eh do tipo string, entao transformamos o numero em decimal
        if isinstance(_value, str):
            _value = verify_decimal_type(_value)
        if not verify_type('decimal', _value):
            column_name = "Energia Ativa CCEE (kWh)"
            if csv:
                column_name = "Ativa C (kWh)"
            em.append_mult_error(line_count, "error_ima_column", column_name)
            _error = True

        if not _error:
            try:
                gauge_data = GaugeDataTemp()
                gauge_data.value = _value
                gauge_data.utc_gauge = _data
                gauge_data.utc_creation = _utc
                gauge_data.id_measurements = _measurement.id_measurements
                gauge_data.id_import_source = _ima.id_import_source
                gauge_data.id_gauge = _source['id_gauge']
                list_data.append(gauge_data)

            except Exception as e:
                print(e.args)
                em.append_mult_error(line_count, "error_ima_column_obj", 'grande')

        line_count = line_count + 1

    return list_data, em


# Este método pode verificar os dados dos arquivos KSB1
def verify_data_ksb1(df, em):
    # Valida se o arquivo tem as colunas do banco de dados mapeadas corretamente
    if not verify_template(df, 'template_KSB1.xlsx'):
        # Nome das colunas do arquivo não corresponde as colunas do template.
        em.set_single_error("error_ima_template_wrong")
        return [], em

    # Pega a lista de valores do arquivo
    list_insert = []
    for linha in df.values:
        lista_dados = []
        for i in range(len(linha)):
            lista_dados.append(linha[i])
        list_insert.append(lista_dados)

    list_dic = []
    linha_count = 2
    for linha in list_insert:

        d = {}
        index = 0
        _error = False

        for _data in linha:
            _chave = ksb1_list[index]['column'].lower()
            d[_chave] = None

            if pd.isna(_data):
                d[_chave] = 'NULL'
            else:
                _type = type_data[ksb1_list[index]['type']]
                if _type == 'decimal':
                    if not verify_type('decimal', _data):
                        try:
                            value = str(_data).replace(',', '.')
                            _data = float(value)
                        except Exception as e:
                            print(e.args)
                            em.append_mult_error(linha_count, "error_ima_column", ksb1_list[index]['field'])
                            _error = True
                else:
                    if not verify_type(_type, _data):
                        em.append_mult_error(linha_count, "error_ima_column", ksb1_list[index]['field'])
                        _error = True

            if ksb1_list[index]['required'] and pd.isna(_data):
                em.append_mult_error(linha_count, "error_ima_required", ksb1_list[index]['field'])
                _error = True

            if d[_chave] is None:
                if ksb1_list[index]['type'] == 1:
                    d[_chave] = str(_data)
                elif ksb1_list[index]['type'] == 2:
                    d[_chave] = int(_data)
                else:
                    d[_chave] = _data
            index += 1

        if not _error:
            list_dic.append(d)
        linha_count = linha_count + 1

    return list_dic, em


# Este método pode verificar os dados dos arquivos FBL3N
def verify_data_fbl3n(df, em):
    # Valida se o arquivo tem as colunas do banco de dados mapeadas corretamente
    if not verify_template(df, 'template_FBL3N.xlsx'):
        # Nome das colunas do arquivo não corresponde as colunas do template.
        em.set_single_error("error_ima_template_wrong")
        return [], em

    # Pega a lista de valores do arquivo
    list_insert = []
    for linha in df.values:
        lista_dados = []
        for i in range(len(linha)):
            lista_dados.append(linha[i])
        list_insert.append(lista_dados)

    list_dic = []
    linha_count = 2
    for linha in list_insert:

        d = {}
        index = 0
        _error = False
        for _data in linha:
            _chave = fbl3n_list[index]['column'].lower()
            d[_chave] = None

            if pd.isna(_data):
                d[_chave] = 'NULL'
            else:
                _type = type_data[fbl3n_list[index]['type']]
                if _type == 'decimal':
                    if not verify_type('decimal', _data):
                        try:
                            value = str(_data).replace(',', '.')
                            _data = float(value)
                        except Exception as e:
                            print(e.args)
                            em.append_mult_error(linha_count, "error_ima_column", fbl3n_list[index]['field'])
                            _error = True
                else:
                    if not verify_type(_type, _data):
                        em.append_mult_error(linha_count, "error_ima_column", fbl3n_list[index]['field'])
                        _error = True

            if fbl3n_list[index]['required'] and pd.isna(_data):
                em.append_mult_error(linha_count, "error_ima_required", fbl3n_list[index]['field'])
                _error = True

            if d[_chave] is None:
                if fbl3n_list[index]['type'] == 1:
                    d[_chave] = str(_data)
                elif fbl3n_list[index]['type'] == 2:
                    try:
                        d[_chave] = int(_data)
                    except Exception as e:
                        print(e.args)
                        em.append_mult_error(linha_count, "error_ima_column", fbl3n_list[index]['field'])
                        _error = True
                else:
                    d[_chave] = _data
            index += 1

        if not _error:
            list_dic.append(d)
        linha_count = linha_count + 1

    return list_dic, em


def verify_file_name(file_path):

    _name = os.path.basename(file_path)
    # Verifica se o padrao de nomes esta correto
    match = re.search("^(fbl3n|ksb1|ccee|producao|dashboards)[_].*?(.xls|.xlsx|.csv)$", _name.lower())
    if match:
        if 'fbl3n_' in _name.lower():
            return 'fbl3n/'
        if 'ksb1_' in _name.lower():
            return 'ksb1/'
        if 'ccee_' in _name.lower():
            return 'ccee/'
        if 'producao_' in _name.lower():
            return 'producao/'
        if 'dashboards_' in _name.lower():
            return 'dashboards/'
    else:
        return None


def verify_type_file(file_path, file_type):
    _name = os.path.basename(file_path)
    match = re.search("^(fbl3n|ksb1|ccee|producao|dashboards)[_].*?(.xls|.xlsx|.csv)$", _name.lower())
    if match:
        if 'ksb1' in str(file_type).lower() in _name.lower():
            return True
        if 'fbl3' in str(file_type).lower() in _name.lower():
            return True
        if 'ccee' in str(file_type).lower() in _name.lower():
            return True
        if 'producao' in str(file_type).lower() in _name.lower():
            return True
        if 'dashboard' in str(file_type).lower() in _name.lower():
            return True
    return False


def verify_type(_type, _value):
    if _type == 'texto':
        return isinstance(str(_value), str)
    if _type == 'data':
        return isinstance(_value, datetime)
    if _type == 'hora':
        return isinstance(_value, time)
    if _type == 'inteiro':
        if isinstance(_value, float):
            frac, whole = math.modf(_value)
            return frac == 0
        else:
            # np.integer verifica qualquer tipo de valor inteiro
            return np.issubdtype(type(_value), np.integer)
    if _type == 'decimal':
        return isinstance(_value, float) or isinstance(_value, int)
    return False
