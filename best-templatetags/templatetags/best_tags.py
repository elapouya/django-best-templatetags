# -*- coding: utf-8 -*-
'''
Création : 12 janv. 2010

@author: Eric Lapouyade
'''
from django.conf import settings
from django import template
from django.utils import simplejson
import re
from bisect import bisect
from django.template import Variable, VariableDoesNotExist, Template


register = template.Library()

class ReparseNode(template.Node):
    def __init__(self, value):
        self.value = value

    def render(self, context):
        t = Template(self.value.resolve(context, True))
        return t.render(context)

@register.tag('reparse')
def do_reparse(parser, token):
    """
    Reparse a string so the tags and variables included will expanded

    Syntax::
        {% reparse value %}
    Example::
        {% reparse flatpages.content %}

    """
    bits = token.contents.split()
    if len(bits) != 2:
        raise template.TemplateSyntaxError("'%s' tag takes 1 argument" % bits[0])
    value = parser.compile_filter(bits[1])
    return ReparseNode(value)

class AssignNode(template.Node):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def render(self, context):
        context[self.name] = self.value.resolve(context, True)
        return ''

@register.tag('assign')
def do_assign(parser, token):
    """
    Assign an expression to a variable in the current context.

    Syntax::
        {% assign [name] [value] %}
    Example::
        {% assign list entry.get_related %}

    """
    bits = token.contents.split()
    if len(bits) != 3:
        raise template.TemplateSyntaxError("'%s' tag takes two arguments" % bits[0])
    value = parser.compile_filter(bits[2])
    return AssignNode(bits[1], value)


class SizeCssNode(template.Node):
    def __init__(self, var_to_css, bname):
        self.var_to_css = template.Variable(var_to_css)
        self.bname = bname

    def render(self, context):
        size = len(self.var_to_css.resolve(context))
        bisect_dict = getattr(settings,self.bname)
        return bisect_dict['css'][bisect(bisect_dict['size'],size)]

@register.tag('size_to_css')
def do_size_to_css(parser, token):
    """
    return a css class depending the size of an element

    Syntax::
        {% size_to_css string bisect_dict_from_settings %}
    Example::
        {% size_to_css topics.title TITLE_SIZE_CSS_BISECT %}

    in settings.py :
    TITLE_SIZE_CSS_BISECT = {'css' : ['ts-big','ts-normal','ts-medium','ts-small'], 'size' : [30,50,70]}

    """
    bits = token.contents.split()
    if len(bits) != 3:
        raise template.TemplateSyntaxError("'%s' tag takes two arguments" % bits[0])
    return SizeCssNode(bits[1], bits[2])

class DebugVariable(template.Variable):
    def _resolve_lookup(self, context):
        current = context
        for bit in self.lookups:
            try: # dictionary lookup
                current = current[bit]
            except (TypeError, AttributeError, KeyError):
                try: # attribute lookup
                    current = getattr(current, bit)
                    if callable(current):
                        if getattr(current, 'alters_data', False):
                            current = settings.TEMPLATE_STRING_IF_INVALID
                        else:
                            try: # method call (assuming no args required)
                                current = current()
                            except:
                                raise Exception("Template Object Method Error : %s" % traceback.format_exc())
                except (TypeError, AttributeError):
                    try: # list-index lookup
                        current = current[int(bit)]
                    except (IndexError, # list index out of range
                            ValueError, # invalid literal for int()
                            KeyError,   # current is a dict without `int(bit)` key
                            TypeError,  # unsubscriptable object
                            ):
                        raise template.VariableDoesNotExist("Failed lookup for key [%s] in %r", (bit, current)) # missing attribute
                except Exception, e:
                    if getattr(e, 'silent_variable_failure', False):
                        current = settings.TEMPLATE_STRING_IF_INVALID
                    else:
                        raise
            except Exception, e:
                if getattr(e, 'silent_variable_failure', False):
                    current = settings.TEMPLATE_STRING_IF_INVALID
                else:
                    raise

        return current

class DebugVarNode(template.Node):
    def __init__(self, var):
        self.var = DebugVariable(var)

    def render(self, context):
        return self.var.resolve(context)

@register.tag('debug_var')
def do_debug_var(parser, token):
    """
    raise every variable rendering exception, TypeError included (usually hidden by django)

    Syntax::
        {% debug_var obj.my_method %} instead of {{ obj.my_method }}
    """
    bits = token.contents.split()
    if len(bits) != 2:
        raise template.TemplateSyntaxError("'%s' tag takes one argument" % bits[0])
    return DebugVarNode(bits[1])

class VariablesNode(template.Node):
    """
    {% var as person %}
    {
         "firstName": "John",
         "lastName": "Smith",
          "address": {
              "streetAddress": "21 2nd Street",
              "city": "New York",
              "state": "NY",
              "postalCode": 10021
          },
          "phoneNumbers": [
              "212 555-1234",
              "646 555-4567"
          ]
      }
     {% endvar %}

     <p>{{person.firstName}}, </br>
        {{person.address.postalCode}}, </br>
        {{person.phoneNumbers.1}}
     </p>
    """
    def __init__(self, nodelist, var_name):
        self.nodelist = nodelist
        self.var_name = var_name

    def render(self, context):
        source = self.nodelist.render(context)
        context[self.var_name] = simplejson.loads(source)
        return ''

@register.tag(name='var')
def do_variables(parser, token):
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        msg = '"%s" tag requires arguments' % token.contents.split()[0]
        raise template.TemplateSyntaxError(msg)
    m = re.search(r'as (\w+)', arg)
    if m:
        var_name, = m.groups()
    else:
        msg = '"%s" tag had invalid arguments' % tag_name
        raise template.TemplateSyntaxError(msg)

    nodelist = parser.parse(('endvar',))
    parser.delete_first_token()
    return VariablesNode(nodelist, var_name)

class ObjectDetailNode(template.Node):
    def __init__(self, objvar, **kwargs):
        self.objvar = template.Variable(objvar)
        self.kwargs = kwargs
        print 'obj =',objvar,' kwargs =',kwargs
    def render(self, context):
        obj = self.objvar.resolve(context)
        return getattr(obj,self.kwargs['fields'][0])

@register.tag(name='object_detail')
def do_object_detail(parser, token):
    try:
        args = token.contents.split()
        tag = args[0]
        objvar = args[1]
        params = args[2:]
    except ValueError:
        msg = '"%s" tag requires at least an object variable' % tag
        raise template.TemplateSyntaxError(msg)
    kwargs = {}
    for p in params:
        splitted = p.split('=')
        if len(splitted) < 2:
            kwargs['fields'] = splitted[0].split(',')
        else:
            kwargs[splitted[0]] = splitted[1].split(',')

    return ObjectDetailNode(objvar, **kwargs)

