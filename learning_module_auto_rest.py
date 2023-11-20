import json

from ryu.app.project import learning_module_auto
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.app.wsgi import ControllerBase
from ryu.app.wsgi import Response
from ryu.app.wsgi import route
from ryu.app.wsgi import WSGIApplication
from ryu.lib import dpid as dpid_lib

switch_instance_name = 'learning_module_api_app'
url = '/learning/host/{name}'

class LearningModuleAutoRest(learning_module_auto.LearningModuleAuto):

    _CONTEXTS = {'wsgi': WSGIApplication}

    def __init__(self, *args, **kwargs):
        super(LearningModuleAutoRest, self).__init__(*args, **kwargs)
        wsgi = kwargs['wsgi']
        wsgi.register(LearningModuleAutoController, {switch_instance_name: self})

class LearningModuleAutoController(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(LearningModuleAutoController, self).__init__(req, link, data, **config)
        print(data[switch_instance_name])
        self.switch_app = data[switch_instance_name]
    
    @route('learning', '/learning/hosts', methods = ['GET'])
    def list_all_hosts(self, req, **kwargs):
        entity = self.switch_app.entity
        result = []
        for item in entity:
            entity[item]["name"] = item
            result.append(entity[item])
        body = json.dumps(result, default = str)
        
        return Response(content_type = 'application/json', body = body)

    @route('learning', url, methods = ['GET'])
    def list_specific_host(self, req, **kwargs):
        app = self.switch_app
        name = kwargs['name']

        if name in app.entity:
            body = json.dumps(app.entity[name], default = str)
            
            return Response(status = 200, content_type = 'application/json', body = body)
        else:
            return Response(status = 404)

    # add learning site's ip
    @route('learning', url + '/learning-sites/add', methods = ['POST'])
    def add_to_whitelist(self, req, **kwargs):
        entity = self.switch_app.entity
        name = kwargs['name']
        ip = json.loads(req.body)['ip']

        if ip not in entity[name]['edu_site'] and ip not in entity[name]['entmt_site']:
            entity[name]['edu_site'].append(ip)
            return Response(status = 200)
        else:
            return Response(status = 404)

    # remove learning site's ip
    @route('learning', url + '/learning-sites/remove', methods = ['POST'])
    def remove_from_whitelist(self, req, **kwargs):
        entity = self.switch_app.entity
        name = kwargs['name']
        ip = json.loads(req.body)['ip']
        
        if ip in entity[name]['edu_site']:
            entity[name]['edu_site'].remove(ip)
            return Response(status = 200)
        else:
            return Response(status = 404)

    # add entertainment site's ip
    @route('learning', url + '/entertainment-sites/add', methods = ['POST'])
    def add_to_blacklist(self, req, **kwargs):
        entity = self.switch_app.entity
        name = kwargs['name']
        ip = json.loads(req.body)['ip']

        if ip not in entity[name]['entmt_site'] and ip not in entity[name]['edu_site'] :
            entity[name]['entmt_site'].append(ip)
            return Response(status = 200)
        else:
            return Response(status = 404)

    # remove entertainment site's ip
    @route('learning', url + '/entertainment-sites/remove', methods = ['POST'])
    def remove_from_blacklist(self, req, **kwargs):
        entity = self.switch_app.entity
        name = kwargs['name']
        ip = json.loads(req.body)['ip']
        
        if ip in entity[name]['entmt_site']:
            entity[name]['entmt_site'].remove(ip)
            return Response(status = 200)
        else:
            return Response(status = 404)

    # adjust learning ratio (incresing)
    @route('learning', url + '/ratio/learning/{value}', methods = ['GET'])
    def update_learning_ratio(self, req, **kwargs):
        entity = self.switch_app.entity
        name = kwargs['name']
        value = kwargs['value']
       
        entity[name]['credit_ratio']['incr'] = float(value)

        return Response(status = 200)

    # adjust entertainment ratio (decresing)
    @route('learning', url + '/ratio/entertainment/{value}', methods = ['GET'])
    def update_entertainment_ratio(self, req, **kwargs):
        entity = self.switch_app.entity
        name = kwargs['name']
        value = kwargs['value']
       
        entity[name]['credit_ratio']['decr'] = float(value)

        return Response(status = 200)
