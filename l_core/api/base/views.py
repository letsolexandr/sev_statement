# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from rest_framework.decorators import api_view
from validate_email import validate_email as VALIDATE_EMAIL
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


@swagger_auto_schema(methods=['post'], request_body=EmailSerializer)
@api_view(['POST'])
def validate_email(request):
    serializer = EmailSerializer(data=request.data)
    if serializer.is_valid():
        is_valid = VALIDATE_EMAIL(serializer.validated_data.get('email'),check_regex=True, check_mx=True,)
        return Response({"is_valid": is_valid})
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)