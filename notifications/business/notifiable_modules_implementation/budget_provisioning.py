from ..notifiable_modules import Modules
from ..notifiable_modules_abstract import AbstractClassNotifiableModule
from budget.models.Budget import Budget
from budget.models.MonthlyBudget import MonthlyBudget
from budget.models.CompanyBudget import CompanyBudget
from budget.models.CompanyBudgetRevision import CompanyBudgetRevision

from django.db.models.signals import post_save
from django.dispatch import receiver
import notifications.business.signal_business as signal_business


def generate_month_fields(year):
    months = [
        "january",
        "february",
        "march",
        "april",
        "may",
        "june",
        "july",
        "august",
        "september",
        "october",
        "november",
        "december"
    ]

    year_fields = []

    for month in months:
        year_fields += generate_year_rows(year, month)

    return year_fields

def generate_year_rows(year, month):
    base_fields = [
        'contracted_peak_power_demand',
        'contracted_offpeak_power_demand',
        'estimated_peak_power_demand',
        'estimated_offpeak_power_demand',
        'consumption_peak_power_demand',
        'consumption_offpeak_power_demand',
        'production',
        'productive_stops',
        'total_consumption',
        'utilization_factor_consistency_offpeakpower',
        'utilization_factor_consistency_peakpower',
        'loadfactor_consistency_offpeakpower',
        'loadfactor_consistency_peakpower',
        'uniqueload_factor_consistency',
        'modulation_factor_consistency',
        'specific_consumption',
    ]

    return [f'companybudgetrevision__{year}__{month}__{field}' for field in base_fields]

class BudgetProvisioningNotifiableModule(AbstractClassNotifiableModule):
    main_model = CompanyBudget
    module_name = Modules.BUDGET_PROVISIONING

    firstyear_budget_specified_fields = generate_month_fields('firstyear_budget')
    secondyear_budget_specified_fields = generate_month_fields('secondyear_budget')
    thirdyear_budget_specified_fields = generate_month_fields('thirdyear_budget')
    fourthyear_budget_specified_fields = generate_month_fields('fourthyear_budget')
    fifthyear_budget_specified_fields = generate_month_fields('fifthyear_budget')

    def get_specified_fields(self):
        return [
            'year',
            'companybudgetrevision__contract_usage_factor_peak',
            'companybudgetrevision__contract_usage_factor_offpeak',
            'companybudgetrevision__consumption_limit',
            *self.firstyear_budget_specified_fields,
            *self.secondyear_budget_specified_fields,
            *self.thirdyear_budget_specified_fields,
            *self.fourthyear_budget_specified_fields,
            *self.fifthyear_budget_specified_fields
        ]

    def get_fields(self):
        non_related_fields, related_fields = super().get_fields()
        firstyear_budget_fields = []
        secondyear_budget_fields = []
        thirdyear_budget_fields = []
        fourthyear_budget_fields = []
        fifth_budget_fields = []

        try: 
            firstyear_budget_fields = super().get_fields(
                specific_model=MonthlyBudget,
                source_path="companybudgetrevision__firstyear_budget"
            )
            firstyear_budget_fields = [
                k
                for k in firstyear_budget_fields[1]
                if k['name'] in self.firstyear_budget_specified_fields
            ]

            secondyear_budget_fields = super().get_fields(
                specific_model=MonthlyBudget,
                source_path="companybudgetrevision__secondyear_budget"
            )
            secondyear_budget_fields = [
                k
                for k in secondyear_budget_fields[1]
                if k['name'] in self.secondyear_budget_specified_fields
            ]

            thirdyear_budget_fields = super().get_fields(
                specific_model=MonthlyBudget,
                source_path="companybudgetrevision__thirdyear_budget"
            )
            thirdyear_budget_fields = [
                k
                for k in thirdyear_budget_fields[1]
                if k['name'] in self.thirdyear_budget_specified_fields
            ]

            fourthyear_budget_fields = super().get_fields(
                specific_model=MonthlyBudget,
                source_path="companybudgetrevision__fourthyear_budget"
            )
            fourthyear_budget_fields = [
                k
                for k in fourthyear_budget_fields[1]
                if k['name'] in self.fourthyear_budget_specified_fields
            ]

            fifthyear_budget_fields = super().get_fields(
                specific_model=MonthlyBudget,
                source_path="companybudgetrevision__fifthyear_budget"
            )
            fifthyear_budget_fields = [
                k
                for k in fifthyear_budget_fields[1]
                if k['name'] in self.fifthyear_budget_specified_fields
            ]
        except IndexError:
            pass

        related_fields += firstyear_budget_fields + secondyear_budget_fields + thirdyear_budget_fields + fourthyear_budget_fields + fifthyear_budget_fields

        specified_fields = self.get_specified_fields()

        non_related_fields = [
            field for field in non_related_fields if field["name"] in specified_fields
        ]
        related_fields = [
            field for field in related_fields if field["name"] in specified_fields
        ]

        return non_related_fields, related_fields

    @staticmethod
    @receiver(post_save, sender=main_model)
    def post_save_signal_handler(sender, instance, **kwargs):
        kwargs["notifiable_module"] = BudgetProvisioningNotifiableModule()
        signal_business.NotificationSignalBusiness.dispatch_signal(
            sender, instance, **kwargs
        )
