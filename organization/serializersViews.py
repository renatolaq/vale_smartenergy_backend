from rest_framework import serializers
from core.serializers import log, generic_update
from organization.models import Segment,Business,DirectorBoard,AccountantArea,Product, OrganizationalType, ElectricalGrouping,ProductionPhase
from locales.translates_function import translate_language
#Segment
class OrganizationSegmentSerializerView(serializers.HyperlinkedModelSerializer):
    def to_representation(self, obj):
        data = super().to_representation(obj)
        data['model'] = 'Segmento'
        return data
    class Meta:
        model = Segment
        fields = ('id_segment','description','status')

#Business
class OrganizationBusinessSerializerView(serializers.ModelSerializer):
    def to_representation(self, obj):
        data = super().to_representation(obj)
        data['model'] = 'Negócio'
        return data
    class Meta:
        model = Business
        fields = ('id_business','description','status')

#Director
class OrganizationDirectorBoardSerializerView(serializers.ModelSerializer):
    def to_representation(self, obj):
        data = super().to_representation(obj)
        data['model'] = 'Diretoria'
        return data
    class Meta:
        model = DirectorBoard
        fields = ('id_director','description','status')

#Account 
class OrganizationAccountSerializerView(serializers.ModelSerializer):
    def to_representation(self, obj):
        data = super().to_representation(obj)
        data['model'] = 'Área contábil'
        return data
    class Meta:
        model = AccountantArea
        fields = ('id_accountant','description','status')

#Product
class OrganizationProductSerializerView(serializers.ModelSerializer):
    def to_representation(self, obj):
        data = super().to_representation(obj)
        data['model'] = 'Produto'
        return data
    class Meta:
        model = Product
        fields = ('id_product','description', 'status')


class FeedSerializers(serializers.Serializer):
    item_type = serializers.CharField(max_length=30)
    data = serializers.DictField()

class OrganizationSerializerView(serializers.ModelSerializer):
    def to_representation(self, obj):
        data = super().to_representation(obj)
        data['description'] = translate_language(data['description'], self._context._request)
        return data
    class Meta:
        model = OrganizationalType
        fields = ('id_organizational_type','description')

class OrganizationAgrupationEletrictSerializerView(serializers.ModelSerializer):
    def to_representation(self, obj):
        data = super().to_representation(obj)
        data['model'] = 'Agrupamento Elétrico'
        return data
    class Meta:
        model = ElectricalGrouping
        fields = ('id_electrical_grouping','description','status')


class OrganizationProductionPhaseSerializerView(serializers.ModelSerializer):
    def to_representation(self, obj):
        data = super().to_representation(obj)
        data['model'] = 'Fase Produtiva'
        return data
    class Meta:
        model = ProductionPhase
        fields = ('id_production_phase','description','status')