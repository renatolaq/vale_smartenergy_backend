from datetime import date
from locales.translates_function import translate_label, translate_logical_and
from .list import queryset_name_to_string
from company.models import Company
from budget.models.CompanyBudget import CompanyBudget
from gauge_point.models import GaugePoint, GaugeEnergyDealership, SourcePme


def generate_delete_msg(budget, gauge_point, request):

    msg = translate_label("error_ctu_update_link", request)

    if budget:
        msg += f'{translate_label("budget(s)", request)}: {queryset_name_to_string(budget)}'
    if budget and gauge_point:
        msg += f" {translate_logical_and(request)} "
    if gauge_point:
        msg += f'{translate_label("gauge_point", request)}: {queryset_name_to_string(gauge_point)}'

    return msg


def return_linked_budgets(usage_contract):
    budgets = []

    today = date.today()

    if today < usage_contract.end_date:
        budgets_ids = CompanyBudget.objects.filter(
            company_id=usage_contract.company_id
        ).values_list("company_id")
        budgets = Company.objects.filter(id_company__in=budgets_ids).values_list(
            "company_name"
        )

    return budgets


def return_linked_gauges(usage_contract):
    source_pme_name = SourcePme.objects.filter(
        gauge_source__id_company=usage_contract.company_id,
        gauge_source__connection_point=usage_contract.connection_point,
        gauge_source__gauge_dealership__id_dealership=usage_contract.energy_dealer.id_company,
        gauge_source__status="S",
    ).values_list("display_name")

    return source_pme_name
