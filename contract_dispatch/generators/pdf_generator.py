from jinja2 import Environment, PackageLoader, select_autoescape

from SmartEnergy.settings import BASE_DIR
from contract_dispatch.business.contract_dispatch_business import (
    ContractDispatchBusiness,
)
import pdfkit

env = Environment(
    loader=PackageLoader("contract_dispatch", "templates"),
    autoescape=select_autoescape(["html", "xml"]),
)


def generate_pdf(request):
    contracts_by_month = ContractDispatchBusiness.retrieve_contracts_dict_list_by_month(
        request
    )
    result = generate(contracts_by_month, True)
    return result


def generate_pdf_by_contract(request, contract_dispatch):
    contracts_by_month = ContractDispatchBusiness.retrieve_contracts_dict_list_by_contract_dispatch(
        request, contract_dispatch
    )
    result = generate(contracts_by_month, False)
    return result


def generate_pdf_contracts_to_send(request, year, month, balance_id=None):
    contracts = ContractDispatchBusiness.retrieve_contracts_dict_list_contracts_to_send(
        request, year, month, balance_id
    )

    result = generate(contracts, False)
    return result


def generate_pdf_contracts_by_ids(request, year, month, balance_id, ids):
    contracts = ContractDispatchBusiness.retrieve_contracts_dict_list_by_contract_cliq_ids(
        request, year, month, balance_id, ids
    )

    result = generate(contracts, False)
    return result


def generate(data, display_title):
    template = env.get_template("pdf_template.html")
    image_file = f"{BASE_DIR}/SmartEnergy/static/vale-logo.png"

    rendered_template = template.render(
        data=data, image_file=image_file, display_title=display_title
    )

    result = pdfkit.PDFKit(rendered_template, "string").to_pdf()
    return result
