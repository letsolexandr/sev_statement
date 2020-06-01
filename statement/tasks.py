from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .models import SEDStatement
import json
from requests import  put

@shared_task
def change_statement_callback(statement_id):
    if not SEDStatement.objects.filter(pk=statement_id).exists():
        return json.dumps({'object_id':statement_id,'message':'Object SEDStatement not exist'})

    statement = SEDStatement.objects.get(pk=statement_id)
    data = {'status': statement.status}
    url = statement.callback_url
    print(f'Send callback to {url}')
    print(data, url)
    resp = put(url=url, data=data)

    if resp.status_code in [200,201,202]:
        print('Success')
        return json.dumps({'url': url, 'data': data})
    else:
        print('Exception')
        print(str({'url': url, 'data': data}))
        raise Exception(url+" :: "+resp.text)