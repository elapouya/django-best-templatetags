# -*- coding: utf-8 -*-
'''
Création : 12 janv. 2010

@author: Eric Lapouyade
'''
from django.conf import settings
from django import template
from django.utils.html import conditional_escape
from django.template.defaultfilters import stringfilter,linenumbers
from django.utils.safestring import mark_safe
import re
import os.path
from bs4 import BeautifulSoup, Comment
from django.utils.translation import ugettext as _
import datetime
from django.template import Variable, VariableDoesNotExist


register = template.Library()

@register.filter
@stringfilter
def basename(str):
    """give the basename of the path

    It uses os.path.basename()

    Example:

        >>> c = {'mypath':'/a/b/c/myfile.extension'}
        >>> t = '{% load best_filters %}{{ mypath|basename }}'
        >>> Template(t).render(Context(c))
        'myfile.extension'

    """
    return os.path.basename(str)

@register.filter
@stringfilter
def dirname(str):
    """give the basename of the path

    It uses os.path.dirname()

    Example:

        >>> c = {'mypath':'/a/b/c/myfile.extension'}
        >>> t = '{% load best_filters %}{{ mypath|dirname }}'
        >>> Template(t).render(Context(c))
        '/a/b/c'

    """
    return os.path.dirname(str)

@register.filter
def multiply(val,arg):
    """Multiply by a value

    Examples:

        >>> c = {'myval':50}
        >>> t = '{% load best_filters %}{{ myval|multiply:1024 }}'
        >>> Template(t).render(Context(c))
        '51200'

        >>> c = {'mystr':'*'}
        >>> t = '{% load best_filters %}{{ mystr|multiply:8 }}'
        >>> Template(t).render(Context(c))
        '********'
    """
    return val * arg

@register.filter
def divide(val,arg):
    """Divide by a value

    Examples:

        >>> c = {'myval':50}
        >>> t = '{% load best_filters %}{{ myval|divide:2|floatformat:0 }}'
        >>> Template(t).render(Context(c))
        '25'

        >>> c = {'mystr':100}
        >>> t = '{% load best_filters %}{{ mystr|divide:3|floatformat:2 }}'
        >>> Template(t).render(Context(c))
        '33.33'
    """
    return val / arg

@stringfilter
@register.filter
def replace(str,arg):
    """Replace a substring

    The replacement syntax is :
    <chosen separator><string to replace><separator><replacement string>

    Examples:

        >>> c = {'mystr':'hello world'}
        >>> t = '{% load best_filters %}{{ mystr|replace:"/world/eric" }}'
        >>> Template(t).render(Context(c))
        'hello eric'

        >>> c = {'mypath':'/home/theuser/projects'}
        >>> t = '{% load best_filters %}{{ mypath|replace:",/home,/Users" }}'
        >>> Template(t).render(Context(c))
        '/Users/theuser/projects'
    """
    sep=arg[0]
    params = arg.split(sep)
    pat = params[1]
    rep = params[2]
    return str.replace(pat,rep)

@stringfilter
@register.filter
def resub(str,arg):
    r"""regex substitute a substring

    The substitution syntax is :
    <chosen separator><regex pattern to search><separator><replacement string>

    Examples:

        >>> c = {'mystr':'hello world'}
        >>> t = '{% load best_filters %}{{ mystr|resub:"/ .*/ eric" }}'
        >>> Template(t).render(Context(c))
        'hello eric'

        >>> c = {'mypath':'/home/theuser/projects'}
        >>> t = r'{% load best_filters %}{{ mypath|resub:",/home/([^/]*)/projects,login=\1" }}'
        >>> Template(t).render(Context(c))
        'login=theuser'
    """
    sep=arg[0]
    params = arg.split(sep)
    pat = params[1]
    rep = params[2]
    flags = re.I if params[-1] == 'i' else 0
    regex = re.compile(pat,flags=flags)
    return regex.sub(rep,str)

@register.filter
def age(bday, d=None):
    """give the age in year

    Example:

        >>> c = {'user_birthdate':datetime(2006,11,9)}
        >>> t = '{% load best_filters %}{{ user_birthdate|age }} years old'
        >>> Template(t).render(Context(c))
        '11 years old'

    """
    if d is None:
        d = datetime.date.today()
    return (d.year - bday.year) - int((d.month, d.day) < (bday.month, bday.day))

@stringfilter
@register.filter
def truncat(str, pattern):
    r"""truncate the string at the specified pattern

    Useful with filters timesince and timeuntil
    pattern is a regex expression string
    Do not forget to escape the dot (\.) if it the char you want to search

    Example:

        >>> c = {'str':'abc...xyz'}
        >>> t = '{% load best_filters %}{{ str|truncat:"\." }}'
        >>> Template(t).render(Context(c))
        'abc'

        >>> c = {'t1':datetime(1789,7,14),'t2':datetime(2018,1,21)}
        >>> t = '''{% load best_filters %}
        ... timesince with 2 terms : {{ t1|timesince:t2 }}
        ... timesince with 1 term : {{ t1|timesince:t2|truncat:"," }}'''
        >>> print(Template(t).render(Context(c)))
        <BLANKLINE>
        timesince with 2 terms : 228 years, 6 months
        timesince with 1 term : 228 years
    """
    return re.sub(pattern+'.*', '', str)

@register.filter
def sanitizetags(value, allowed_tags=None):
    """Remove all tags that is not in the allowed list

    Argument should be in form 'tag1:attr1:attr2 tag2:attr1 tag3', where tags
    are allowed HTML tags, and attrs are the allowed attributes for that tag.
    In the example above, it means accepted tags are :
    <tag1 attr1="..." attr2="..."> and <tag2 attr1="..."> and <tag3>
    All other HTML tags an attributes will be removed.
    for example <tag2 attr1="..." attr3="..."> <tag4 ...>
    will be replaced by just <tag2 attr1="...">
    The filter also unconditionnaly removes attributes with attributes starting
    with 'javascript:' to avoid maliciouscode.

    If No argument is given, the filter will look for SANITIZETAGS_ALLOWED
    in settings or will use this default value:
    'a:href b u p i h1 h2 h3 hr img:src table tr td th code'

    Notes:

        * The output is marked as a safe string.
        * If the HTML given has not a correct syntax, an error html message is
          displayed instead of the original value.
        * Only tags are sanitized, not the text in between

    Examples:

        >>> c = {'comment':'My comment <b>with</b> <a href="spam">ads</a>'}
        >>> t = '{% load best_filters %}{{ comment|sanitizetags:"B u i"}}'
        >>> Template(t).render(Context(c))
        'My comment <b>with</b> ads'

        >>> c = {'comment':
        ... '<i>Go</i> <a badattrib="xx" href="google.com">here</a>'}
        >>> t = '{% load best_filters %}{{ comment|sanitizetags:"a:href"}}'
        >>> Template(t).render(Context(c))
        'Go <a href="google.com">here</a>'

        >>> c = {'comment':'<b><i><u>nested tags</u></i></u>'}
        >>> t = '{% load best_filters %}{{ comment|sanitizetags:"b u"}}'
        >>> Template(t).render(Context(c))
        '<b><u>nested tags</u></b>'

    """
    if allowed_tags==None:
        allowed_tags = getattr(
            settings,
            'SANITIZETAGS_ALLOWED',
            'a:href b u p i h1 h2 h3 hr img:src table tr td th code'
        )
    pattern = '\s*' + r'[\s]*(&#x.{1,7})?'.join(list('javascript:')) + '.*'
    js_regex = re.compile(pattern)
    allowed_tags = [tag.split(':') for tag in allowed_tags.lower().split()]
    allowed_tags = dict((tag[0], tag[1:]) for tag in allowed_tags)

    try:
        soup = BeautifulSoup(value, "html.parser")
    except Exception as e:
        return mark_safe(('<br><span class="warning">{} :<br>{}</span><br>'
                '<pre class="sanitizetags">{}</pre>').format(
                    str(e),
                    _('You have a HTML syntax error, please, check you have '
                      'quoted href and src attributes, that is '
                      'href="xxx" or src="yyy" and not href=xxx or src=yyy'),
                    linenumbers(value, True)
                ))

    for comment in soup.findAll(text=lambda text: isinstance(text, Comment)):
        comment.extract()

    for tag in soup.findAll(True):
        if tag.name not in allowed_tags:
            tag.hidden = True
        else:
            tag.attrs = dict(
                [(attr, val) for attr, val in tag.attrs.items()
                    if attr in allowed_tags[tag.name]
                        and not js_regex.match(val)]
            )

    return mark_safe(soup.renderContents().decode('utf8'))

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