# -*- coding: utf-8 -*-
'''
Création : 12 janv. 2010

@author: Eric Lapouyade
'''
from django.template import Template
from urllib.parse import urlsplit, urlunsplit
from django import template
from django.http import QueryDict
from django.utils.safestring import mark_safe
import hashlib


register = template.Library()

@register.simple_tag()
def update_url(url, **kwargs):
    """ Update url parameters

    * Not existing parameters are added
    * Existing parameters are replaced
    * parameters with "__del__" value are deleted

    Examples:

        >>> c = {'myurl':'http://a.com/b/c.html?d=1&e=2'}
        >>> t = '{% load best_tags %}{% update_url myurl e=3 f=4 %}'
        >>> Template(t).render(Context(c))
        'http://a.com/b/c.html?d=1&e=3&f=4'

        >>> c = {'myurl':'?d=1&e=2'}
        >>> t = '{% load best_tags %}{% update_url myurl e=3 f=4 %}'
        >>> Template(t).render(Context(c))
        '?d=1&e=3&f=4'

        >>> c = {'myurl':'http://a.com/b/c.html?d=1&e=2'}
        >>> t = '{% load best_tags %}{% update_url myurl d="__del__" f=4 %}'
        >>> Template(t).render(Context(c))
        'http://a.com/b/c.html?e=2&f=4'

    """
    splitted_url = urlsplit(url)
    querystring = QueryDict(splitted_url.query, mutable=True)
    # do not use update() QueryDict method here otherwise,
    # the dict will be extended
    # and the final url will grow and grow ....
    for k,v in kwargs.items():
        if v == '__del__' and k in querystring:
            del querystring[k]
        elif hasattr(v, '__iter__'):
            querystring.setlist(k, v)
        else:
            querystring[k] = v
    return mark_safe(
            urlunsplit(splitted_url._replace(query=querystring.urlencode()))
        )

@register.simple_tag()
def extend_url(url, **kwargs):
    """ Update url parameters

    * Not existing parameters are added
    * Existing parameters are extended
    * parameters with "__del__" value are deleted

    Note:

        It takes care to not have duplicate values for a same parameter.
        The values taken from the tag parameters are converted to string.

    Examples:

        >>> c = {'myurl':'http://a.com/b/c.html?d=1&e=2'}
        >>> t = '{% load best_tags %}{% extend_url myurl d=1 e=3 f=4 %}'
        >>> Template(t).render(Context(c))
        'http://a.com/b/c.html?d=1&e=2&e=3&f=4'

        >>> c = {'myurl':'?d=1&e=2'}
        >>> t = '{% load best_tags %}{% extend_url myurl e=3 f=4 %}'
        >>> Template(t).render(Context(c))
        '?d=1&e=2&e=3&f=4'

        >>> c = {'myurl':'http://a.com/b/c.html?d=1&e=2'}
        >>> t = '{% load best_tags %}{% extend_url myurl d="__del__" e=3 %}'
        >>> Template(t).render(Context(c))
        'http://a.com/b/c.html?e=2&e=3'

    """
    splitted_url = urlsplit(url)
    querystring = QueryDict(splitted_url.query, mutable=True)
    for k, v in kwargs.items():
        if v == '__del__' and k in querystring:
            del querystring[k]
        else:
            param_set = set(querystring.getlist(k))
            param_set.add(str(v))
            querystring.setlist(k,list(param_set))
    return mark_safe(
            urlunsplit(splitted_url._replace(query=querystring.urlencode()))
        )


@register.simple_tag()
def hash(algorithm, str):
    """ Return a hexadecimal md5 digest of a string

    First argument is a string giving the hash algorithm, for example:
    "md5", "sha1" ...
    Second argument is the string or variable to hash

    Note:

        string are encoded to utf-8 prior calculating the hash

    Example:

        >>> c = {'title':'My worderful document title'}
        >>> t = '{% load best_tags %}{% hash "md5" title %}'
        >>> Template(t).render(Context(c))
        '3ddbd7936634a6a47f978376674dea31'
    """
    m = hashlib.new(algorithm)
    if not isinstance(str,bytes):
        str = str.encode('utf-8')
    m.update(str)
    return m.hexdigest()

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