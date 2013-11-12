# -*- coding: utf-8 -*-
# libcredit - module for converting RDF metadata to human-readable strings
#
# Copyright 2013 Commons Machinery http://commonsmachinery.se/
#
# Authors: Artem Popov <artfwo@commonsmachinery.se>
#          Peter Liljenberg <peter@commonsmachinery.se>
#
# Distributed under an GPLv2 license, please see LICENSE in the top dir.

import unittest

import gettext
import rdflib
import libcredit

class TestCreditFormatter(libcredit.CreditFormatter):
    def __init__(self):
        self.source_stack = []
        self.source_depth = 0

    def begin(self):
        if (self.source_depth == 0):
            self.output = []
        self.source_depth += 1

    def end(self):
        if (self.source_depth > 1):
            self.source_stack.pop()
        self.source_depth -= 1

    def add_title(self, text, url):
        if (self.source_depth > 1):
            self.source_stack.append(url)
        self.add_line('title', text, url)

    def add_attrib(self, text, url):
        self.add_line('attrib', text, url)

    def add_license(self, text, url):
        self.add_line('license', text, url)

    def add_line(self, type, text, url):
        prefix = ''

        if len(self.source_stack) > 0:
            prefix = '<' + '> <'.join(self.source_stack) + '> '

        self.output.append(prefix + type + ' "' + \
            (text if text else '') + '" <' + \
            (url if url else '') + '>')

def load_credit(filename, source_uri):
    g = rdflib.Graph()
    g.parse('../testcases/' + filename + '.ttl', format="n3")
    credit = libcredit.Credit(g, source_uri)
    return credit

def format_credit(credit):
    tf = TestCreditFormatter()
    credit.format(tf, 10)
    actual = tf.output[:]
    actual.sort()
    return actual

def load_output(filename):
    out = open('../testcases/' + filename + '.out').read().split('\n')
    expected = [unicode(s) for s in out if s != '']
    expected.sort()
    return expected

class LibCreditTests(unittest.TestCase):
    def _test_credit_output(self, tests):
        for filename_prefix, uri in tests:
            credit = load_credit(filename_prefix, uri)
            format = format_credit(credit)
            output = load_output(filename_prefix)
            self.assertEqual(format, output)

    def test_license_label(self):
        self.assertEqual(libcredit.get_license_label('http://creativecommons.org/licenses/by-sa/3.0/'),
            'CC BY-SA 3.0 Unported')
        self.assertEqual(libcredit.get_license_label('http://creativecommons.org/licenses/by-nc/2.5/deed.en'),
            'CC BY-NC 2.5 Unported')
        self.assertEqual(libcredit.get_license_label('http://creativecommons.org/licenses/by/3.0/au/deed.en_US'),
            'CC BY 3.0 (AU)')
        self.assertEqual(libcredit.get_license_label('http://creativecommons.org/publicdomain/zero/1.0/deed.fr'),
            'CC0 1.0')
        self.assertEqual(libcredit.get_license_label('http://creativecommons.org/publicdomain/mark/1.0/deed.de'),
            'public domain')
        self.assertEqual(libcredit.get_license_label('http://artlibre.org/licence/lal'),
            'Free Art License 1.3')
        self.assertEqual(libcredit.get_license_label('http://artlibre.org/licence/lal/en'),
            'Free Art License 1.3')
        self.assertEqual(libcredit.get_license_label('http://artlibre.org/licence/lal/licence-art-libre-12'),
            'Free Art License 1.2')
        self.assertEqual(libcredit.get_license_label('http://some/rights/statement'),
            'http://some/rights/statement')

    def test_empty(self):
        credit = load_credit('nothing', 'urn:src')
        format = format_credit(credit)
        self.assertEqual(format, [])

    def test_dc(self):
        self._test_credit_output([
            ('dc-title-text', 'urn:src'),
            ('dc-title-url', 'http://test/'),
            ('dc-creator-text', 'urn:src'),
            ('dc-creator-url', 'urn:src'),
            ('dc-rights', 'urn:src'),
        ])

    def test_ccrel(self):
        self._test_credit_output([
            ('cc-attrib-name', 'urn:src'),
            ('cc-attrib-url', 'urn:src'),
            ('cc-attrib-both', 'urn:src'),
            ('cc-license', 'urn:src'),
            ('cc-full-attrib', 'http://src/'),
        ])

    def test_license_text(self):
        self._test_credit_output([
            ('xhtml-license-text', 'urn:src'),
        ])

    def test_open_graph(self):
        self._test_credit_output([
            ('og-title', 'urn:src'),
            ('og-url', 'http://src/'),
        ])

    def test_twitter(self):
        self._test_credit_output([
            ('twitter-creator', 'urn:src'),
        ])

    def test_flickr(self):
        self._test_credit_output([
            ('flickr-photos-by', 'http://www.flickr.com/photos/somecreator/123/'),
        ])

    def test_sources(self):
        self._test_credit_output([
            ('sources-uris', 'http://src/'),
            ('sources-with-sources', 'http://src/'),
            ('source-with-full-attrib', 'http://src/'),
        ])

    def test_text_formatter(self):
        credit = load_credit('source-with-full-attrib', 'http://src/')
        tf = libcredit.TextCreditFormatter()
        credit.format(tf)
        self.assertEqual(tf.get_text(),
            u'a title by name of attribution (CC BY-SA 3.0 Unported). Source:\n' + \
            '    * subsrc title by subsrc attribution (CC BY-NC-ND 3.0 Unported).')

    def test_i18n(self):
        i18n = gettext.GNUTranslations(open('../build/mo/sv/LC_MESSAGES/libcredit.mo'))
        i18n.set_output_charset('utf-8')

        credit = load_credit('source-with-full-attrib', 'http://src/')
        tf = libcredit.TextCreditFormatter()
        credit.format(tf, 10, i18n)
        self.assertEqual(tf.get_text(),
            u'a title av name of attribution (CC BY-SA 3.0 Unported). Källa:\n' + \
            '    * subsrc title av subsrc attribution (CC BY-NC-ND 3.0 Unported).')

        credit = load_credit('sources-uris', 'http://src/')
        tf = libcredit.TextCreditFormatter()
        credit.format(tf, 10, i18n)
        expected1 = u'main title. Källor:\n' + \
            '    * http://subsrc-1/.\n' + \
            '    * http://subsrc-2/.'
        expected2 = u'main title. Källor:\n' + \
            '    * http://subsrc-2/.\n' + \
            '    * http://subsrc-1/.'
        self.assertTrue(tf.get_text() == expected1 or tf.get_text() == expected2)
