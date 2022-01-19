from datetime import datetime

from django.utils import timezone
from rest_framework import serializers

from agents.models import Agents
from asset_items.models import AssetItems
from assets.models import Assets
from company.models import CompanyContacts, BankAccount, Address, EletricUtilityCompany, Company, City, State, AccountType
from core.serializers import log, generic_update, generic_validation_status, \
    generic_validation_changed, generic_insert_user_and_observation_in_self
from energy_composition.models import EnergyComposition
from gauge_point.models import GaugePoint, GaugeEnergyDealership
from core.views import alter_number
from locales.translates_function import translate_language_error


class CompanyContactsSerializer(serializers.ModelSerializer):
    def validate_cellphone(self, dob):
        if dob==" ":    
            return None
        return dob
    status = serializers.CharField(default='S', required=False)
    responsible = serializers.CharField(
        write_only=False,
        required=True
    )
    email = serializers.CharField(
        write_only=False,
        required=True
    )
    phone = serializers.CharField(
        write_only=False,
        required=True
    )

    type = serializers.CharField(
        write_only=False,
        required=True
    )

    class Meta:
        fields = ('responsible', 'email', 'phone', 'cellphone', 'status', 'type')
        model = CompanyContacts


class EletricUtilityCompanySerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('instaled_capacity', 'guaranteed_power', 'regulatory_act', 'internal_loss', 'transmission_loss')
        model = EletricUtilityCompany

class AccountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id_account_type', 'description')
        model = AccountType


class BankAccountSerializer(serializers.ModelSerializer):
    status = serializers.CharField(default='S', required=False)

    class Meta:
        fields = ('bank', 'account_type', 'account_number', 'bank_agency', 'other', 'main_account', 'status')
        model = BankAccount


def validate_status(pk, status, self):
    if status is None:
        return 'S'
    elif status == 'N':
        kwargs = {EnergyComposition: 'id_company', Agents: 'id_company', AssetItems: 'id_company',
                  GaugePoint: 'id_company', Assets: 'id_company', GaugeEnergyDealership: 'id_dealership'}
        status_message = generic_validation_status(pk, 'Company', kwargs, self)
        if status_message != 'S':
            raise serializers.ValidationError(status_message)
    return status

def validate_type(pk, type_company, self):

    if type_company != Company.objects.get(pk=pk).type:
        kwargs = {EnergyComposition: 'id_company', Agents: 'id_company', AssetItems: 'id_company',\
                  GaugePoint: 'id_company', Assets: 'id_company', GaugeEnergyDealership: 'id_dealership'}
        status_message=generic_validation_changed(pk, Company, kwargs, self.context['request'])
        if status_message != 'S':
            raise serializers.ValidationError(status_message)
    return type_company

class CompanySerializer(serializers.ModelSerializer):
    def validate_characteristics(self,dob):
        if dob is not None and dob not in ('consumidora', 'geradora'):
            raise serializers.ValidationError(translate_language_error('error_characteristics', self.context['request']) )
        return dob

    eletric_utility = EletricUtilityCompanySerializer(write_only=False, many=False, source="id_company_eletric",
                                                      read_only=False)
    bank_account = BankAccountSerializer(write_only=False, many=True, source="id_company_bank", read_only=False)
    company_contacts = CompanyContactsSerializer(write_only=False, many=True, source="id_company_contacts",
                                                 read_only=False)

    company_name = serializers.CharField(
        write_only=False,
        help_text='* Insert name company',
        required=True
    )
    legal_name = serializers.CharField(
        write_only=False,
        help_text='* Insert legal name company',
        required=True
    )
    registered_number = serializers.CharField(
        write_only=False,
        help_text='* Insert IE',
        required=False,
        allow_blank=True,
        allow_null=True
    )
    type = serializers.CharField(
        write_only=False,
        help_text='* Insert type company - Geradora/Consumidora',
        required=True
    )
    state_number = serializers.CharField(
        write_only=False,
        help_text='* Insert CNPJ of company',
        required=True
    )
    nationality = serializers.CharField(
        write_only=False,
        help_text='* Insert nationality of company',
        required=True
    )
    status = serializers.CharField(default='S', required=False)
    create_date = serializers.DateTimeField(default=datetime.now(tz=timezone.utc), required=False)

    class Meta:
        fields = (
            'url', 'id_company', 'company_name', 'legal_name', 'registered_number', 'type', 'state_number', 'nationality', 'id_sap',
            'id_address', 'characteristics', 'status', 'create_date', 'eletric_utility', 'bank_account',
            'company_contacts')
        model = Company

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(CompanySerializer, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        electric_utility_data = validated_data.pop('id_company_eletric')
        bank_data = validated_data.pop('id_company_bank')
        company_contacts_data = validated_data.pop('id_company_contacts')
        company = Company.objects.create(**validated_data)
        log(Company, company.id_company, {}, company, self.user, self.observation_log, action="INSERT")
        electric = EletricUtilityCompany.objects.create(id_company=company, **electric_utility_data)
        log(EletricUtilityCompany, electric.id_eletric_utility_company, {}, electric, self.user,
            self.observation_log, action="INSERT")
        for data_bank in bank_data:
            bank = BankAccount.objects.create(id_company=company, **data_bank)
            log(BankAccount, bank.id_bank, {}, bank, self.user,
                self.observation_log, action="INSERT")
        for data_contacts in company_contacts_data:
            contact = CompanyContacts.objects.create(id_company=company, **data_contacts)
            log(CompanyContacts, contact.id_contacts, {}, contact, self.user,
                self.observation_log, action="INSERT")
        return company

    def update(self, instance, validated_data):
        electric_utility_data = validated_data.pop('id_company_eletric')
        id_bank_data = validated_data.pop('id_company_bank')
        company_contacts_data = validated_data.pop('id_company_contacts')
        banks = list(instance.id_company_bank.all())
        contacts = list(instance.id_company_contacts.all())
        validate_status(instance.id_company, dict(validated_data)['status'], self)
        validate_type(instance.id_company, dict(validated_data)['type'], self)

        obj = generic_update(Company, instance.id_company, dict(validated_data), self.user, self.observation_log)
        try:
            electric = EletricUtilityCompany.objects.filter(id_company=instance.id_company)[0]
            generic_update(EletricUtilityCompany, electric.id_eletric_utility_company, dict(electric_utility_data),
                           self.user, self.observation_log)
        except:
            pass
        company = Company.objects.get(pk=instance.id_company)
        for data in id_bank_data:
            try:
                bank = banks.pop(0)
                generic_update(BankAccount, bank.id_bank, dict(data), self.user, self.observation_log)
            except IndexError as e:
                bank = BankAccount.objects.create(id_company=company, **data)
                log(BankAccount, bank.id_bank, {}, bank, self.user, self.observation_log,
                    action="INSERT")

        for data in company_contacts_data:
            try:
                contact = contacts.pop(0)
                generic_update(CompanyContacts, contact.id_contacts, dict(data), self.user)
            except IndexError as e:
                contact = CompanyContacts.objects.create(id_company=company, **data)
                log(CompanyContacts, contact.id_contacts, {}, contact, self.user, self.observation_log,
                    action="INSERT")
        return obj


class StateSerializer(serializers.ModelSerializer):

    class Meta:
        model = State
        fields = ('name', 'initials')


class CitySerializerData(serializers.ModelSerializer):

    id_state = StateSerializer(many=False)

    class Meta:
        model = City
        fields = ('id_state', 'city_name')


class AddressSerializerData(serializers.ModelSerializer):

    id_city = CitySerializerData(many=False, required=False)

    class Meta:
        model = Address
        fields = ('url', 'id_address', 'id_city', 'street', 'number', 'zip_code', 'complement', 'neighborhood')


class CitySerializer(serializers.ModelSerializer):

    class Meta:
        model = City
        fields = ('id_state', 'city_name')


class AddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = Address
        fields = ('url', 'id_address', 'id_city', 'street', 'number', 'zip_code', 'complement', 'neighborhood')

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(AddressSerializer, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        address = Address.objects.create(**validated_data)
        log(Address, address.id_address, {}, address, self.user, self.observation_log, action="INSERT")
        return address

    def update(self, instance, validated_data):
        obj = generic_update(Address, instance.id_address, dict(validated_data), self.user, self.observation_log)
        return obj
