from django.test import TestCase
from django.template.loader import render_to_string
import os.path

GENERATE_REF_FILE = True
TEST_DIR = os.path.dirname(os.path.realpath(__file__))

class FiltersTestCase(TestCase):
    compare_file = 'test_filters.out'
    maxDiff = None

    def setUp(self):
        self.context = dict(
            file_path='/a/b/c/myfile.extension',
            nl2br_text='hello\nworld',
        )

    def test_filters(self):
        reference_filename = os.path.join(TEST_DIR, self.compare_file)
        rendered = render_to_string('best_templatetags/test_filters.html', self.context)
        if GENERATE_REF_FILE:
            with open(reference_filename,'w') as fh:
                fh.write(rendered)
        else:
            with open(reference_filename) as fh:
                reference = fh.read()
            self.assertMultiLineEqual(reference,rendered)