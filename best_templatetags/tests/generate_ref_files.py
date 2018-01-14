import sys
import os
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path[0:0] = [PROJECT_DIR]
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "best_templatetags.settings")
import django
django.setup()

from best_templatetags.tests.test_filters import FiltersTestCase
from best_templatetags.tests.test_tags import TagsTestCase


for cls in FiltersTestCase,TagsTestCase:
    test = cls()
    test.setUp()
    print(f'Generating ref file for {cls.__name__} ...')
    test.generate_ref_file()
    print('Done.')


