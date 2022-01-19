from django.utils import timezone as django_timezone

from datetime import datetime, timezone, timedelta
from collections import namedtuple

from django.db import transaction

from rest_framework import serializers

from company.models import Company

from .uteis.ctu_json import CTUJson
from .uteis.log_utils import LogUtils

from .models import Cct
from .models import ContractCycles
from .models import EnergyDistributor
from .models import EnergyTransmitter
from .models import RatePostException
from .models import RatedVoltage
from .models import TaxModality
from .models import TypeUsageContract
from .models import UploadFileUsageContract
from .models import UsageContract
from company.serializers import AddressSerializerData


def detach_values(validated_data, contract_type):
    # Detach nested values to create or update the database
    # Detach usage contract values
    usage_contract = validated_data.pop(contract_type)

    # Detach RatePostException model values
    rate_post_exception = validated_data.pop("rate_post_exception")

    if contract_type == "energy_distributor":
        # Detach TaxModality model values
        tax_modality = usage_contract.pop("tax_modality")

        return usage_contract, rate_post_exception, tax_modality
    else:
        # Detach CCT
        cct_data = usage_contract.pop("cct")

        # Detach ContractCycles
        contract_cycles = usage_contract.pop("contract_cycles")
        return usage_contract, rate_post_exception, cct_data, contract_cycles


class CctSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cct
        fields = [
            "id_cct",
            "cct_number",
            "length",
            "destination",
            "begin_date",
            "end_date",
            "contract_value",
        ]


class ContractCyclesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractCycles
        fields = [
            "id_contract_cycles",
            "begin_date",
            "end_date",
            "peak_must",
            "peak_tax",
            "off_peak_must",
            "off_peak_tax",
        ]


class TaxModalitySerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxModality
        fields = [
            "id_tax_modality",
            "begin_date",
            "end_date",
            "peak_musd",
            "peak_tax",
            "off_peak_musd",
            "off_peak_tax",
            "unique_musd",
            "unique_tax",
        ]


class CompanySerializer(serializers.ModelSerializer):

    id_address = AddressSerializerData(many=False)

    class Meta:
        model = Company
        fields = ["id_company", "company_name", "state_number", "id_address", "status"]


class EnergyDealerSerializer(CompanySerializer):
    connection_points = serializers.SerializerMethodField()

    def get_connection_points(self, obj):
        dealerships = obj.company_dealership.all()
        connection_point_set = set()
        for item in dealerships:
            id_param = self.context["request"].query_params.get("id")
            connection_point = item.id_gauge_point.connection_point
            gauge_company_id = item.id_gauge_point.id_company.id_company
            if id_param is not None:
                if (
                    connection_point is not None
                    and connection_point
                    and gauge_company_id == int(id_param)
                ):
                    connection_point_set.add(connection_point)
            else:
                if connection_point is not None and connection_point:
                    connection_point_set.add(connection_point)
        return connection_point_set

    class Meta(CompanySerializer.Meta):
        model = Company
        fields = [
            "id_company",
            "company_name",
            "state_number",
            "id_address",
            "connection_points",
        ]


class EnergyDistributorSerializer(serializers.ModelSerializer):

    audit_renovation = serializers.ChoiceField(
        default="N", required=False, choices=["S", "N"]
    )
    hourly_tax_modality = serializers.ChoiceField(choices=["Azul", "Verde"])
    tax_modality = TaxModalitySerializer(many=True)

    def validate(self, attrs):
        modality = attrs["hourly_tax_modality"]
        tax_modalities = attrs["tax_modality"]
        if modality == "Verde":
            for tax_modality in tax_modalities:
                try:
                    (tax_modality["unique_musd"], tax_modality["unique_tax"])
                except Exception:
                    raise serializers.ValidationError(
                        "Required fields unique_musd or unique_tax not found"
                    )
                tax_modality["peak_musd"] = None
                tax_modality["peak_tax"] = None
                tax_modality["off_peak_musd"] = None
                tax_modality["off_peak_tax"] = None
        else:
            for tax_modality in tax_modalities:
                try:
                    (
                        tax_modality["peak_musd"],
                        tax_modality["peak_tax"],
                        tax_modality["off_peak_musd"],
                        tax_modality["off_peak_tax"],
                    )
                except Exception:
                    raise serializers.ValidationError(
                        "Required fields peak_musd, peak_tax, off_peak_musd or off_peak_tax not found"
                    )
                tax_modality["unique_musd"] = None
                tax_modality["unique_tax"] = None
        return attrs

    class Meta:
        model = EnergyDistributor
        fields = [
            "pn",
            "installation",
            "renovation_period",
            "audit_renovation",
            "aneel_resolution",
            "aneel_publication",
            "tax_modality",
            "hourly_tax_modality",
        ]


class EnergyTransmitterSerializer(serializers.ModelSerializer):
    cct = CctSerializer(many=True)
    contract_cycles = ContractCyclesSerializer(many=True)
    audit_renovation = serializers.ChoiceField(
        default="N", required=False, choices=["S", "N"]
    )

    class Meta:
        model = EnergyTransmitter
        fields = [
            "ons_code",
            "aneel_resolution",
            "aneel_publication",
            "cct",
            "contract_cycles",
            "renovation_period",
            "audit_renovation",
        ]


class RatedVoltageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RatedVoltage
        fields = ["id_rated_voltage", "voltages", "group", "subgroup"]


class RatePostExceptionSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        # Verify if date and time span are correctly inserted
        if attrs["begin_date"] is not None and attrs["end_date"] is not None:
            if attrs["begin_date"] >= attrs["end_date"]:
                raise serializers.ValidationError(
                    "End date must occurs after start date"
                )

        if (
            attrs["begin_hour_clock"] is not None
            and attrs["end_hour_clock"] is not None
        ):
            if attrs["begin_hour_clock"] >= attrs["end_hour_clock"]:
                raise serializers.ValidationError(
                    "End hour clock must occurs after begin hour clock"
                )

        return attrs

    class Meta:
        model = RatePostException
        fields = [
            "id_rate_post_exception",
            "begin_hour_clock",
            "end_hour_clock",
            "begin_date",
            "end_date",
        ]


class TypeUsageContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeUsageContract
        fields = ["id_usage_contract_type", "description"]


class UsageContractSimpleSerializer(serializers.ModelSerializer):

    status = serializers.ChoiceField(default="S", required=False, choices=["S", "N"])
    companys = CompanySerializer(many=False, read_only=False, source="company")
    energy_dealers = CompanySerializer(
        many=False, read_only=False, source="energy_dealer"
    )
    rated_voltage = RatedVoltageSerializer(many=False, read_only=True)
    usage_contract_type = TypeUsageContractSerializer(many=False)
    create_date = serializers.DateTimeField(default=datetime.now(tz=timezone.utc))

    class Meta:
        model = UsageContract
        fields = [
            "id_usage_contract",
            "usage_contract_type",
            "companys",
            "energy_dealers",
            "contract_number",
            "rated_voltage",
            "bought_voltage",
            "tolerance_range",
            "power_factor",
            "peak_begin_time",
            "peak_end_time",
            "contract_value",
            "start_date",
            "end_date",
            "create_date",
            "status",
            "connection_point",
        ]


class UploadFileUsageContractSerializer(serializers.ModelSerializer):
    id_usage_contract = serializers.PrimaryKeyRelatedField(
        queryset=UsageContract.objects.all(), allow_null=True
    )

    @transaction.atomic
    def create(self, validated_data):
        _username = self.context.get("username")
        _log = LogUtils(_username)

        _uploadFileUsageContract = UploadFileUsageContract.objects.create(
            **validated_data
        )

        _uploadFile_dict = validated_data.copy()
        if _uploadFile_dict.get("file_path") is not None:
            _uploadFile_dict["file_path"] = (
                "usage_contracts/" + _uploadFile_dict.get("file_path").name
            )

        _uploadFile_dict["id_usage_contract"] = _uploadFile_dict[
            "id_usage_contract"
        ].__str__()

        _log.save_log(
            _uploadFileUsageContract.id_upload_file_usage_contract,
            UploadFileUsageContract._meta.db_table,
            _uploadFile_dict,
            django_timezone.now(),
        )

        return _uploadFileUsageContract

    class Meta:
        model = UploadFileUsageContract
        fields = [
            "id_upload_file_usage_contract",
            "file_name",
            "file_path",
            "file_version",
            "observation",
            "date_upload",
            "id_usage_contract",
        ]


class UsageContractCompleteSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(default="S", required=False, choices=["S", "N"])
    upload_file = UploadFileUsageContractSerializer(many=True, required=False)
    companys = CompanySerializer(many=False, read_only=False, source="company")
    energy_dealers = CompanySerializer(
        many=False, read_only=False, source="energy_dealer"
    )
    rated_voltage = RatedVoltageSerializer(many=False)
    usage_contract_type = TypeUsageContractSerializer(many=False)
    energy_distributor = EnergyDistributorSerializer(many=False)
    energy_transmitter = EnergyTransmitterSerializer(many=False)
    rate_post_exception = RatePostExceptionSerializer(many=True)

    create_date = serializers.DateTimeField(default=datetime.now(tz=timezone.utc))

    class Meta:
        model = UsageContract
        fields = [
            "id_usage_contract",
            "usage_contract_type",
            "companys",
            "energy_dealers",
            "contract_number",
            "rated_voltage",
            "bought_voltage",
            "tolerance_range",
            "power_factor",
            "peak_begin_time",
            "peak_end_time",
            "contract_value",
            "rate_post_exception",
            "energy_distributor",
            "energy_transmitter",
            "start_date",
            "end_date",
            "observation",
            "create_date",
            "status",
            "upload_file",
            "connection_point",
        ]

def assign_uploaded_files(context, ctu, _list_uf):
    # Assign uploaded files
    if context["upload_file_usage_contract_ids"]:
        files = UploadFileUsageContract.objects.filter(
            id_upload_file_usage_contract__in=context[
                "upload_file_usage_contract_ids"
            ]
        )
        serializer = UploadFileUsageContractSerializer(files, many=True)
        _list_uf = serializer.data
        ctu.upload_file.set(files)
        ctu.save()

def save_rate_post_exception_values(rate_post_exception_data, ctu, create_time, _ctu_json, _list_rpe, _log):
    index = 0
    # Save RatePostException values
    for data in rate_post_exception_data:

        rpe = RatePostException()

        if "begin_date" in data:
            rpe.begin_date = data["begin_date"]
        if "end_date" in data:
            rpe.end_date = data["end_date"]
        if "begin_hour_clock" in data:
            rpe.begin_hour_clock = data["begin_hour_clock"]
        if "end_hour_clock" in data:
            rpe.end_hour_clock = data["end_hour_clock"]
        rpe.id_usage_contract = ctu

        # Save RatePostException
        rpe.save()
        ctu.rate_post_exception.add(rpe)

        # Save log create RatePostException
        aux_time = create_time - timedelta(seconds=index)
        _ctu_json.set_model_object("RATE_POST_EXCEPTION", rpe)
        _json_rpe = _ctu_json.get_json_rate_post_exception()
        _list_rpe.append(_json_rpe)
        _log.save_log(
            rpe.id_rate_post_exception,
            _ctu_json.get_table_model(),
            _json_rpe,
            aux_time,
        )
        index = index + 1

class UsageContractDistributorSerializer(serializers.ModelSerializer):

    company = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.filter(
            gauge_company__gauge_type="Fronteira"
        ).distinct()
    )
    energy_dealer = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.filter(
            company_dealership__id_gauge_point__id_company__isnull=False
        ).distinct()
    )
    status = serializers.ChoiceField(default="S", required=False, choices=["S", "N"])
    upload_file = UploadFileUsageContractSerializer(many=True, required=False)
    energy_distributor = EnergyDistributorSerializer(many=False)
    rate_post_exception = RatePostExceptionSerializer(many=True, required=False)

    def validate(self, attrs):
        # Verify if date and time span are correctly inserted
        if attrs["start_date"] is not None and attrs["end_date"] is not None:
            if attrs["start_date"] >= attrs["end_date"]:
                raise serializers.ValidationError(
                    "End date must occurs after start date"
                )

        if attrs["peak_begin_time"] is not None and attrs["peak_end_time"] is not None:
            if attrs["peak_begin_time"] >= attrs["peak_end_time"]:
                raise serializers.ValidationError(
                    "Peak end time must occurs after Peak begin time"
                )

        return attrs

    def assign_usage_contract_and_save_energy_distributor(self, ctu, energy_distributor_data):
        # Assign Usage_contract and save EnergyDistributor
        energy_distributor_data["id_usage_contract"] = ctu
        energy_distributor = EnergyDistributor.objects.create(**energy_distributor_data)
        return energy_distributor

    def save_tax_modality_values(self, tax_modality_data, energy_distributor, create_time, _ctu_json, _list_tax, _log):
        index = 0

        # Save TaxModality values
        for data in tax_modality_data:
            tm = TaxModality()

            if "begin_date" in data:
                tm.begin_date = data["begin_date"]
            if "end_date" in data:
                tm.end_date = data["end_date"]
            if "unique_musd" in data:
                tm.unique_musd = data["unique_musd"]
            if "unique_tax" in data:
                tm.unique_tax = data["unique_tax"]
            if "peak_musd" in data:
                tm.peak_musd = data["peak_musd"]
            if "peak_tax" in data:
                tm.peak_tax = data["peak_tax"]
            if "off_peak_musd" in data:
                tm.off_peak_musd = data["off_peak_musd"]
            if "off_peak_tax" in data:
                tm.off_peak_tax = data["off_peak_tax"]

            tm.id_usage_contract = energy_distributor

            # Save TaxModality
            tm.save()
            energy_distributor.tax_modality.add(tm)

            # Save log create TaxModality
            aux_time = create_time - timedelta(seconds=index)
            _ctu_json.set_model_object("TAX_MODALITY", tm)
            _json_tm = _ctu_json.get_json_tax_modality()
            _list_tax.append(_json_tm)
            _log.save_log(
                tm.id_tax_modality, _ctu_json.get_table_model(), _json_tm, aux_time
            )
            index = index + 1


    def save_log_create_energy_distributor(self, energy_distributor, ctu, _ctu_json, _log, create_time):
        # Save log create EnergyDistributor
        _ctu_json.set_model_object("ENERGY_DISTRIBUTOR", energy_distributor)
        _json_ed = _ctu_json.get_json_energy_distributor()
        _json_et = "{}"
        _log.save_log(
            ctu.id_usage_contract, _ctu_json.get_table_model(), _json_ed, create_time
        )
        return _json_et, _json_ed

    def save_log_create_usage_contract(self, _ctu_json, ctu, _json_ed, _json_et, _list_rpe, _list_tax, _list_cc, _list_cct, _list_uf, _log, create_time):
        # Save log create Usage Contract
        _ctu_json.set_model_object("USAGE_CONTRACT", ctu)

        _company = ctu.company
        _energy_dealer = ctu.energy_dealer
        _rated_voltage = ctu.rated_voltage

        _json_ctu = _ctu_json.get_json_usage_contract(
            1,
            _company,
            _energy_dealer,
            _rated_voltage,
            _json_ed,
            _json_et,
            _list_rpe,
            _list_tax,
            _list_cc,
            _list_cct,
            _list_uf,
        )
        _log.save_log(
            ctu.id_usage_contract, _ctu_json.get_table_model(), _json_ctu, create_time
        )

    @transaction.atomic
    def create(self, validated_data):
        create_time = datetime.now()
        context = self.context
        _log = LogUtils(context["username"])

        _list_tax = []
        _list_rpe = []
        _list_cc = []
        _list_cct = []
        _list_uf = []

        energy_distributor_data = validated_data.pop("energy_distributor")
        rate_post_exception_data = validated_data.pop("rate_post_exception")
        tax_modality_data = energy_distributor_data.pop("tax_modality")

        ctu = UsageContract.objects.create(**validated_data)
        _ctu_json = CTUJson(ctu.id_usage_contract, context["username"])

        assign_uploaded_files(context, ctu, _list_uf)

        energy_distributor = self.assign_usage_contract_and_save_energy_distributor(ctu, energy_distributor_data)
        self.save_tax_modality_values(tax_modality_data, energy_distributor, create_time, _ctu_json, _list_tax, _log)

        save_rate_post_exception_values(rate_post_exception_data, ctu, create_time, _ctu_json, _list_rpe, _log)

        # Save new Usage Contract
        ctu.save()
        _json_et, _json_ed = self.save_log_create_energy_distributor(energy_distributor, ctu, _ctu_json, _log, create_time)

        self.save_log_create_usage_contract(_ctu_json, ctu, _json_ed, _json_et, _list_rpe, _list_tax, _list_cc, _list_cct, _list_uf, _log, create_time)

        return ctu

    @transaction.atomic
    def update(self, instance, validated_data):
        update_time = datetime.now()
        _user = self.context
        _log = LogUtils(_user["username"])
        _list_tax = []
        _list_rate = []
        _list_uf = []

        (
            energy_distributor_data,
            rate_post_exception_data,
            tax_modality_data,
        ) = detach_values(validated_data, "energy_distributor")

        # Update UsageContract values
        ctu = UsageContract.objects.filter(pk=instance.pk)
        ctu.update(**validated_data)
        _ctu_json = CTUJson(ctu[0].id_usage_contract, _user["username"])

        # Prepare to log uploaded files
        serializer = UploadFileUsageContractSerializer(ctu[0].upload_file, many=True)
        _list_uf = serializer.data

        # Update Energy Distributor
        _energy_distributor = EnergyDistributor.objects.update_or_create(
            pk=instance.pk, defaults=energy_distributor_data
        )[0]

        _company = ctu[0].company
        _energy_dealer = ctu[0].energy_dealer
        _rated = ctu[0].rated_voltage

        # Update Tax Modality
        tax_modality_ids = TaxModality.objects.filter(
            id_usage_contract=instance.pk
        ).values_list("id_tax_modality", flat=True)
        tax_modality_ids = list(map(int, tax_modality_ids))
        ids_tm_diff = len(tax_modality_data) - len(tax_modality_ids)

        # Remove old Tax Modality values
        if ids_tm_diff < 0:
            for i in range(-ids_tm_diff):
                remove_id = tax_modality_ids.pop()
                TaxModality.objects.filter(pk=remove_id).delete()

        # Add new Tax Modality values
        elif ids_tm_diff > 0:

            index = 0
            for i in range(ids_tm_diff):
                data = tax_modality_data.pop()
                tm = TaxModality()

                if "begin_date" in data:
                    tm.begin_date = data["begin_date"]
                if "end_date" in data:
                    tm.end_date = data["end_date"]
                if "unique_musd" in data:
                    tm.unique_musd = data["unique_musd"]
                if "unique_tax" in data:
                    tm.unique_tax = data["unique_tax"]
                if "peak_musd" in data:
                    tm.peak_musd = data["peak_musd"]
                if "peak_tax" in data:
                    tm.peak_tax = data["peak_tax"]
                if "off_peak_musd" in data:
                    tm.off_peak_musd = data["off_peak_musd"]
                if "off_peak_tax" in data:
                    tm.off_peak_tax = data["off_peak_tax"]

                tm.id_usage_contract = _energy_distributor
                tm.save()
                _energy_distributor.tax_modality.add(tm)

                # Save log create TaxModality
                aux_time = update_time - timedelta(seconds=index)
                _ctu_json.set_model_object("TAX_MODALITY", tm)
                _json_tm = _ctu_json.get_json_tax_modality()
                _log.save_log(
                    tm.id_tax_modality, _ctu_json.get_table_model(), _json_tm, aux_time
                )
                _list_tax.append(_json_tm)
                index = index + 1

        index = 0
        # Update Tax Modality values
        for tax_modality_id, data in zip(tax_modality_ids, tax_modality_data):
            tm = TaxModality.objects.filter(pk=tax_modality_id)
            tm.update(**data)

            # Save log update TaxModality
            aux_time = update_time - timedelta(seconds=index)
            _ctu_json.set_model_object("TAX_MODALITY", tm[0])
            _new = _ctu_json.get_json_tax_modality()
            _list_tax.append(_new)
            updated = _log.update_log(
                tm[0].id_tax_modality, _ctu_json.get_table_model(), _new, aux_time
            )
            if updated:
                index = index + 1

        # Update Rate Post Exception
        rate_post_ids = RatePostException.objects.filter(
            id_usage_contract=instance.pk
        ).values_list("id_rate_post_exception", flat=True)
        rate_post_ids = list(map(int, rate_post_ids))
        ids_rr_diff = len(rate_post_exception_data) - len(rate_post_ids)

        # Remove old  Rate Post Exception
        if ids_rr_diff < 0:
            for i in range(-ids_rr_diff):
                remove_id = rate_post_ids.pop()
                RatePostException.objects.filter(pk=remove_id).delete()

        # Add new Rate Post Exception
        elif ids_rr_diff > 0:

            index = 0
            for i in range(ids_rr_diff):

                data = rate_post_exception_data.pop()
                rpe = RatePostException()

                if "begin_date" in data:
                    rpe.begin_date = data["begin_date"]
                if "end_date" in data:
                    rpe.end_date = data["end_date"]
                if "begin_hour_clock" in data:
                    rpe.begin_hour_clock = data["begin_hour_clock"]
                if "end_hour_clock" in data:
                    rpe.end_hour_clock = data["end_hour_clock"]

                rpe.id_usage_contract = ctu[0]

                # Save RatePostException
                rpe.save()
                ctu[0].rate_post_exception.add(rpe)

                # Save log create RatePostException
                aux_time = update_time - timedelta(seconds=index)
                _ctu_json.set_model_object("RATE_POST_EXCEPTION", rpe)
                _json_rpe = _ctu_json.get_json_rate_post_exception()
                _log.save_log(
                    rpe.id_rate_post_exception,
                    _ctu_json.get_table_model(),
                    _json_rpe,
                    aux_time,
                )
                _list_rate.append(_json_rpe)
                index = index + 1

        index = 0
        # Update Rate Post Exception
        for rate_post_id, data in zip(rate_post_ids, rate_post_exception_data):
            rpe = RatePostException.objects.filter(pk=rate_post_id)
            rpe.update(**data)

            # Save log update Rate Post Exception
            aux_time = update_time - timedelta(seconds=index)
            _ctu_json.set_model_object("RATE_POST_EXCEPTION", rpe[0])
            _new = _ctu_json.get_json_rate_post_exception()
            _list_rate.append(_new)
            updated = _log.update_log(
                rpe[0].id_rate_post_exception,
                _ctu_json.get_table_model(),
                _new,
                aux_time,
            )
            if updated:
                index = index + 1

        # Save log update EnergyDistributor
        _ctu_json.set_model_object("ENERGY_DISTRIBUTOR", _energy_distributor)
        _new_energy_distributor = _ctu_json.get_json_energy_distributor()
        _log.update_log(
            _energy_distributor.id_usage_contract_id,
            _ctu_json.get_table_model(),
            _new_energy_distributor,
            update_time,
        )

        # Save log update Usage Contract
        _company = ctu[0].company
        _json_ed = _ctu_json.get_json_energy_distributor()

        _ctu_json.set_model_object("USAGE_CONTRACT", ctu[0])
        _new = _ctu_json.get_json_usage_contract(
            1,
            _company,
            _energy_dealer,
            _rated,
            _json_ed,
            "{}",
            _list_rate,
            _list_tax,
            [],
            [],
            _list_uf,
        )
        _log.update_log(
            ctu[0].id_usage_contract, _ctu_json.get_table_model(), _new, update_time
        )

        return instance

    class Meta:
        model = UsageContract
        fields = [
            "id_usage_contract",
            "usage_contract_type",
            "company",
            "energy_dealer",
            "contract_number",
            "rated_voltage",
            "bought_voltage",
            "tolerance_range",
            "power_factor",
            "peak_begin_time",
            "peak_end_time",
            "contract_value",
            "rate_post_exception",
            "energy_distributor",
            "start_date",
            "end_date",
            "observation",
            "create_date",
            "status",
            "upload_file",
            "connection_point",
        ]


class UsageContractTransmitterSerializer(serializers.ModelSerializer):

    company = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.filter(
            gauge_company__gauge_type="Fronteira"
        ).distinct()
    )
    energy_dealer = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.filter(
            company_dealership__id_gauge_point__id_company__isnull=False
        ).distinct()
    )
    status = serializers.ChoiceField(default="S", required=False, choices=["S", "N"])
    upload_file = UploadFileUsageContractSerializer(many=True, required=False)
    energy_transmitter = EnergyTransmitterSerializer(many=False)
    rate_post_exception = RatePostExceptionSerializer(many=True, required=False)

    class Meta:
        model = UsageContract
        fields = [
            "id_usage_contract",
            "usage_contract_type",
            "company",
            "energy_dealer",
            "contract_number",
            "rated_voltage",
            "bought_voltage",
            "tolerance_range",
            "power_factor",
            "peak_begin_time",
            "peak_end_time",
            "contract_value",
            "rate_post_exception",
            "energy_transmitter",
            "start_date",
            "end_date",
            "observation",
            "create_date",
            "status",
            "upload_file",
            "connection_point",
        ]

    def validate(self, attrs):

        # Verify if date and time span are correctly inserted
        if attrs["start_date"] is not None and attrs["end_date"] is not None:
            if attrs["start_date"] >= attrs["end_date"]:
                raise serializers.ValidationError(
                    "End date must occurs after start date"
                )

        if attrs["peak_begin_time"] is not None and attrs["peak_end_time"] is not None:
            if attrs["peak_begin_time"] >= attrs["peak_end_time"]:
                raise serializers.ValidationError(
                    "Peak end time must occurs after Peak begin time"
                )

        return attrs

    def assign_usage_contract_and_save_energy_transmitter(self, ctu, energy_transmitter_data):
        # Assign Usage_contract and save EnergyTransmitter
        energy_transmitter_data["id_usage_contract"] = ctu
        energy_transmitter = EnergyTransmitter.objects.create(**energy_transmitter_data)
        return energy_transmitter

    def save_cct(self, cct_data, energy_transmitter, _ctu_json, _log, _list_cct, create_time):
        index = 0
        # Save CCT
        for data in cct_data:
            cct = Cct()
            if "begin_date" in data:
                cct.begin_date = data["begin_date"]
            if "end_date" in data:
                cct.end_date = data["end_date"]
            if "contract_value" in data:
                cct.contract_value = data["contract_value"]
            if "cct_number" in data:
                cct.cct_number = data["cct_number"]
            if "length" in data:
                cct.length = data["length"]
            if "destination" in data:
                cct.destination = data["destination"]

            cct.id_usage_contract = energy_transmitter
            cct.save()
            energy_transmitter.cct.add(cct)

            # Save log create CCT
            aux_time = create_time - timedelta(seconds=index)
            _ctu_json.set_model_object("CCT", cct)
            _json_cct = _ctu_json.get_json_cct()
            _log.save_log(cct.id_cct, _ctu_json.get_table_model(), _json_cct, aux_time)
            _list_cct.append(_json_cct)
            index = index + 1

    def save_contract_cycles(self, contract_cycles_data, energy_transmitter, _ctu_json, _log, _list_cc, create_time):
        index = 0
        # Save ContractCycles
        for data in contract_cycles_data:

            cc = ContractCycles()
            if "begin_date" in data:
                cc.begin_date = data["begin_date"]
            if "end_date" in data:
                cc.end_date = data["end_date"]
            if "peak_must" in data:
                cc.peak_must = data["peak_must"]
            if "off_peak_must" in data:
                cc.off_peak_must = data["off_peak_must"]
            if "peak_tax" in data:
                cc.peak_tax = data["peak_tax"]
            if "off_peak_tax" in data:
                cc.off_peak_tax = data["off_peak_tax"]

            cc.id_usage_contract = energy_transmitter
            cc.save()
            energy_transmitter.contract_cycles.add(cc)

            # Save log create CC
            aux_time = create_time - timedelta(seconds=index)
            _ctu_json.set_model_object("CONTRACT_CYCLES", cc)
            _json_cc = _ctu_json.get_json_contract_cycles()
            _log.save_log(
                cc.id_contract_cycles, _ctu_json.get_table_model(), _json_cc, aux_time
            )
            _list_cc.append(_json_cc)
            index = index + 1



    @transaction.atomic
    def create(self, validated_data):

        context = self.context
        _log = LogUtils(context["username"])
        create_time = datetime.now()

        _list_cc = []
        _list_cct = []
        _list_rate = []
        _list_uf = []

        (
            energy_transmitter_data,
            rate_post_exception_data,
            cct_data,
            contract_cycles_data,
        ) = detach_values(validated_data, "energy_transmitter")

        # Save UsageContract values
        ctu = UsageContract.objects.create(**validated_data)
        _ctu_json = CTUJson(ctu.id_usage_contract, context["username"])

        assign_uploaded_files(context, ctu, _list_uf)

        energy_transmitter = self.assign_usage_contract_and_save_energy_transmitter(ctu, energy_transmitter_data)

        self.save_cct(cct_data, energy_transmitter, _ctu_json, _log, _list_cct, create_time)

        self.save_contract_cycles(contract_cycles_data, energy_transmitter, _ctu_json, _log, _list_cc, create_time)

        save_rate_post_exception_values(rate_post_exception_data, ctu, create_time, _ctu_json, _list_rate, _log)

        # Save log create EnergyTransmitter
        _ctu_json.set_model_object("ENERGY_TRANSMITTER", energy_transmitter)
        _json_et = _ctu_json.get_json_energy_transmitter()
        _log.save_log(
            ctu.id_usage_contract, _ctu_json.get_table_model(), _json_et, create_time
        )

        # Save log create Usage Contract
        _ctu_json.set_model_object("USAGE_CONTRACT", ctu)

        _company = ctu.company
        _energy_dealer = ctu.energy_dealer
        _rated = ctu.rated_voltage

        _json_ctu = _ctu_json.get_json_usage_contract(
            2,
            _company,
            _energy_dealer,
            _rated,
            "{}",
            _json_et,
            _list_rate,
            [],
            _list_cc,
            _list_cct,
            _list_uf,
        )
        _log.save_log(
            ctu.id_usage_contract, _ctu_json.get_table_model(), _json_ctu, create_time
        )
        return ctu

    @transaction.atomic
    def update(self, instance, validated_data):

        _user = self.context
        _log = LogUtils(_user["username"])

        update_time = datetime.now()

        _list_tax = []
        _list_rate = []
        _list_cc = []
        _list_cct = []

        (
            energy_transmitter_data,
            rate_post_exception_data,
            cct_data,
            contract_cycles_data,
        ) = detach_values(validated_data, "energy_transmitter")

        # Update UsageContract values
        ctu = UsageContract.objects.filter(pk=instance.pk)
        ctu.update(**validated_data)
        _ctu_json = CTUJson(ctu[0].id_usage_contract, _user["username"])

        # Prepare to log uploaded files
        serializer = UploadFileUsageContractSerializer(ctu[0].upload_file, many=True)
        _list_uf = serializer.data

        # Update EnergyTransmitter
        energy_transmitter = EnergyTransmitter.objects.update_or_create(
            pk=instance.pk, defaults=energy_transmitter_data
        )[0]

        _company = ctu[0].company
        _energy_dealer = ctu[0].energy_dealer
        _rated = ctu[0].rated_voltage

        # Update CCT
        cct_ids = Cct.objects.filter(id_usage_contract=instance.pk).values_list(
            "id_cct", flat=True
        )
        cct_ids = list(map(int, cct_ids))
        ids_cct_diff = len(cct_data) - len(cct_ids)

        # Remove old CCT values
        if ids_cct_diff < 0:
            for _ in range(-ids_cct_diff):
                remove_id = cct_ids.pop()
                Cct.objects.filter(pk=remove_id).delete()

        # Add new CCT values
        elif ids_cct_diff > 0:
            index = 0

            for _ in range(ids_cct_diff):

                data = cct_data.pop()
                cct = Cct()
                if "begin_date" in data:
                    cct.begin_date = data["begin_date"]
                if "end_date" in data:
                    cct.end_date = data["end_date"]
                if "contract_value" in data:
                    cct.contract_value = data["contract_value"]
                if "cct_number" in data:
                    cct.cct_number = data["cct_number"]
                if "length" in data:
                    cct.length = data["length"]
                if "destination" in data:
                    cct.destination = data["destination"]

                cct.id_usage_contract = energy_transmitter
                cct.save()
                energy_transmitter.cct.add(cct)

                # Save log create CCT
                aux_time = update_time - timedelta(seconds=index)
                _ctu_json.set_model_object("CCT", cct)
                _json_cct = _ctu_json.get_json_cct()
                _list_cct.append(_json_cct)
                _log.save_log(
                    cct.id_cct, _ctu_json.get_table_model(), _json_cct, aux_time
                )
                index = index + 1

        index = 0

        # Update CCT values
        for cct_id, data in zip(cct_ids, cct_data):
            cct = Cct.objects.filter(pk=cct_id)
            cct.update(**data)

            # Save log update CCT
            aux_time = update_time - timedelta(seconds=index)
            _ctu_json.set_model_object("CCT", cct[0])
            _new_cct = _ctu_json.get_json_cct()
            _list_cct.append(_new_cct)
            updated = _log.update_log(
                cct[0].id_cct, _ctu_json.get_table_model(), _new_cct, aux_time
            )
            if updated:
                index = index + 1

        # Update ContractCycles
        contract_cycle_ids = ContractCycles.objects.filter(
            id_usage_contract=instance.pk
        ).values_list("id_contract_cycles", flat=True)
        contract_cycle_ids = list(map(int, contract_cycle_ids))
        ids_cc_diff = len(contract_cycles_data) - len(contract_cycle_ids)

        # Remove old Contract Cycles
        if ids_cc_diff < 0:
            for _ in range(-ids_cc_diff):
                remove_id = contract_cycle_ids.pop()
                ContractCycles.objects.filter(pk=remove_id).delete()

        # Add new Contract Cycles values
        elif ids_cc_diff > 0:
            index = 0
            for _ in range(ids_cc_diff):

                data = contract_cycles_data.pop()
                cc = ContractCycles()
                if "begin_date" in data:
                    cc.begin_date = data["begin_date"]
                if "end_date" in data:
                    cc.end_date = data["end_date"]
                if "peak_must" in data:
                    cc.peak_must = data["peak_must"]
                if "off_peak_must" in data:
                    cc.off_peak_must = data["off_peak_must"]
                if "peak_tax" in data:
                    cc.peak_tax = data["peak_tax"]
                if "off_peak_tax" in data:
                    cc.off_peak_tax = data["off_peak_tax"]

                cc.id_usage_contract = energy_transmitter
                cc.save()

                energy_transmitter.contract_cycles.add(cc)

                # Save log create CC
                aux_time = update_time - timedelta(seconds=index)
                _ctu_json.set_model_object("CONTRACT_CYCLES", cc)
                _json_cc = _ctu_json.get_json_contract_cycles()
                _list_cc.append(_json_cc)
                _log.save_log(
                    cc.id_contract_cycles,
                    _ctu_json.get_table_model(),
                    _json_cc,
                    aux_time,
                )
                index = index + 1

        # Update Contract Cycles values
        index = 0
        for contract_cycle_id, data in zip(contract_cycle_ids, contract_cycles_data):
            cc = ContractCycles.objects.filter(pk=contract_cycle_id)
            cc.update(**data)

            # Save log update CC
            aux_time = update_time - timedelta(seconds=index)
            _ctu_json.set_model_object("CONTRACT_CYCLES", cc[0])
            _new_cc = _ctu_json.get_json_contract_cycles()
            _list_cc.append(_new_cc)
            updated = _log.update_log(
                cc[0].id_contract_cycles, _ctu_json.get_table_model(), _new_cc, aux_time
            )
            if updated:
                index = index + 1

        # Save RatePostException values
        # Update Rate Post Exception
        rate_post_ids = RatePostException.objects.filter(
            id_usage_contract=instance.pk
        ).values_list("id_rate_post_exception", flat=True)
        rate_post_ids = list(map(int, rate_post_ids))
        ids_rr_diff = len(rate_post_exception_data) - len(rate_post_ids)

        # Remove old  Rate Post Exception
        if ids_rr_diff < 0:
            for _ in range(-ids_rr_diff):
                remove_id = rate_post_ids.pop()
                RatePostException.objects.filter(pk=remove_id).delete()

        # Add new Rate Post Exception
        elif ids_rr_diff > 0:
            index = 0
            for _ in range(ids_rr_diff):

                data = rate_post_exception_data.pop()
                rpe = RatePostException()

                if "begin_date" in data:
                    rpe.begin_date = data["begin_date"]
                if "end_date" in data:
                    rpe.end_date = data["end_date"]
                if "begin_hour_clock" in data:
                    rpe.begin_hour_clock = data["begin_hour_clock"]
                if "end_hour_clock" in data:
                    rpe.end_hour_clock = data["end_hour_clock"]

                rpe.id_usage_contract = ctu[0]
                rpe.save()
                ctu[0].rate_post_exception.add(rpe)

                # Save log create RatePostException
                aux_time = update_time - timedelta(seconds=index)
                _ctu_json.set_model_object("RATE_POST_EXCEPTION", rpe)
                _json_rpe = _ctu_json.get_json_rate_post_exception()
                _list_rate.append(_json_rpe)
                _log.save_log(
                    rpe.id_rate_post_exception,
                    _ctu_json.get_table_model(),
                    _json_rpe,
                    aux_time,
                )

                index = index + 1

        index = 0
        # Update Rate Post Exception
        for rate_post_id, data in zip(rate_post_ids, rate_post_exception_data):
            rpe = RatePostException.objects.filter(pk=rate_post_id)
            rpe.update(**data)

            # Save log update Rate Post Exception
            aux_time = update_time - timedelta(seconds=index)
            _ctu_json.set_model_object("RATE_POST_EXCEPTION", rpe[0])
            _new = _ctu_json.get_json_rate_post_exception()
            _list_rate.append(_new)
            updated = _log.update_log(
                rpe[0].id_rate_post_exception,
                _ctu_json.get_table_model(),
                _new,
                aux_time,
            )
            if updated:
                index = index + 1

        # Save log update Energy Trasmitter
        _ctu_json.set_model_object("ENERGY_TRANSMITTER", energy_transmitter)
        _new_et = _ctu_json.get_json_energy_transmitter()
        _log.update_log(
            ctu[0].id_usage_contract, _ctu_json.get_table_model(), _new_et, update_time
        )

        # Save log update Usage Contract
        _company = ctu[0].company

        _ctu_json.set_model_object("USAGE_CONTRACT", ctu[0])
        _new = _ctu_json.get_json_usage_contract(
            2,
            _company,
            _energy_dealer,
            _rated,
            "{}",
            _new_et,
            _list_rate,
            _list_tax,
            _list_cc,
            _list_cct,
            _list_uf,
        )
        _log.update_log(
            ctu[0].id_usage_contract, _ctu_json.get_table_model(), _new, update_time
        )

        return instance
