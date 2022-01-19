from ..notifiable_modules import Modules
from ..notifiable_modules_abstract import AbstractClassNotifiableModule
from company.models import Company, Country, AccountType, State
from energy_composition.models import EnergyComposition

from django.db.models.signals import post_save
from django.dispatch import receiver
import notifications.business.signal_business as signal_business


class RegisterCompanyNotifiableModule(AbstractClassNotifiableModule):
    main_model = Company
    module_name = Modules.REGISTER_COMPANY

    def get_specified_fields(self):
        return [
            "company_name",
            "legal_name",
            "registered_number",
            "type",
            "state_number",
            "id_sap",
            "id_address__zip_code",
            "id_address__street",
            "id_address__number",
            "id_address__complement",
            "id_address__neighborhood",
            "id_address__id_city__id_state__name",
            "nationality",
            "characteristics",
            "id_company_bank__bank",
            "id_company_bank__bank_agency",
            "id_company_bank__account_number",
            "id_company_bank__other",
            "id_company_bank__main_account",
            "id_company_contacts__type",
            "id_company_contacts__responsible",
            "id_company_contacts__email",
            "id_company_contacts__cellphone",
            "id_company_contacts__phone",
            "id_company_eletric__instaled_capacity",
            "id_company_eletric__guaranteed_power",
            "id_company_eletric__regulatory_act",
            "id_company_eletric__internal_loss",
            "id_company_eletric__transmission_loss",
            "energyComposition_company__composition_name",
            "energyComposition_company__description",
            "energyComposition_company__id_business__description",
            "energyComposition_company__id_director__description",
            "energyComposition_company__id_segment__description",
            "energyComposition_company__id_accountant__description",
            "energyComposition_company__profit_center",
        ]   

    def get_fields(self):
        non_related_fields, related_fields = super().get_fields()
        additional_bank_fields = []
        additional_energy_composition_fields = []
        additional_state_fields = []
        try:
            additional_bank_fields = super().get_fields(
                specific_model=AccountType, source_path="id_company_bank__account_type"
            )

            additional_bank_fields = [
                k
                for k in additional_bank_fields[0]
                if k["name"] == "id_company_bank__account_type__description"
            ]

            additional_energy_composition_fields = super().get_fields(
                specific_model=EnergyComposition,
                source_path="energyComposition_company",
            )

            energy_composition_fields = [
                "energyComposition_company__id_business__description",
                "energyComposition_company__id_director__description",
                "energyComposition_company__id_segment__description",
                "energyComposition_company__id_accountant__description",
            ]

            additional_energy_composition_fields = [
                k
                for k in additional_energy_composition_fields[1]
                if k["name"] in energy_composition_fields
            ]

            additional_state_fields = super().get_fields(
                specific_model=State,
                source_path="id_address__id_city__id_state",
            )

            additional_state_fields = [
                k
                for k in additional_state_fields[0]
                if k["name"] == "id_address__id_city__id_state__name"
            ]
        except IndexError:
            pass

        related_fields += additional_bank_fields
        related_fields += additional_energy_composition_fields
        related_fields += additional_state_fields

        self.add_field_options(non_related_fields, related_fields)

        specified_fields = self.get_specified_fields()

        non_related_fields = [
            field for field in non_related_fields if field["name"] in specified_fields
        ]
        related_fields = [
            field for field in related_fields if field["name"] in specified_fields
        ]

        return non_related_fields, related_fields


    def add_field_options(self, non_related_fields, related_fields):
        for field in non_related_fields + related_fields:
            field_name = field.get("name")
            if field_name == "nationality":
                countries = Country.objects.all().values("initials")
                field["options"] = [value["initials"] for value in countries]
            if field_name == "characteristics":
                field["options"] = ["consumidora", "geradora"]

            if field_name == "id_company_bank__account_type__description":
                account_types = AccountType.objects.all().values("description")
                field["options"] = [value["description"] for value in account_types]

    @staticmethod
    @receiver(post_save, sender=main_model)
    def post_save_signal_handler(sender, instance, **kwargs):
        kwargs["notifiable_module"] = RegisterCompanyNotifiableModule()
        signal_business.NotificationSignalBusiness.dispatch_signal(
            sender, instance, **kwargs
        )
