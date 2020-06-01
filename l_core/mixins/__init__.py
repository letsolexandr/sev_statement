
class CheckProtected(object):
    @property
    def is_protected(self):
        if hasattr(self,'protected'):
            return getattr(self,'protected')
        else:
            return False



class RelatedObjects(object):
    @property
    def related_objects(self):
            """Повертає список повязаних обєктів"""
            obj = self
            ##name = obj._meta.verbose_name
            if not hasattr(obj._meta,'related_objects'):
                return []

            related_fields = obj._meta.related_objects
            related_list = []
            for related in related_fields:
                field_name = related.get_cache_name()
                if hasattr(obj, field_name):
                    related_field = getattr(obj, field_name)
                    if hasattr(related_field, 'all'):
                        queryset = related_field.all()
                        children = []
                        name = None
                        for item in queryset:
                            name = item._meta.verbose_name_plural
                            children.append({'id': item.id, 'name': str(item)})

                        if name:
                            data = {'name': name, 'id': obj.id, 'children': children}
                            related_list.append(data)
                    else:
                        data = {'name': str(related_field), 'id': related_field.id}
                        related_list.append(data)
            return related_list