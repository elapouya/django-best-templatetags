# -*- coding: utf-8 -*-
'''
Création : 12 janv. 2010

@author: Eric Lapouyade
'''
from django.conf import settings
from django import template
from django.utils.html import conditional_escape
from django.template.defaultfilters import stringfilter,force_escape,linenumbers
from django.utils.safestring import mark_safe
import re
import os.path
try:
    from bs4 import BeautifulSoup, Comment
except ImportError:
    from BeautifulSoup import BeautifulSoup, Comment
from django.utils.translation import ugettext as _
import datetime
from django.template import Variable, VariableDoesNotExist, Template


register = template.Library()

@register.filter
@stringfilter
def basename(str):
    return os.path.basename(str)

@register.filter
@stringfilter
def nl2br(str):
    return str.replace('\n', '<br>')

@register.filter
def format(val,arg):
    return val % arg

@stringfilter
@register.filter
def replace(str,arg):
    sep=arg[0]
    params = arg.split(sep)
    pat = params[1]
    rep = params[2]
    return str.replace(pat,rep)

@stringfilter
@register.filter
def resub(str,arg):
    sep=arg[0]
    params = arg.split(sep)
    pat = params[1]
    rep = params[2]
    flags = re.I if params[-1] == 'i' else 0
    regex = re.compile(pat,flags=flags)
    return regex.sub(rep,str)

@register.filter
def multiply(val,arg):
    return val * arg

@register.filter
def divide(val,arg):
    return val / arg

@register.filter
@stringfilter
def truncate(str,arg):
    if len(str) > arg:
        return str[:arg] + "..."
    else:
        return str

@register.filter
@stringfilter
def nbsp(str, autoescape=True):
    if autoescape:
        esc = conditional_escape
    else:
        esc = lambda x: x
    return mark_safe(esc(str).replace(' ', '&nbsp;'))
nbsp.needs_autoescape = True

@register.filter
def age(bday, d=None):
    if d is None:
        d = datetime.date.today()
    return (d.year - bday.year) - int((d.month, d.day) < (bday.month, bday.day))

@register.filter
def deltaday_human_simple(t1, t2=None):
    if t2 is None:
        t2 = datetime.datetime.now()
    d = t2 - t1
    days=d.days
    if days:
        if not days :
            return _('today')
        elif days < 7 :
            return _('%d days') % days
        elif days < 14 :
            return _('one week')
        elif days < 30 :
            return _('%d weeks') % int(days / 7)
        elif days < 60 :
            return _('one month')
        elif days < 365 :
            return _('%d months') % int(days / 30)
        elif days < 730 :
            return _('one year')
        else:
            return _('%d years') % int(days / 365.25)

sanitize_simple_html_tags = getattr(settings,'SANITIZE_SIMPLE_HTML_TAGS','a:href b u p i h1 h2 h3 hr img:src table tr td th code')

@register.filter
def sanitize_simple_html(value):
    return sanitize(value, sanitize_simple_html_tags)

@register.filter
def sanitize(value, allowed_tags):
    """Argument should be in form 'tag2:attr1:attr2 tag2:attr1 tag3', where tags
    are allowed HTML tags, and attrs are the allowed attributes for that tag.
    """
    js_regex = re.compile(r'[\s]*(&#x.{1,7})?'.join(list('javascript')))
    allowed_tags = [tag.split(':') for tag in allowed_tags.split()]
    allowed_tags = dict((tag[0], tag[1:]) for tag in allowed_tags)

    try:
        soup = BeautifulSoup(value)
    except Exception, e:
        return '<br><span class="warning">%s :<br>%s</span><br><pre class="sanitize">%s</pre>' % (str(e), _('You have a HTML syntax error, please, check you have quote href and src attributes, that is href="xxx" or src="yyy" and not href=xxx or src=yyy'), linenumbers(value, True) )

    for comment in soup.findAll(text=lambda text: isinstance(text, Comment)):
        comment.extract()

    for tag in soup.findAll(True):
        if tag.name not in allowed_tags:
            tag.hidden = True
        else:
            tag.attrs = [(attr, js_regex.sub('', val)) for attr, val in tag.attrs
                         if attr in allowed_tags[tag.name]]

    return soup.renderContents().decode('utf8')

@register.filter
def hash(object, attr):
    """ permet d'utiliser la notation pointé avec une variable comme attribut :
        permet de prendre un item d'un dict via une variable comme index.
        Si l'index n'est pas connu, essaye avec 'default_index'.
        Ex : {{ user|hash:my_var }}
    """
    pseudo_context = { 'object' : object }
    try:
        value = Variable('object.%s' % attr).resolve(pseudo_context)
    except VariableDoesNotExist:
        try:
            value = Variable('object.default_index').resolve(pseudo_context)
        except VariableDoesNotExist:
            value = None
    return value

@register.filter
def listsort(lst):
    if not lst:
        return []
    return sorted(lst)