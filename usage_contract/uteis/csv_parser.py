from pandas import DataFrame
from datetime import datetime
from fpdf import FPDF, HTMLMixin
from bs4 import BeautifulSoup as Be
from locales.translates_function import translate_label, get_language
from base64 import b64encode
import pdfkit

from django.conf import settings


class HTML2PDF(FPDF, HTMLMixin):
    pass

# static values for generation
def get_not_relevant_data():
    return ['id_usage_contract', 'rate_post_exception', 'energy_distributor', 'energy_transmitter', 'upload_file', 'observation']

def get_labels_width():
    return {
        "": "2%",
        "field_ctu_min_usage_contract_type": "5%",
        "field_ctu_company": "5%",
        "field_ctu_energy_dealer": "12%",
        "field_ctu_min_contract_number": "6%",
        "field_ctu_rated_voltage": "6%",
        "field_ctu_group": "3%",
        "field_ctu_subgroup": "4%",
        "field_ctu_min_bought_voltage": "5%",
        "field_ctu_min_tolerance_range": "6%",
        "field_ctu_min_power_factor": "5%",
        "field_ctu_min_peak_begin_time": "5%",
        "field_ctu_min_peak_end_time": "5%",
        "field_ctu_contract_value": "6%",
        "field_ctu_start_date": "4%",
        "field_ctu_end_date": "4%",
        "field_ctu_create_date": "5%",
        "field_ctu_status": "3%",
        "field_ctu_connection_point": "6%",
    }

def get_header(request):
    label_widths = get_labels_width()
    labels = label_widths.keys()
    
    header = '<tr>'
    for label in labels:
        header += f'<th width="{label_widths[label]}">{translate_label(label, request) if label != "" else " "}</th>'
    header += '</tr>'
    
    return header

def get_body(tbody, noValue):
    widths = list(get_labels_width().values())
    finished_tbody = ''

    new_tbody = str(tbody).replace(
        '<td></td>', f'<td> ({noValue}) </td>')

    rows = new_tbody.split('<tr>')

    for row in rows:
        new_cols = ''
        cols = row.split('<td>')
        for col_id, col in enumerate(cols):
            if new_cols == '':
                new_cols = col
            else:
                new_cols += f"<td width='{widths[col_id]}'>{col}"
        finished_tbody += f"<tr>{new_cols}"

    return finished_tbody

def get_html_en(date_time, tbody, request):

    html = "<html><body>"
    html += "<center><h3>Usage Constracts</h3></center>"
    html += "<h4>" + date_time + "</h4>"
    html += "<font size='5' face='Courier New' >"
    html += "<table border='1' style='width:100%' >"
    html += "<thead>"
    html += get_header(request)
    html += "</thead>"
    html += get_body(tbody[0], 'no value')
    html += "</table>"
    # html += "</font>"
    # html += "<h4><i>Legend</i></h4>"
    # html += "<font size='5' face='Courier New' >"
    # html += "<p>Usg. Ctr. Type = Usage Contract Number</p>"
    # html += "<p>Ctr. Number = Contract Number</p>"
    # html += "<p>Rated V. = Rated Voltage</p>"
    # html += "<p>Bought V. = Bought Voltage</p>"
    # html += "<p>Tol. Range = Tolerance Range</p>"
    # html += "<p>Ctr. Value = Contract Value</p>"
    # html += "<p>Conn. Point = Connection Point</p>"
    # html += "</font>"
    html += "</body>"
    html += "</html>"

    return html


def get_html_pt(date_time, tbody, request):

    html = '<html><body>'
    html += "<center><h3>Contratos de Uso</h3></center>"
    html += "<h4>" + date_time + "</h4>"
    html += "<font size='5' face='Courier New' >"
    html += "<table border='1' style='width:100%' >"
    html += "<thead>"
    html += get_header(request)
    html += "</thead>"
    html += get_body(tbody[0], 'sem valor')
    html += "</table>"
    # html += "</font>"
    # html += "<h4><i>Legenda</i></h4>"
    # html += "<font size='5' face='Courier New' >"
    # html += "<p>Tipo Ctr. Usg. = Tipo de Contrato de Uso</p>"
    # html += "<p>Num. Ctr. = Número do Contrato</p>"
    # html += "<p>T. Nominal = Tensão Nominal</p>"
    # html += "<p>T. Contr. = Tensão Contratada</p>"
    # html += "<p>Faixa T. = Faixa de Tolerância</p>"
    # html += "<p>Fator P. = Fator de Potência</p>"
    # html += "<p>Valor Ctr. = Valor do Contrato</p>"
    # html += "</font>"
    html += "</body>"
    html += "</html>"
    
    return html


def generate_pdf_from_df(df, language, request):

    html_file = df.style.hide_index().set_table_styles(
       [{
           'selector': 'th',
           'props': [
               ('background-color', '#007E7A'),
               ('color', '#fff'),
               ('font-weight', 'bold')]
       },{
           'selector': '*',
           'props': [
               ('border', 'none')]
       }]).render()

    options = {
        'page-size': 'A4',  # to see sizes https://doc.qt.io/archives/qt-4.8/qprinter.html#PaperSize-enum
        'margin-top': '1cm',
        'margin-bottom': '1cm',
        'margin-left': '0.2cm',
        'margin-right': '0.2cm',
        'quiet': '',
        'orientation':'Landscape'
    }
    vale_logo_data = open("uploads/images/vale.png", "rb").read()
    vale_logo_encoded = b64encode(vale_logo_data).decode("utf-8")
    vale_logo_html = f"<img src='data:image/png;base64,{vale_logo_encoded}' width='150px'>"

    pdf_file = pdfkit.PDFKit('<meta charset="UTF-8">\n' + vale_logo_html + html_file, "string", options=options).to_pdf()

    return pdf_file


class CTUParser(object):

    def __init__(self):
        self.__lista = []

    @classmethod
    def get_valor(cls, _value_init, _items):
        for _key, _value in _items.items():
            if _value_init == _key:
                return _value

    @classmethod
    def value_or_none(cls, value):
        import re
        if value is None or value.strip() == '':
            return ' - '
        else:
            if re.match("^\d+\.\d+$", value):

                entrada = float(value)
                aux = str(entrada).split('.')
                valor = cls.group_number(int(aux[0]))

                if len(aux) == 2:
                    valor = valor + ',' + str(aux[1])
                    if len(aux[1]) == 1:
                        valor = valor + '0'
                return str(valor)
            else:
                return str(value)

    @classmethod
    def group_number(cls, number):
        s = '%d' % number
        groups = []
        while s and s[-1].isdigit():
            groups.append(s[-3:])
            s = s[:-3]
        return s + '.'.join(reversed(groups))

    def generate_data_frame(self, dict_values, request, language):

        if dict_values.__len__() >= 1:

            for valores in dict_values:

                # Remove data not relevant for the csv file
                for a in get_not_relevant_data():
                    del valores[a]

                ctu = {}
                for a, b in valores.items():

                    if 'usage_contract_type' == a:
                        ctu_type = b['id_usage_contract_type']
                        if ctu_type == 1:
                            ctu[translate_label('field_ctu_usage_contract_type', request)] = translate_label(
                                'field_ctu_type_d', request)
                        else:
                            ctu[translate_label('field_ctu_usage_contract_type', request)] = translate_label(
                                'field_ctu_type_t', request)

                    elif 'companys' == a:
                        key = translate_label('field_ctu_company', request)
                        ctu[key] = self.value_or_none(b['company_name'])

                    elif 'energy_dealers' == a:
                        key = translate_label(
                            'field_ctu_energy_dealer', request)
                        ctu[key] = self.value_or_none(b['company_name'])

                    elif 'rated_voltage' == a:
                        key1 = translate_label(
                            'field_ctu_rated_voltage', request)
                        ctu[key1] = self.value_or_none(b['voltages'])

                        key2 = translate_label('field_ctu_group', request)
                        ctu[key2] = self.value_or_none(b['group'])

                        key3 = translate_label('field_ctu_subgroup', request)
                        ctu[key3] = self.value_or_none(b['subgroup'])

                    elif 'create_date' == a:

                        key = translate_label('field_ctu_' + a, request)
                        value = datetime.strptime(b.split('.')[0].replace(
                            'T', ' '), '%Y-%m-%d %H:%M:%S').date()

                        if value != '':
                            if 'en' in language:
                                ctu[key] = value.strftime("%m/%d/%Y")
                            else:
                                ctu[key] = value.strftime("%d/%m/%Y")
                        else:
                            ctu[key] = ' - '

                    elif 'start_date' == a or 'end_date' == a:
                        key = translate_label('field_ctu_' + a, request)
                        value = datetime.strptime(b, '%Y-%m-%d').date()

                        if value != '':
                            if 'en' in language:
                                ctu[key] = value.strftime("%m/%d/%Y")
                            else:
                                ctu[key] = value.strftime("%d/%m/%Y")
                        else:
                            ctu[key] = ' - '

                    elif 'status' == a:
                        key = translate_label('field_ctu_' + a, request)
                        value = self.value_or_none(b)

                        if 'en' in language:
                            if value == 'S':
                                ctu[key] = 'Active'
                            else:
                                ctu[key] = 'Inactive'
                        else:
                            if value == 'S':
                                ctu[key] = 'Ativo'
                            else:
                                ctu[key] = 'Inativo'                            
                    else:
                        key = translate_label('field_ctu_' + a, request)
                        ctu[key] = self.value_or_none(b)

                self.__lista.append(ctu)

        df = DataFrame(self.__lista)
        return df

    def generate_pdf(self, dict_values, request):

        language = get_language(request)
        df = self.generate_data_frame(dict_values, request, language)
        return generate_pdf_from_df(df, language, request)
