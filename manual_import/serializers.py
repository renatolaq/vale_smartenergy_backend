from rest_framework import serializers
from .models import UploadFile


class UploadFileSerializer(serializers.ModelSerializer):

    class Meta:
        model = UploadFile
        fields = ['id', 'file_path', 'file_name', 'user_name', 'file_type', 'date_upload']


class ListUploadFileSerializer(serializers.ModelSerializer):

    # date_upload = serializers.DateTimeField(format="%d/%m/%Y %H:%M:%S")
    class Meta:
        model = UploadFile
        fields = ['id', 'user_name', 'date_upload', 'file_name', 'file_path', 'file_type', 'send_status', 'msg']
