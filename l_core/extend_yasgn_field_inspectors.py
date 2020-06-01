from drf_yasg.inspectors.field import FieldInspector
from drf_yasg import openapi
from rest_framework.settings import api_settings as rest_framework_settings
from .fields import Base64FileField

class Base64Inspector(FieldInspector):
    """For otherwise unhandled fields, return them as plain :data:`.TYPE_STRING` objects."""

    def field_to_swagger_object(self, field, swagger_object_type, use_references, **kwargs):
        SwaggerType, ChildSwaggerType = self._get_partial_types(field, swagger_object_type, use_references, **kwargs)

        if isinstance(field, Base64FileField):
            result = SwaggerType(type=openapi.TYPE_STRING, read_only=True)
            if getattr(field, 'use_url', rest_framework_settings.UPLOADED_FILES_USE_URL):
                result.format = openapi.FORMAT_BASE64
            return result
