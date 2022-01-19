from gauge_point.models import GaugePoint, SourcePme
from ..notifiable_modules import Modules
from ..notifiable_modules_abstract import AbstractClassNotifiableModule
from energy_composition.models import EnergyComposition, ApportiomentComposition

from django.db.models.signals import post_save
from django.dispatch import receiver
import notifications.business.signal_business as signal_business


class RegisterEnergyCompositionNotifiableModule(AbstractClassNotifiableModule):
    main_model = EnergyComposition
    module_name = Modules.REGISTER_ENERGY_COMPOSITION

    def get_specified_fields(self):
        return [
            'composition_name',
            'description',
            'cost_center',
            'profit_center',
            'composition_loss',
            'save_date',
            'data_source',
            'id_director__description',
            'id_segment__description',
            'id_accountant__description',
            'id_company__company_name',
            'id_business__description',
            'id_production_phase__description',
            'apport_energy_composition__id_company__company_name',
            'apport_energy_composition__volume_code',
            'apport_energy_composition__cost_code',
            'id_gauge_point_destination__id_source__display_name'
        ]

    def get_fields(self):
        non_related_fields, related_fields = super().get_fields()
        apport_energy_composition_additional_fields = []
        try:
            # apport company info
            apport_energy_composition_additional_fields = super().get_fields(
                specific_model=ApportiomentComposition,
                source_path="apport_energy_composition",
            )
            apport_energy_composition_additional_fields = [
                k
                for k in apport_energy_composition_additional_fields[1]
                if k["name"] == "apport_energy_composition__id_company__company_name"
                or k["name"] == "apport_energy_composition__id_company__legal_name"
            ]

            meter_destination_additional_fields = super().get_fields(
                specific_model=SourcePme,
                source_path="id_gauge_point_destination__id_source",
            )
            meter_destination_additional_fields = [
                k
                for k in meter_destination_additional_fields[0]
                if k["name"] == "id_gauge_point_destination__id_source__display_name"
            ]
        except IndexError:
            pass

        related_fields += apport_energy_composition_additional_fields
        related_fields += meter_destination_additional_fields

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
        kwargs["notifiable_module"] = RegisterEnergyCompositionNotifiableModule()
        signal_business.NotificationSignalBusiness.dispatch_signal(
            sender, instance, **kwargs
        )
