from energy_composition.models import Product, Business, AccountantArea, DirectorBoard, Segment, EnergyComposition
from company.serializers import EletricUtilityCompanySerializer, BankAccountSerializer, CompanyContactsSerializer
from company.models import Country, State, City, Address, Company
from rest_framework import serializers


class CountrySerializerView(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ('id_country', 'name', 'initials')


class StateSerializerView(serializers.ModelSerializer):
    country = CountrySerializerView(source="id_country", read_only=True)

    class Meta:
        model = State
        fields = ('id_state', 'country', 'name', 'initials')


class CitySerializerVIew(serializers.ModelSerializer):
    state = StateSerializerView(source="id_state", read_only=True)

    class Meta:
        model = City
        fields = ('id_city', 'state', 'city_name', 'initials')


class CitySerializerSimpleView(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ('id_city', 'city_name', 'initials')


class AddressSerializerView(serializers.ModelSerializer):
    city = CitySerializerVIew(source="id_city", read_only=True)
    number_address=serializers.DecimalField(source="number", max_digits=9, decimal_places=0)
    class Meta:
        model = Address
        fields = ('url', 'id_address', 'street', 'number', 'number_address', 'zip_code', 'complement', 'neighborhood', 'city')


class CompanySerializerView(serializers.ModelSerializer):
    eletric_utility = EletricUtilityCompanySerializer(many=False, source="id_company_eletric", read_only=True)
    bank_account = BankAccountSerializer(many=True, source="id_company_bank", read_only=True)
    company_contacts = CompanyContactsSerializer(many=True, source="id_company_contacts", read_only=True)
    address = AddressSerializerView(source="id_address", read_only=True)

    class Meta:
        fields = ('id_company', 'url', 'company_name', 'legal_name', 'registered_number', 'type', 'state_number', 'nationality', 'id_sap',
                  'characteristics', 'status', 'create_date', 'address', 'eletric_utility', 'bank_account', 'company_contacts')
        model = Company

class CompanySerializerViewFindMany(serializers.ModelSerializer):
    address = AddressSerializerView(source="id_address", read_only=True)
    class Meta:
        fields = ('id_company', 'url', 'company_name', 'legal_name', 'registered_number', 'type', 'state_number', 'nationality', 'id_sap',
                  'characteristics', 'status', 'create_date', 'address')
        model = Company

class CompanySerializerViewBasicData(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Company
