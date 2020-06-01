# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers, viewsets


from .models import CoreUser



##CoreUser-------------------------------------------------------
class CoreUserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CoreUser
        fields = ('id','first_name',)

# ViewSets define the view behavior.
class CoreUserViewSet(viewsets.ModelViewSet):
    queryset = CoreUser.objects.all()
    serializer_class = CoreUserSerializer
##-------------------------------------------------------------



