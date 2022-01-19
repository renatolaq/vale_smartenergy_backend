from rest_framework import serializers
from core.serializers import log, generic_update,generic_validation_status, generic_insert_user_and_observation_in_self
from organization.models import Segment, Business, DirectorBoard, AccountantArea, Product, ElectricalGrouping, ProductionPhase
from energy_composition.models import EnergyComposition
from gauge_point.models import GaugePoint



def validate_status(pk, status, model, self):
    if status is None:
        return 'S'
    elif model=="Segment":
        if status == 'N':
            kwargs = {EnergyComposition: 'id_segment'}
            status_message = generic_validation_status(pk, 'Segment', kwargs, self)
            if status_message != 'S':
                raise serializers.ValidationError(status_message)
        return status
    elif model=="Business":
        if status == 'N':
            kwargs = {EnergyComposition: 'id_business'}
            status_message = generic_validation_status(pk, 'Business', kwargs, self)
            if status_message != 'S':
                raise serializers.ValidationError(status_message)
        return status
    elif model=="DirectorBoard":
        if status == 'N':
            kwargs = {EnergyComposition: 'id_director'}
            status_message = generic_validation_status(pk, 'DirectorBoard', kwargs, self)
            if status_message != 'S':
                raise serializers.ValidationError(status_message)
        return status
    elif model=="AccountantArea":
        if status == 'N':
            kwargs = {EnergyComposition: 'id_accountant'}
            status_message = generic_validation_status(pk, 'AccountantArea', kwargs, self)
            if status_message != 'S':
                raise serializers.ValidationError(status_message)
        return status
    elif model=="Product":
        if status == 'N':
            kwargs = {}
            status_message = generic_validation_status(pk, 'Product', kwargs, self)
            if status_message != 'S':
                raise serializers.ValidationError(status_message)
        return status
    elif model=="ElectricalGrouping":
        if status == 'N':
            kwargs = {GaugePoint: 'id_electrical_grouping'}
            status_message = generic_validation_status(pk, 'ElectricalGrouping', kwargs, self)
            if status_message != 'S':
                raise serializers.ValidationError(status_message)
        return status
    elif model=="ProductionPhase":
        if status == 'N':
            kwargs = {EnergyComposition: 'id_production_phase'}
            status_message = generic_validation_status(pk, 'ProductionPhase', kwargs, self)
            if status_message != 'S':
                raise serializers.ValidationError(status_message)
        return status

##############Segment
class OrganisationSegmentSerializer(serializers.ModelSerializer ):
    description = serializers.CharField(
        write_only=False,
        help_text='* Insert description of organization',
        required=True
    )
    status = serializers.CharField(default='S', required=False)
    class Meta:
        fields = ('id_segment','description','status')
        model = Segment
        

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(OrganisationSegmentSerializer, self).__init__(*args, **kwargs)

    def to_representation(self, obj):
        data = super().to_representation(obj)
        data['model'] = '5'
        return data

    def create(self, validated_data):
        segment = Segment.objects.create( **validated_data)
        log(Segment, segment.id_segment, {}, segment, self.user, self.observation_log, action="INSERT")
        return segment

    def update(self, instance, validated_data):
        validate_status(instance.id_segment, dict(validated_data)['status'], "Segment", self)
        generic_update(Segment, instance.id_segment, dict(validated_data), self.user, self.observation_log)
        return instance

##############Business
class OrganisationBusinessSerializer(serializers.ModelSerializer):

    description = serializers.CharField(
        write_only=False,
        help_text='* Insert description of organization',
        required=True
    )
    status = serializers.CharField(default='S', required=False)
    class Meta:
        fields = ('id_business','description','status')
        model = Business

    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(OrganisationBusinessSerializer, self).__init__(*args, **kwargs)

    def to_representation(self, obj):
        data = super().to_representation(obj)
        data['model'] = '3'
        return data

    def create(self, validated_data):
        business = Business.objects.create(**validated_data)
        log(Business, business.id_business, {}, business, self.user, self.observation_log, action="INSERT")
        return business

    def update(self, instance, validated_data):
        validate_status(instance.id_business, dict(validated_data)['status'], "Business", self)
        generic_update(Business, instance.id_business, dict(validated_data), self.user, self.observation_log)
        return instance

##############DirectorBoard
class OrganisationDirectorBoardSerializer(serializers.ModelSerializer):

    description = serializers.CharField(
        write_only=False,
        help_text='* Insert description of organization',
        required=True
    )
    status = serializers.CharField(default='S', required=False)
    class Meta:
        fields = ('id_director','description','status')
        model = DirectorBoard
    
    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(OrganisationDirectorBoardSerializer, self).__init__(*args, **kwargs)

    def to_representation(self, obj):
        data = super().to_representation(obj)
        data['model'] = '2'
        return data

    def create(self, validated_data):
        directorBoard = DirectorBoard.objects.create(**validated_data)
        log(DirectorBoard, directorBoard.id_director, {}, directorBoard, self.user, self.observation_log, action="INSERT")
        return directorBoard

    def update(self, instance, validated_data):
        validate_status(instance.id_director, dict(validated_data)['status'], "DirectorBoard", self)
        generic_update(DirectorBoard, instance.id_director, dict(validated_data), self.user, self.observation_log)
        return instance

###############AccountantArea
class OrganisationAccountantAreaSerializer(serializers.ModelSerializer):

    description = serializers.CharField(
        write_only=False,
        help_text='* Insert description of organization',
        required=True
    )
    status = serializers.CharField(default='S', required=False)
    class Meta:
        fields = ('id_accountant','description','status')
        model = AccountantArea
    
    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(OrganisationAccountantAreaSerializer, self).__init__(*args, **kwargs)

    def to_representation(self, obj):
        data = super().to_representation(obj)
        data['model'] = '1'
        return data

    def create(self, validated_data):
        accountantArea = AccountantArea.objects.create(**validated_data)
        log(AccountantArea, accountantArea.id_accountant, {}, accountantArea, self.user, self.observation_log, action="INSERT")
        return accountantArea

    def update(self, instance, validated_data):
        validate_status(instance.id_accountant, dict(validated_data)['status'], "AccountantArea", self)
        generic_update(AccountantArea, instance.id_accountant, dict(validated_data), self.user, self.observation_log)
        return instance

###############Product
class OrganisationProductSerializer(serializers.ModelSerializer):
    status = serializers.CharField(default='S', required=False)
    class Meta:
        fields = ('id_product','description','status')
        model = Product
    
    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(OrganisationProductSerializer, self).__init__(*args, **kwargs)

    def to_representation(self, obj):
        data = super().to_representation(obj)
        data['model'] = '4'
        return data

    def create(self, validated_data):
        product = Product.objects.create(**validated_data)
        log(Product, product.id_product, {}, product, self.user, self.observation_log, action="INSERT")
        return product

    def update(self, instance, validated_data):
        validate_status(instance.id_product, dict(validated_data)['status'], "Product", self)
        generic_update(Product, instance.id_product, dict(validated_data), self.user, self.observation_log)
        return instance

###############Agrupamento Elétrico
class OrganisationAgrupationEletrictSerializer(serializers.ModelSerializer):
    status = serializers.CharField(default='S', required=False)
    class Meta:
        fields = ('id_electrical_grouping','description','status')
        model = ElectricalGrouping
    
    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(OrganisationAgrupationEletrictSerializer, self).__init__(*args, **kwargs)

    def to_representation(self, obj):
        data = super().to_representation(obj)
        data['model'] = '6'
        return data

    def create(self, validated_data):
        electricalGrouping = ElectricalGrouping.objects.create(**validated_data)
        log(ElectricalGrouping, electricalGrouping.id_electrical_grouping, {}, electricalGrouping, self.user, self.observation_log, action="INSERT")
        return electricalGrouping

    def update(self, instance, validated_data):
        validate_status(instance.id_electrical_grouping, dict(validated_data)['status'], "ElectricalGrouping", self)
        generic_update(ElectricalGrouping, instance.id_electrical_grouping, dict(validated_data), self.user, self.observation_log)
        return instance       


###############Fase Produtiva
class OrganizationProductionPhaseSerializer(serializers.ModelSerializer):
    status = serializers.CharField(default='S', required=False)
    class Meta:
        fields = ('id_production_phase','description','status')
        model = ProductionPhase
    
    def __init__(self, *args, **kwargs):
        generic_insert_user_and_observation_in_self(self, **kwargs)
        super(OrganizationProductionPhaseSerializer, self).__init__(*args, **kwargs)

    def to_representation(self, obj):
        data = super().to_representation(obj)
        data['model'] = '6'
        return data

    def create(self, validated_data):
        productionPhase = ProductionPhase.objects.create(**validated_data)
        log(ProductionPhase, productionPhase.id_production_phase, {}, productionPhase, self.user, self.observation_log, action="INSERT")
        return productionPhase

    def update(self, instance, validated_data):
        validate_status(instance.id_production_phase, dict(validated_data)['status'], "ProductionPhase", self)
        generic_update(ProductionPhase, instance.id_production_phase, dict(validated_data), self.user, self.observation_log)
        return instance 