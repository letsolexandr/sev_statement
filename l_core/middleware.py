import json
from django.utils.deprecation import MiddlewareMixin


class DeserializeJson(MiddlewareMixin):
    def process_request(self, request):
        ##l =dir(request.POST)
        in_data = request.POST
        request.POST._mutable = True
        for key in request.POST.keys():
            value = request.POST.get(key)
            if type(value)==str:
                try:
                    value_json = json.loads(value)
                    setattr(request,key,value_json)
                except Exception as e:
                    pass
        out_data = request.POST
        ##aise Exception 

