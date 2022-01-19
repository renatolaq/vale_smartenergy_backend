from assets.models import Assets
from ..notifiable_modules import Modules
from ..notifiable_modules_abstract import AbstractClassNotifiableModule
from asset_items.models import AssetItems, SeasonalityAssetItem, SeasonalityAssetItemCost, SeazonalityAssetItemDepreciation
from core.models import Seasonality

from django.db.models.signals import post_save
from django.dispatch import receiver
import notifications.business.signal_business as signal_business


class RegisterAssetItemNotifiableModule(AbstractClassNotifiableModule):
    main_model = AssetItems
    module_name = Modules.REGISTER_ASSET_ITEM

    def get_specified_fields(self):
        return [
            'id_company__company_name',
            'id_company__characteristics',
            'id_energy_composition__composition_name',
            'id_energy_composition__cost_center',
            "id_assets__id_company__company_name",
            'assetitem_seasonality__id_seasonality__year',
            'assetitem_seasonality__id_seasonality__measure_unity',
            'assetitem_seasonality__id_seasonality__january',
            'assetitem_seasonality__id_seasonality__february',
            'assetitem_seasonality__id_seasonality__march',
            'assetitem_seasonality__id_seasonality__april',
            'assetitem_seasonality__id_seasonality__may',
            'assetitem_seasonality__id_seasonality__june',
            'assetitem_seasonality__id_seasonality__july',
            'assetitem_seasonality__id_seasonality__august',
            'assetitem_seasonality__id_seasonality__september',
            'assetitem_seasonality__id_seasonality__october',
            'assetitem_seasonality__id_seasonality__november',
            'assetitem_seasonality__id_seasonality__december',
            'assetitem_cost__id_seazonality_asset__year',
            'assetitem_cost__id_seazonality_asset__measure_unity',
            'assetitem_cost__id_seazonality_asset__january',
            'assetitem_cost__id_seazonality_asset__february',
            'assetitem_cost__id_seazonality_asset__march',
            'assetitem_cost__id_seazonality_asset__april',
            'assetitem_cost__id_seazonality_asset__may',
            'assetitem_cost__id_seazonality_asset__june',
            'assetitem_cost__id_seazonality_asset__july',
            'assetitem_cost__id_seazonality_asset__august',
            'assetitem_cost__id_seazonality_asset__september',
            'assetitem_cost__id_seazonality_asset__october',
            'assetitem_cost__id_seazonality_asset__november',
            'assetitem_cost__id_seazonality_asset__december',
            'assetitem_depreciation__id_seasonality__year',
            'assetitem_depreciation__id_seasonality__measure_unity',
            'assetitem_depreciation__id_seasonality__january',
            'assetitem_depreciation__id_seasonality__february',
            'assetitem_depreciation__id_seasonality__march',
            'assetitem_depreciation__id_seasonality__april',
            'assetitem_depreciation__id_seasonality__may',
            'assetitem_depreciation__id_seasonality__june',
            'assetitem_depreciation__id_seasonality__july',
            'assetitem_depreciation__id_seasonality__august',
            'assetitem_depreciation__id_seasonality__september',
            'assetitem_depreciation__id_seasonality__october',
            'assetitem_depreciation__id_seasonality__november',
            'assetitem_depreciation__id_seasonality__december',
        ]

    def get_fields(self):
        non_related_fields, related_fields = super().get_fields()
        additional_asset_fields = []
        seasonality_asset_item_fields = []
        seasonality_asset_item_cost_fields = []
        seasonality_asset_item_depreciation_fields = []

        try:
            additional_asset_fields = super().get_fields(
                specific_model=Assets, source_path="id_assets"
            )
            additional_asset_fields = [
                k
                for k in additional_asset_fields[1]
                if k["name"] == "id_assets__id_company__company_name"
            ]

            seasonality_asset_item_fields = super().get_fields(
                specific_model=SeasonalityAssetItem, source_path="assetitem_seasonality"
            )
            seasonality_asset_item_fields_specified_fields = [
                'assetitem_seasonality__id_seasonality__year',
                'assetitem_seasonality__id_seasonality__measure_unity',
                'assetitem_seasonality__id_seasonality__january',
                'assetitem_seasonality__id_seasonality__february',
                'assetitem_seasonality__id_seasonality__march',
                'assetitem_seasonality__id_seasonality__april',
                'assetitem_seasonality__id_seasonality__may',
                'assetitem_seasonality__id_seasonality__june',
                'assetitem_seasonality__id_seasonality__july',
                'assetitem_seasonality__id_seasonality__august',
                'assetitem_seasonality__id_seasonality__september',
                'assetitem_seasonality__id_seasonality__october',
                'assetitem_seasonality__id_seasonality__november',
                'assetitem_seasonality__id_seasonality__december'
            ]
            seasonality_asset_item_fields = [
                k
                for k in seasonality_asset_item_fields[1]
                if k["name"] in seasonality_asset_item_fields_specified_fields
            ]

            seasonality_asset_item_cost_fields = super().get_fields(
                specific_model=SeasonalityAssetItemCost, source_path="assetitem_cost"
            )
            seasonality_asset_item_cost_specified_fields = [
                'assetitem_cost__id_seazonality_asset__year',
                'assetitem_cost__id_seazonality_asset__measure_unity',
                'assetitem_cost__id_seazonality_asset__january',
                'assetitem_cost__id_seazonality_asset__february',
                'assetitem_cost__id_seazonality_asset__march',
                'assetitem_cost__id_seazonality_asset__april',
                'assetitem_cost__id_seazonality_asset__may',
                'assetitem_cost__id_seazonality_asset__june',
                'assetitem_cost__id_seazonality_asset__july',
                'assetitem_cost__id_seazonality_asset__august',
                'assetitem_cost__id_seazonality_asset__september',
                'assetitem_cost__id_seazonality_asset__october',
                'assetitem_cost__id_seazonality_asset__november',
                'assetitem_cost__id_seazonality_asset__december'
            ]
            seasonality_asset_item_cost_fields = [
                k
                for k in seasonality_asset_item_cost_fields[1]
                if k['name'] in seasonality_asset_item_cost_specified_fields
            ]

            seasonality_asset_item_depreciation_fields = super().get_fields(
                specific_model=SeazonalityAssetItemDepreciation, source_path="assetitem_depreciation"
            )
            seasonality_asset_item_depreciation_specified_fields = [
                'assetitem_depreciation__id_seasonality__year',
                'assetitem_depreciation__id_seasonality__measure_unity',
                'assetitem_depreciation__id_seasonality__january',
                'assetitem_depreciation__id_seasonality__february',
                'assetitem_depreciation__id_seasonality__march',
                'assetitem_depreciation__id_seasonality__april',
                'assetitem_depreciation__id_seasonality__may',
                'assetitem_depreciation__id_seasonality__june',
                'assetitem_depreciation__id_seasonality__july',
                'assetitem_depreciation__id_seasonality__august',
                'assetitem_depreciation__id_seasonality__september',
                'assetitem_depreciation__id_seasonality__october',
                'assetitem_depreciation__id_seasonality__november',
                'assetitem_depreciation__id_seasonality__december'
            ]
            seasonality_asset_item_depreciation_fields = [
                k
                for k in seasonality_asset_item_depreciation_fields[1]
                if k['name'] in seasonality_asset_item_depreciation_specified_fields
            ]

        except IndexError:
            pass


        related_fields += additional_asset_fields + seasonality_asset_item_fields + seasonality_asset_item_depreciation_fields + seasonality_asset_item_cost_fields

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
        kwargs["notifiable_module"] = RegisterAssetItemNotifiableModule()
        signal_business.NotificationSignalBusiness.dispatch_signal(
            sender, instance, **kwargs
        )
