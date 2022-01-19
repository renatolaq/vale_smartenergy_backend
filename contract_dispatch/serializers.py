from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from django.utils import timezone
from datetime import datetime
from django.db import transaction


from agents.models import Agents
from assets.models import Submarket
from assets.serializersViews import CompanySerializer

from contract_dispatch.business.contract_dispatch_business import (
    ContractDispatchBusiness,
)
from contract_dispatch.models import (
    ContractDispatch,
    ContractDispatchCliqContract,
    CliqContractCurrentStatus,
    CliqContractStatus,
    CliqCceeProcessment,
    CliqCceeProcessmentResult,
    CliqContractCCEEState,
    CliqContractCCEEPeriodInfo,
)
from cliq_contract.models import CliqContract
from cliq_contract.serializers import CliqContractSerializer
from balance_report_market_settlement.models import Report


class ContractDispatchBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ["id", "report_name"]


class ContractDispatchDetailSerializer(serializers.ModelSerializer):
    sentDate = serializers.DateTimeField(source="dispatch_date", read_only=True)
    user = serializers.CharField(source="dispatch_username", max_length=50)
    supplyDate = serializers.DateTimeField(
        source="supply_date", input_formats=["%Y-%m-%d", "%Y-%m"]
    )
    lastUpdateDate = serializers.DateTimeField(
        source="last_status_update_date", read_only=True
    )

    class Meta:
        model = ContractDispatch
        fields = ["id", "sentDate", "user", "supplyDate", "lastUpdateDate"]
        read_only_fields = fields


class AgentsCCEEStateSerializer(serializers.ModelSerializer):
    company_detail = CompanySerializer(source="id_company", read_only=True)
    status = serializers.CharField(default="S", required=False)

    class Meta:
        model = Agents
        fields = (
            "id_agents",
            "id_company",
            "vale_name_agent",
            "status",
            "company_detail",
        )
        read_only_fields = fields


class CliqContractListSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="id_contract_cliq")
    contractType = serializers.CharField(source="ccee_type_contract")
    category = serializers.CharField(required=False)
    operation = serializers.CharField(required=False)
    cliqCode = serializers.CharField(
        required=False, max_length=40, source="id_ccee.code_ccee"
    )
    modality = serializers.CharField(source="id_contract.modality")
    name = serializers.CharField(source="id_contract.contract_name")
    volume = serializers.DecimalField(
        source="volume_final", max_digits=18, decimal_places=9, required=False
    )
    buyerAgent = serializers.CharField(
        source="id_buyer_profile.id_agents.vale_name_agent", default=None
    )
    buyerProfile = serializers.CharField(
        source="id_buyer_profile.name_profile", default=None
    )
    salesAgent = serializers.CharField(
        source="id_vendor_profile.id_agents.vale_name_agent", default=None
    )
    salesProfile = serializers.CharField(
        source="id_vendor_profile.name_profile", default=None
    )
    status = serializers.CharField(source="status_val", required=False)

    class Meta:
        model = CliqContract
        fields = [
            "id",
            "contractType",
            "category",
            "operation",
            "cliqCode",
            "modality",
            "name",
            "volume",
            "buyerAgent",
            "buyerProfile",
            "salesAgent",
            "salesProfile",
            "status",
        ]
        read_only_fields = fields


class ProcessmentResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = CliqCceeProcessmentResult
        fields = ["status", "description"]


class ProcessmentSerializer(serializers.ModelSerializer):
    processment_result = ProcessmentResultSerializer(many=True)

    class Meta:
        model = CliqCceeProcessment
        fields = ["processment_result"]


class ContractUpdateSerializer(serializers.Serializer):
    id_cliq_contract = serializers.PrimaryKeyRelatedField(
        queryset=CliqContract.objects.all()
    )
    cliq_code = serializers.CharField(
        required=False, max_length=40, allow_blank=True, allow_null=True
    )
    status_date = serializers.DateField(input_formats=["%Y-%m"])
    status = serializers.ChoiceField(
        choices=[name for name, member in CliqContractStatus.__members__.items()]
    )


class ContractDispatchUpdateContractsSerializer(serializers.Serializer):
    """
    Update cliq contract status

    Three operations are performed:
        - Cliq contract status is updated
        - Cliq contract ccee code is updated if cliq_code is within the payload
        - Contract dispatch last update date is updated
    """

    updates = ContractUpdateSerializer(many=True)

    @transaction.atomic
    def create(self, validated_data):
        contract_dispatches_to_update = set()

        for update in validated_data["updates"]:
            cliq_contract = update["id_cliq_contract"]

            current_status_queryset = CliqContractCurrentStatus.objects.filter(
                cliq_contract=cliq_contract
            )

            year = int(update["status_date"].strftime("%Y"))
            month = int(update["status_date"].strftime("%m"))
            current_status_queryset = current_status_queryset.filter(
                status_date__year=year, status_date__month=month
            )

            if not current_status_queryset:
                cliq_contract_current_status = CliqContractCurrentStatus(
                    cliq_contract=cliq_contract,
                    status_date=update["status_date"],
                    status=CliqContractStatus[update["status"]],
                )
                cliq_contract_current_status.save()
            else:
                cliq_contract_current_status = current_status_queryset.first()
                cliq_contract_current_status.status = CliqContractStatus[
                    update["status"]
                ]
                cliq_contract_current_status.save()

            contract_dispatches_cliq_contract = cliq_contract.contract_dispatches.all()
            for dispatch in contract_dispatches_cliq_contract:
                dispatch_status = cliq_contract.contract_dispatch_status.filter(
                    status_date__year=year, status_date__month=month
                )
                dispatch.contract_dispatch.last_status_update_date = (
                    dispatch_status.first().updated_at
                )
                contract_dispatches_to_update.add(dispatch.contract_dispatch)

            cliq_code = update.get("cliq_code")
            if cliq_code is not None:
                ccee_description = cliq_contract.id_ccee
                ccee_description.code_ccee = cliq_code

                cliq_contract_serializer = CliqContractSerializer(cliq_contract)
                data = cliq_contract_serializer.data
                cliq_contract_serializer_update = CliqContractSerializer(
                    cliq_contract, data=data
                )
                cliq_contract_serializer_update.is_valid(raise_exception=True)
                cliq_contract_serializer_update.user = "Integração CCEE"
                cliq_contract_serializer_update.save()

        for contract_dispatch in contract_dispatches_to_update:
            contract_dispatch.save()
        return validated_data


class ContractDispatchSerializerView(serializers.ModelSerializer):
    sentDate = serializers.DateTimeField(source="dispatch_date", read_only=True)
    user = serializers.CharField(source="dispatch_username", max_length=50)
    supplyDate = serializers.DateTimeField(source="supply_date")
    lastUpdateDate = serializers.DateTimeField(
        source="last_status_update_date", read_only=True
    )
    has_processment_errors = serializers.SerializerMethodField()

    class Meta:
        model = ContractDispatch
        fields = [
            "id",
            "sentDate",
            "user",
            "supplyDate",
            "lastUpdateDate",
            "has_processment_errors",
        ]

    def get_has_processment_errors(self, obj):
        return CliqCceeProcessmentResult.objects.filter(
            id_cliq_ccee_processment__in=obj.contractdispatchcliqcontract_set.values(
                "cliq_ccee_processment"
            ),
            status="ERRO",
        ).exists()


class ContractDispatchInfoSerializer(serializers.Serializer):
    contractId = serializers.PrimaryKeyRelatedField(queryset=CliqContract.objects.all())
    operation = serializers.CharField()
    volume = serializers.DecimalField(max_digits=18, decimal_places=9)


class ContractDispatchSerializer(serializers.Serializer):
    sentDate = serializers.DateTimeField(source="dispatch_date", read_only=True)
    contractInfo = ContractDispatchInfoSerializer(many=True)
    user = serializers.CharField(source="dispatch_username", max_length=50)
    supplyDate = serializers.DateTimeField(
        source="supply_date", input_formats=["%Y-%m-%d", "%Y-%m"]
    )
    lastUpdateDate = serializers.DateTimeField(
        source="last_status_update_date", read_only=True
    )

    def to_representation(self, value):
        view_serializer = ContractDispatchSerializerView(value)
        return view_serializer.data

    def validate_contractInfo(self, contracts):
        if not contracts:
            raise serializers.ValidationError(
                "At least one contract is required for dispatch"
            )
        return contracts

    def retrieve_current_status(self, contract, supply_date):
        current_status_queryset = CliqContractCurrentStatus.objects.filter(
            cliq_contract=contract
        )

        year, month = supply_date.split("-", 1)
        current_status_queryset = current_status_queryset.filter(
            status_date__year=year, status_date__month=month
        )

        if not current_status_queryset:
            if (
                contract.id_contract.modality == "Transferencia"
                or contract.id_contract.type == "V"
            ):
                return CliqContractStatus.NOT_SENT
            elif contract.id_contract.type == "C":
                return CliqContractStatus.REGISTERED_NOT_VALIDATED
            else:
                raise ValueError("Incorrect values for contract modality or type")
        else:
            cliq_contract_current_status = current_status_queryset.first()
            return cliq_contract_current_status.status

    def month_year_iter(self, start_month, start_year, end_month, end_year):
        ym_start = 12 * start_year + start_month - 1
        ym_end = 12 * end_year + end_month - 1
        for ym in range(ym_start, ym_end):
            y, m = divmod(ym, 12)
            yield y, m + 1

    @transaction.atomic
    def create(self, validated_data):
        # Since ManyToMany intermediate table had to be defined
        # Intermediate table is also filled manually
        supply_date = self.initial_data["supplyDate"]
        contracts = validated_data.pop("contractInfo")
        contract_dispatch = ContractDispatch.objects.create(
            dispatch_date=timezone.now(),
            last_status_update_date=timezone.now(),
            **validated_data,
        )

        contract_dispatch_cliq_contract = []
        for contract in contracts:
            cliq_contract = contract.get("contractId")
            ccee_result = [
                value
                for value in self.context.get("ccee_integration_response", [])
                if value.get("id_contract_cliq") == cliq_contract.pk
            ]

            current_status = self.retrieve_current_status(cliq_contract, supply_date)
            cliq_ccee_processment = (
                ccee_result[0].get("id_cliq_ccee_processment") if ccee_result else None
            )
            if cliq_ccee_processment:
                try:
                    cliq_ccee_processment = CliqCceeProcessment.objects.get(
                        pk=int(cliq_ccee_processment)
                    )
                except CliqCceeProcessment.ObjectDoesNotExist:
                    cliq_ccee_processment = None

            contract_dispatch_cliq_contract.append(
                ContractDispatchCliqContract(
                    cliq_contract=cliq_contract,
                    contract_dispatch=contract_dispatch,
                    contract_status_on_dispatch=current_status,
                    volume_on_dispatch=contract.get("volume"),
                    cliq_ccee_processment=cliq_ccee_processment,
                )
            )
            # Everytime a contract is sent its status become Waiting CCEE
            if (
                current_status == CliqContractStatus.NOT_SENT
                or current_status == CliqContractStatus.CANCELED
                or current_status == CliqContractStatus.REGISTERED_NOT_VALIDATED
            ):
                start_supply = cliq_contract.id_contract.start_supply
                end_supply = cliq_contract.id_contract.end_supply

                for year, month in self.month_year_iter(
                    start_supply.month,
                    start_supply.year,
                    end_supply.month + 1,
                    end_supply.year,
                ):
                    month = f"0{month}" if month < 10 else f"{month}"
                    supply_date_ns = datetime.strptime(
                        f"{month}/{year}", "%m/%Y"
                    ).date()
                    CliqContractCurrentStatus.objects.update_or_create(
                        cliq_contract=cliq_contract,
                        status_date=supply_date_ns,
                        defaults={
                            "status": CliqContractStatus.WAITING_CCEE,
                            "status_date": supply_date_ns,
                        },
                    )
            else:
                supply_date_datetime = datetime.strptime(supply_date, "%Y-%m")
                CliqContractCurrentStatus.objects.update_or_create(
                    cliq_contract=cliq_contract,
                    status_date=supply_date_datetime.date(),
                    defaults={
                        "status": CliqContractStatus.WAITING_CCEE,
                        "status_date": supply_date_datetime.date(),
                    },
                )
        ContractDispatchCliqContract.objects.bulk_create(
            contract_dispatch_cliq_contract
        )
        return contract_dispatch


class CliqContractCCEEPeriodInfoCreateSerializer(serializers.ModelSerializer):
    month = serializers.DateField(source="date", input_formats=["%m/%Y"])
    amount = serializers.CharField(source="volume")

    class Meta:
        model = CliqContractCCEEPeriodInfo
        fields = ("amount", "month")


class CliqContractCCEEPeriodInfoReadSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()

    class Meta:
        model = CliqContractCCEEPeriodInfo
        fields = ("volume", "date")
        read_only_fields = fields

    def get_date(self, obj):
        return obj.date.strftime("%m/%Y")


class SubmarketCCEEStateSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("id_submarket", "description", "status")
        model = Submarket


class CliqContractCCEEStateReadSerializer(serializers.ModelSerializer):
    period_info = CliqContractCCEEPeriodInfoReadSerializer(
        many=True, source="cliqcontractcceeperiodinfo_set"
    )
    buyer_agent = AgentsCCEEStateSerializer()
    seller_agent = AgentsCCEEStateSerializer()
    id_submarket = SubmarketCCEEStateSerializer(source="submarket")

    class Meta:
        model = CliqContractCCEEState
        fields = (
            "id_contract_cliq",
            "id_submarket",
            "buyer_agent",
            "seller_agent",
            "period_info",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class CliqContractCCEEStateCreateSerializer(serializers.ModelSerializer):
    volume_info = CliqContractCCEEPeriodInfoCreateSerializer(many=True)
    buyer = serializers.SlugRelatedField(
        source="buyer_agent",
        slug_field="profile_agent__id_ccee__code_ccee",
        queryset=Agents.objects.filter(id_ccee__type="A/P"),
    )
    seller = serializers.SlugRelatedField(
        source="seller_agent",
        slug_field="profile_agent__id_ccee__code_ccee",
        queryset=Agents.objects.filter(id_ccee__type="A/P"),
    )
    submarket = serializers.SlugRelatedField(
        slug_field="id_ccee__code_ccee",
        queryset=Submarket.objects.filter(id_ccee__type="SUBMARKET"),
    )

    class Meta:
        model = CliqContractCCEEState
        fields = (
            "id_contract_cliq",
            "buyer",
            "seller",
            "submarket",
            "volume_info",
        )

    def create(self, validated_data):
        volume_info_list = validated_data.pop("volume_info")

        (
            cliq_contract_ccee_state,
            created,
        ) = CliqContractCCEEState.objects.update_or_create(
            defaults=validated_data,
            id_contract_cliq=validated_data.pop("id_contract_cliq"),
        )

        for volume_data in volume_info_list:
            CliqContractCCEEPeriodInfo.objects.update_or_create(
                cliq_contract_ccee_state=cliq_contract_ccee_state,
                date=volume_data.pop("date"),
                defaults={**volume_data},
            )

        return cliq_contract_ccee_state


class CliqContractContractDispatchViewSerializer(CliqContractListSerializer):
    lastContractVersion = serializers.SerializerMethodField()
    available = serializers.BooleanField(default=None)
    ccee_processment = serializers.SerializerMethodField()
    ccee_state = serializers.SerializerMethodField()
    id_submarket = SubmarketCCEEStateSerializer()

    class Meta:
        model = CliqContract
        fields = CliqContractListSerializer.Meta.fields + [
            "id_submarket",
            "lastContractVersion",
            "available",
            "ccee_processment",
            "ccee_state",
        ]

    def get_ccee_state(self, obj):
        ccee_state = (
            CliqContractCCEEState.objects.filter(id_contract_cliq=obj.pk)
            .order_by("-created_at")
            .first()
        )
        if ccee_state:
            return CliqContractCCEEStateReadSerializer(ccee_state).data
        return None

    def get_ccee_processment(self, obj):
        try:
            contract_dispatch_cliq_contract = ContractDispatchCliqContract.objects.get(
                cliq_contract=obj.pk,
                contract_dispatch=self.context.get("contract_dispatch_pk"),
            )
            processment_serializer = ProcessmentSerializer(
                contract_dispatch_cliq_contract.cliq_ccee_processment
            )
            return processment_serializer.data
        except ObjectDoesNotExist:
            return None

    def get_lastContractVersion(self, obj):
        # retrieve history
        last_cc = ContractDispatchBusiness.retrieve_cliq_contract_last_log_by_contract(
            obj
        )
        return CliqContractListSerializer(last_cc).data if last_cc else None
