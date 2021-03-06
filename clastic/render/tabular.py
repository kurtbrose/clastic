# -*- coding: utf-8 -*-

import os
from inspect import getargspec

from werkzeug.wrappers import Response

from tableutils import Table

_CUR_PATH = os.path.dirname(os.path.abspath(__file__))
_CSS_PATH = _CUR_PATH + '/../_clastic_assets/common.css'
try:
    _STYLE_CONTENT = open(_CSS_PATH).read()
except:
    import pdb;pdb.set_trace()
    _STYLE_CONTENT = ''


class TabularRender(object):
    _html_doctype = '<!doctype html>'
    _html_wrapper, _html_wrapper_close = '<html>', '</html>'
    _html_table_tag = '<table class="clastic-atr-table">'
    _html_style_content = _STYLE_CONTENT

    def __init__(self, max_depth=4, orientation='auto'):
        self.max_depth = max_depth
        self.orientation = orientation

    def _html_format_ep(self, route):
        # TODO: callable object endpoints?
        module_name = route.endpoint.__module__
        try:
            func_name = route.endpoint.func_name
        except:
            func_name = repr(route.endpoint)
        func_name = func_name.replace('<', '(').replace('>', ')')
        args, _, _, _ = getargspec(route.endpoint)
        argstr = ', '.join(args)
        title = ('<h2><small><sub>%s</sub></small><br/>%s(%s)</h2>'
                 % (module_name, func_name, argstr))
        return title

    def __call__(self, context, _route):
        content_parts = [self._html_wrapper]
        if self._html_style_content:
            content_parts.extend(['<head><style type="text/css">',
                                  self._html_style_content,
                                  '</style></head>'])
        content_parts.append('<body>')
        title = self._html_format_ep(_route)
        content_parts.append(title)
        table = Table.from_data(context, max_depth=self.max_depth)
        table._html_table_tag = self._html_table_tag
        content = table.to_html(max_depth=self.max_depth,
                                orientation=self.orientation)
        content_parts.append(content)
        content_parts.append('</body>')
        content_parts.append(self._html_wrapper_close)
        return Response('\n'.join(content_parts), mimetype='text/html')
