from ..notifiable_modules import Modules
from ..notifiable_modules_abstract import AbstractClassNotifiableModule
from assets.models import Assets, Submarket, AssetsComposition, SeasonalityProinfa
from asset_items.models import AssetItems
from company.models import Company
from usage_contract.models import UsageContract
from energy_composition.models import EnergyComposition

from django.db.models.signals import post_save
from django.dispatch import receiver
import notifications.business.signal_business as signal_business


class RegisterAssetNotifiableModule(AbstractClassNotifiableModule):
    main_model = Assets
    module_name = Modules.REGISTER_ASSET

    def get_specified_fields(self):
      return [
            'id_company__company_name',
            'id_profile__name_profile',
            'id_ccee_siga__type',
            'id_submarket__description',
            'id_company__company__contract_number',
            'show_balance',
            'id_ccee_proinfa__code_ccee',
            'id_ccee_proinfa__id_ccee_SeasonalityProinfa__id_seasonality__year',
            'id_ccee_proinfa__id_ccee_SeasonalityProinfa__id_seasonality__measure_unity',
            'id_ccee_proinfa__id_ccee_SeasonalityProinfa__id_seasonality__january',
            'id_ccee_proinfa__id_ccee_SeasonalityProinfa__id_seasonality__february',
            'id_ccee_proinfa__id_ccee_SeasonalityProinfa__id_seasonality__march',
            'id_ccee_proinfa__id_ccee_SeasonalityProinfa__id_seasonality__april',
            'id_ccee_proinfa__id_ccee_SeasonalityProinfa__id_seasonality__may',
            'id_ccee_proinfa__id_ccee_SeasonalityProinfa__id_seasonality__june',
            'id_ccee_proinfa__id_ccee_SeasonalityProinfa__id_seasonality__july',
            'id_ccee_proinfa__id_ccee_SeasonalityProinfa__id_seasonality__august',
            'id_ccee_proinfa__id_ccee_SeasonalityProinfa__id_seasonality__september',
            'id_ccee_proinfa__id_ccee_SeasonalityProinfa__id_seasonality__october',
            'id_ccee_proinfa__id_ccee_SeasonalityProinfa__id_seasonality__november',
            'id_ccee_proinfa__id_ccee_SeasonalityProinfa__id_seasonality__december',
            'assetitems_asset__id_company__company_name',
            'assetitems_asset__id_energy_composition__composition_name',
            'assetitems_asset__id_company__characteristics',
            'assetitems_asset__id_energy_composition__cost_center',
        ]

    def get_fields(self):
        non_related_fields, related_fields = super().get_fields()
        assets_composition_additional_data = []
        usage_contract_fields = []
        seasonality_proinfa_fields = []
        asset_item_energy_composition_fields = []
        asset_item_company_fields = []

        try:
            assets_composition_additional_data = super().get_fields(
                specific_model=AssetsComposition,
                source_path="AssetsComposition_id_assets",
            )
            assets_composition_additional_data = [
                k
                for k in assets_composition_additional_data[1]
                if k["name"]
                == "AssetsComposition_id_assets__id_energy_composition__composition_name"
            ]

            usage_contract_fields = super().get_fields(
                specific_model=UsageContract, source_path="id_company__company"
            )
            usage_contract_fields = [
                k
                for k in usage_contract_fields[0]
                if k["name"]
                == "id_company__company__contract_number"
            ]

            seasonality_proinfa_fields = super().get_fields(
                specific_model=SeasonalityProinfa, source_path="id_ccee_proinfa__id_ccee_SeasonalityProinfa"
            )
            seasonality_proinfa_specified_fields = [
                'id_ccee_proinfa__id_ccee_SeasonalityProinfa__id_seasonality__year',
                'id_ccee_proinfa__id_ccee_SeasonalityProinfa__id_seasonality__measure_unity',
                'id_ccee_proinfa__id_ccee_SeasonalityProinfa__id_seasonality__january',
                'id_ccee_proinfa__id_ccee_SeasonalityProinfa__id_seasonality__february',
                'id_ccee_proinfa__id_ccee_SeasonalityProinfa__id_seasonality__march',
                'id_ccee_proinfa__id_ccee_SeasonalityProinfa__id_seasonality__april',
                'id_ccee_proinfa__id_ccee_SeasonalityProinfa__id_seasonality__may',
                'id_ccee_proinfa__id_ccee_SeasonalityProinfa__id_seasonality__june',
                'id_ccee_proinfa__id_ccee_SeasonalityProinfa__id_seasonality__july',
                'id_ccee_proinfa__id_ccee_SeasonalityProinfa__id_seasonality__august',
                'id_ccee_proinfa__id_ccee_SeasonalityProinfa__id_seasonality__september',
                'id_ccee_proinfa__id_ccee_SeasonalityProinfa__id_seasonality__october',
                'id_ccee_proinfa__id_ccee_SeasonalityProinfa__id_seasonality__november',
                'id_ccee_proinfa__id_ccee_SeasonalityProinfa__id_seasonality__december',
            ]
            seasonality_proinfa_fields = [
                k
                for k in seasonality_proinfa_fields[1]
                if k['name'] in seasonality_proinfa_specified_fields
            ]

            asset_item_energy_composition_fields = super().get_fields(
                specific_model=EnergyComposition, source_path="assetitems_asset__id_energy_composition"
            )
            asset_item_energy_composition_specified_fields = [
                'assetitems_asset__id_energy_composition__composition_name',
                'assetitems_asset__id_energy_composition__cost_center'
            ]
            asset_item_energy_composition_fields = [
                k
                for k in asset_item_energy_composition_fields[0]
                if k['name'] in asset_item_energy_composition_specified_fields
            ]


            asset_item_company_fields = super().get_fields(
                specific_model=Company, source_path="assetitems_asset__id_company"
            )
            asset_item_company_specified_fields = [
                'assetitems_asset__id_company__company_name',
                'assetitems_asset__id_company__characteristics',
            ]
            asset_item_company_fields = [
                k
                for k in asset_item_company_fields[0]
                if k['name'] in asset_item_company_specified_fields
            ]
        except IndexError:
            pass
        


        related_fields += assets_composition_additional_data + usage_contract_fields + seasonality_proinfa_fields + asset_item_energy_composition_fields + asset_item_company_fields
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
            if field_name == "id_submarket__description":
                submarket_options = Submarket.objects.all().values("description")
                field["options"] = [value["description"] for value in submarket_options]

            if field_name == "show_balance":
                field["options"] = ["Assets", "Asset items"]

    @staticmethod
    @receiver(post_save, sender=main_model)
    def post_save_signal_handler(sender, instance, **kwargs):
        kwargs["notifiable_module"] = RegisterAssetNotifiableModule()
        signal_business.NotificationSignalBusiness.dispatch_signal(
            sender, instance, **kwargs
        )
