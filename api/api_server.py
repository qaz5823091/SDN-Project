import os

from webob.static import DirectoryApp

from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.base import app_manager


PATH = os.path.dirname(__file__)


# Serving static files
class ApiServerApp(app_manager.RyuApp):
    _CONTEXTS = {
        'wsgi': WSGIApplication,
    }

    def __init__(self, *args, **kwargs):
        super(ApiServerApp, self).__init__(*args, **kwargs)

        wsgi = kwargs['wsgi']
        wsgi.register(ApiServerAppController)

class ApiServerAppController(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(ApiServerAppController, self).__init__(req, link, data, **config)
        path = "%s/web/" % PATH
        self.static_app = DirectoryApp(path)

    @route('topology', '/{filename:[^/]*}')
    def static_handler(self, req, **kwargs):
        if kwargs['filename']:
            req.path_info = kwargs['filename']
        return self.static_app(req)

app_manager.require_app('ryu.app.learning_module_auto_rest')
app_manager.require_app('ryu.app.ofctl_rest')
app_manager.require_app('ryu.app.ws_topology')
app_manager.require_app('ryu.app.rest_topology')
