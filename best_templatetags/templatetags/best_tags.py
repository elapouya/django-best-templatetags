# -*- coding: utf-8 -*-
'''
Création : 12 janv. 2010

@author: Eric Lapouyade
'''
from django.template import Template
from urllib.parse import urlsplit, urlunsplit
from django import template
from django.http import QueryDict


register = template.Library()

@register.simple_tag
def update_url(url, **kwargs):
    """ Update url parameters
    """

    parsed = urlsplit(url)
    querystring = QueryDict(parsed.query, mutable=True)
    # do not use update() QueryDict method here otherwise,
    # the dict will be extended
    # and the final url will grow and grow ....
    for k,v in kwargs:
        querystring[k] = v
    return urlunsplit(parsed._replace(query=querystring.urlencode()))


def render_template(value):
    # fake function for sphinx autodoc and doctest, do not remove
    """ Render a string as it was a Django template

    It will use the same context as the outer template.

    Example:

        >>> c = {'mytemplate':'my value = {{myvar}}',
        ...      'myvar':'myvalue'}
        >>> t = '''{% load best_tags %}My template : {{ mytemplate }}
        ... with myvar = {{myvar}}
        ... My template rendered : {% render_template mytemplate %}'''
        >>> print(Template(t).render(Context(c)))
        My template : my value = {{myvar}}
        with myvar = myvalue
        My template rendered : my value = myvalue

    """

class Render_templateNode(template.Node):
    def __init__(self, value):
        self.value = value

    def render(self, context):
        t = Template(self.value.resolve(context, True))
        return t.render(context)

@register.tag('render_template')
def do_render_template(parser, token):
    bits = token.contents.split()
    if len(bits) != 2:
        raise template.TemplateSyntaxError("'%s' tag takes 1 argument" % bits[0])
    value = parser.compile_filter(bits[1])
    return Render_templateNode(value)