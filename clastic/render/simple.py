
import itertools
from json import JSONEncoder
from collections import Mapping, Sized, Iterable

from werkzeug.wrappers import Response


class ClasticJSONEncoder(JSONEncoder):
    def __init__(self, **kw):
        self.dev_mode = kw.pop('dev_mode', False)
        kw.setdefault('skipkeys', True)
        kw.setdefault('ensure_ascii', True)
        kw.setdefault('indent', 2)
        kw.setdefault('sort_keys', True)
        super(ClasticJSONEncoder, self).__init__(**kw)

    def default(self, obj):
        if isinstance(obj, Mapping):
            try:
                return dict(obj)
            except:
                pass
        if isinstance(obj, Sized) and isinstance(obj, Iterable):
            return list(obj)
        if callable(getattr(obj, 'to_dict', None)):
            return obj.to_dict()

        if self.dev_mode:
            return repr(obj)  # TODO: blargh
            if isinstance(obj, type) or callable(obj):
                return unicode(repr(obj))
            try:
                return dict([(k, v) for k, v in obj.__dict__.items()
                             if not k.startswith('__')])
            except AttributeError:
                return unicode(repr(obj))
        else:
            raise TypeError('cannot serialize to JSON: %r' % obj)


class JSONRender(object):
    def __init__(self, streaming=False, dev_mode=False, encoding='utf-8'):
        self.streaming = streaming
        self.dev_mode = dev_mode
        self.encoding = encoding
        self.json_encoder = ClasticJSONEncoder(encoding=encoding,
                                               dev_mode=self.dev_mode)

    def __call__(self, context):
        if self.streaming:
            json_iter = self.json_encoder.iterencode(context)
        else:
            json_iter = [self.json_encoder.encode(context)]
        resp = Response(json_iter, mimetype="application/json")
        resp.mimetype_params['charset'] = self.encoding
        return resp


class JSONPRender(JSONRender):
    def __init__(self, qp_name='callback', *a, **kw):
        self.qp_name = qp_name
        super(JSONPRender, self).__init__(*a, **kw)

    def __call__(self, request, context):
        cb_name = request.args.get(self.qp_name, None)
        if not cb_name:
            return super(JSONPRender, self).__call__(context)
        json_iter = self.json_encoder.iterencode(context)
        resp_iter = itertools.chain([cb_name, '('], json_iter, [');'])
        resp = Response(resp_iter, mimetype="application/javascript")
        resp.mimetype_params['charset'] = self.encoding
        return resp


class BasicRender(object):
    def __init__(self, dev_mode=True):
        self.json_render = JSONRender(dev_mode=dev_mode)

    def __call__(self, context):
        if isinstance(context, basestring):
            if '<html' in context[:168]:  # based on the longest DOCTYPE found
                return Response(context, mimetype="text/html")
            elif self._guess_json(context):
                return Response(context, mimetype="application/json")
            else:
                return Response(context, mimetype="text/plain")
        if isinstance(context, Sized):
            try:
                return self.json_render(context)
            except:
                pass
        return Response(unicode(context), mimetype="text/plain")

    @staticmethod
    def _guess_json(text):
        if not text:
            return False
        elif text[0] == '{' and text[-1] == '}':
            return True
        elif text[0] == '[' and text[-1] == ']':
            return True
        else:
            return False

    @classmethod
    def factory(cls, *a, **kw):
        def basic_render_factory(render_arg):
            # behavior doesn't change depending on render_arg
            return cls(*a, **kw)
        return basic_render_factory


render_json = JSONRender()
render_json_dev = JSONRender(dev_mode=True)
render_basic = BasicRender()


#TODO: deprecate


DefaultRender = BasicRender
json_response = render_json
dev_json_response = render_json_dev
default_response = render_basic
