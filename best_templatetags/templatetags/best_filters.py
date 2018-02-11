# -*- coding: utf-8 -*-
'''
Creation : 12 janv. 2010

@author: Eric Lapouyade
'''
from django.conf import settings
from django import template
from django.utils.html import conditional_escape
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
import re
import os.path
from bs4 import BeautifulSoup, Comment
from django.utils.translation import ugettext as _
import datetime
from django.template import Variable, VariableDoesNotExist

# to get all filters :
# grep "def " best_filters.py | sed -e 's,^def ,,' -e 's,(.*,,' | sort

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
    """give the directory name of the path

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
        >>> t = r'''{% load best_filters %}
        ... {{ mypath|resub:",/home/([^/]*)/projects,login=\1" }}'''
        >>> Template(t).render(Context(c))
        '\nlogin=theuser'
    """
    sep=arg[0]
    params = arg.split(sep)
    pat = params[1]
    rep = params[2]
    flags = re.I if params[-1] == 'i' else 0
    regex = re.compile(pat,flags=flags)
    return regex.sub(rep,str)

@register.filter
def age(bday, ref_date=None):
    """give the age in year

    Argument is optionnal. If not set, the refererence day is today

    Example:

        >>> c = {'user_birthdate':datetime(2006,11,9),
        ...      'mytoday' : datetime(2018,1,21) }
        >>> t = '{% load best_filters %}{{ user_birthdate|age:mytoday }} years old'
        >>> Template(t).render(Context(c))
        '11 years old'

    """
    if ref_date is None:
        ref_date = datetime.date.today()
    return (ref_date.year - bday.year) - int(
        (ref_date.month, ref_date.day) < (bday.month, bday.day))

@stringfilter
@register.filter
def truncat(str, pattern):
    r"""truncate the string at the specified pattern

    Useful with filters timesince and timeuntil
    pattern is a regex expression string
    Do not forget to escape the dot (\.) if it the char you want to search

    Examples:

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
    r"""Remove all tags that is not in the allowed list

    Argument should be in form 'tag1:attr1:attr2 tag2:attr1 tag3', where tags
    are allowed HTML tags, and attrs are the allowed attributes for that tag.

    In the example above, it means accepted tags are :
    <tag1 attr1="..." attr2="..."> and <tag2 attr1="..."> and <tag3>
    All other HTML tags an attributes will be removed.

    for example <tag2 attr1="..." attr3="..."> <tag4 ...>
    will be replaced by just <tag2 attr1="...">

    The filter also unconditionnaly removes attributes having values starting
    with 'javascript:' to avoid malicious code.

    If No argument is given, the filter will look for SANITIZETAGS_ALLOWED
    in settings or will use this default value:
    'a:href:name b u p i h1 h2 h3 hr img:src table tr td th code'

    Notes:

        * The output is marked as a safe string.
        * If the HTML given has not a correct syntax, an error html message is
          displayed instead of the original value.
        * Only tags are sanitized, not the text in between

    Examples:

        >>> c = {'comment':'''<a href="x" name="y" id="z"></a> <b></b> <u></u>
        ... <p></p> <i></i> <h1></h1> <h2></h2> <h3></h3> <hr>
        ... <img src="x" id="y"> <table></table> <tr></tr> <td></td> <th></th>
        ... <code></code> <unkown_tag></unknown_tag> <div></div>'''}
        >>> t = '{% load best_filters %}{{ comment|sanitizetags}}'
        >>> print(Template(t).render(Context(c))) #doctest: +NORMALIZE_WHITESPACE
        <a href="x" name="y"></a> <b></b> <u></u>
        <p></p> <i></i> <h1></h1> <h2></h2> <h3></h3> <hr/>
        <img src="x"/> <table></table> <tr></tr> <td></td> <th></th>
        <code></code>

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

        >>> c = {'comment':'''<a href="javascript:hack_me();" name="iambad">
        ... <a href="http://google.com" name="iamgood">'''}
        >>> t = '{% load best_filters %}{{ comment|sanitizetags:"a:href:name"}}'
        >>> Template(t).render(Context(c))
        '<a name="iambad">\n<a href="http://google.com" name="iamgood"></a></a>'
    """
    if allowed_tags==None:
        allowed_tags = getattr(
            settings,
            'SANITIZETAGS_ALLOWED',
            'a:href:name b u p i h1 h2 h3 hr img:src table tr td th code'
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
                    _('Unable to parse the HTML text you gave. '
                      'Please, check your syntax'),
                    value
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
def get_key(object, attr):
    """Give access to a dict value with a key contained in a var

    Example :

        >>> c = {'countries': {'FR':'France','US':'United States'},
        ...      'country':'FR'}
        >>> t = '{% load best_filters %}Country:{{ countries|get_key:country }}'
        >>> Template(t).render(Context(c))
        'Country:France'
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
def listsort(lst,col=None):
    r""" Sort a list or a list of lists/tuples

    If no argument is given, the list is sorted like python does by default.
    If an argunment is given (int), the filter is expecting a
    list of lists/tuples and will sort following the column 'col' order

    Examples :

        >>> c = { 'lst': ['a','c','b'] }
        >>> t = '''{% load best_filters %}
        ... sorted : {% for i in lst|listsort %}{{i}}{% endfor %}'''
        >>> Template(t).render(Context(c))
        '\nsorted : abc'

        >>> c = { 'lst': [('a',3),('c',1),('b',2)] }
        >>> t = '''{% load best_filters %}
        ... sorted : {% for i in lst|listsort:1 %}{{i|safe}}{% endfor %}'''
        >>> Template(t).render(Context(c))
        "\nsorted : ('c', 1)('b', 2)('a', 3)"
    """
    if not lst:
        return []
    if col and isinstance(col,int):
        return sorted(lst,key=lambda c:c[col])
    return sorted(lst)

@register.filter
def listsortreversed(lst,col=None):
    r""" Sort a list or a list of lists/tuples in reversed order

    Same as :func:`listsort` except that is reverse the order

    Examples :

        >>> c = { 'lst': ['a','c','b'] }
        >>> t = '''{% load best_filters %}
        ... sorted : {% for i in lst|listsortreversed %}{{i}}{% endfor %}'''
        >>> Template(t).render(Context(c))
        '\nsorted : cba'

        >>> c = { 'lst': [('a',3),('b',1),('c',2)] }
        >>> t = '''{% load best_filters %}
        ... sorted : {% for i in lst|listsortreversed:1 %}{{i|safe}}{% endfor %}'''
        >>> Template(t).render(Context(c))
        "\nsorted : ('a', 3)('c', 2)('b', 1)"
    """
    return reversed(listsort(lst,col))
