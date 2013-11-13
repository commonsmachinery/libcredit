# -*- coding: utf-8 -*-
# libcredit - module for converting RDF metadata to human-readable strings
#
# Copyright 2013 Commons Machinery http://commonsmachinery.se/
#
# Authors: Artem Popov <artfwo@commonsmachinery.se>
#          Peter Liljenberg <peter@commonsmachinery.se>
#
# Distributed under an GPLv2 license, please see LICENSE in the top dir.

import sys
import re
import gettext
import rdflib
from xml.dom import minidom

# py3k compatibility
try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

# another compatibility hack
try:
    basestring = basestring
except NameError:
    basestring = str
    unicode = str

def get_i18n(languages = None):
    if languages is None:
        i18n = gettext.translation('libcredit', sys.prefix + '/share/locale', fallback = True)
    else:
        i18n = gettext.translation('libcredit', sys.prefix + '/share/locale', languages = languages)

    i18n.set_output_charset('utf-8')
    return i18n

# Set up a default translation based on the system locale
_i18n = get_i18n()


_cc_license_url_re = re.compile("^https?://creativecommons.org/licenses/([-a-z]+)/([0-9.]+)/(?:([a-z]+)/)?(?:deed\..*)?$")

_cc_public_domain_url_re = re.compile("^https?://creativecommons.org/publicdomain/([a-z]+)/([0-9.]+)/(?:deed\..*)?$")

_free_art_license_url_re = re.compile("^https?://artlibre.org/licence/lal(?:/([-a-z0-9]+))?$")

def get_license_label(url):
    """
    Return a human-readable short name for a license.
    If the URL is unknown, it is returned as-is.

    Parameters:
    url -- the license URL
    """

    m = _cc_license_url_re.match(url)
    if m:
        g = m.groups()
        return 'CC %s %s %s' % (g[0].upper(), g[1], "(%s)" % g[2].upper() if g[2] else "Unported")

    m = _cc_public_domain_url_re.match(url)
    if m:
        g = m.groups()
        if g[0] == 'zero':
            return 'CC0 ' + g[1]
        elif g[0] == 'mark':
            return 'public domain'

    m = _free_art_license_url_re.match(url)
    if m:
        g = m.groups()
        return 'Free Art License %s' % ('1.2' if g[0] == 'licence-art-libre-12' else '1.3')

    return url;


# credit markup templates for metadata of various completeness
# key format: (title != None, attrib != None, license != None)
CREDIT_MARKUP = {
    (True, True, True):     "<title> by <attrib> (<license>).",
    (True, True, False):    "<title> by <attrib>.",
    (True, False, True):    "<title> (<license>).",
    (True, False, False):   "<title>.",
    (False, True, True):    "Credit: <attrib> (<license>).",
    (False, True, False):   "Credit: <attrib>.",
    (False, False, True):   "License: <license>.",
    (False, False, False):  None,
}

ITEM_RE = re.compile('(<[a-z]+>)')


DC = rdflib.Namespace('http://purl.org/dc/elements/1.1/')
DCTERMS = rdflib.Namespace('http://purl.org/dc/terms/')
CC = rdflib.Namespace('http://creativecommons.org/ns#')
XHV = rdflib.Namespace('http://www.w3.org/1999/xhtml/vocab#')
OG = rdflib.Namespace('http://ogp.me/ns#')


def a2uri(obj):
    """
    Shorthand for rdflib.URIRef(obj). Used for converting strings
    to rdflib URIs.
    """
    if isinstance(obj, rdflib.URIRef):
        return obj
    elif isinstance(obj, basestring):
        return rdflib.URIRef(obj)
    else:
        raise ValueError("Unrecognisable URI type for object: %s" % obj)

def get_url(url):
    """
    Return url if it can be used as an URL,
    otherwise return None.

    Parameters:
    url -- URL
    """
    url_re = "^https?:"
    if re.match(url_re, unicode(url)):
        return url
    else:
        return None

class Credit(object):
    """
    Class for extracting credit information from RDF metadata

    Keyword arguments:
    rdf -- rdflib graph or a string of RDF/XML to parse.
    subject -- URI for querying work in the graph
    """
    def __init__(self, rdf, subject=None):
        if isinstance(rdf, rdflib.Graph):
            self.g = rdf
        else:
            self.g = rdflib.Graph()
            self.g.parse(data=rdf)

        if subject is None:
            # by the new convention, work is an object of a dc:source predicate for the about="" node
            new_subject_uri = next(self.g[a2uri(''):DC['source']:])
            subject = rdflib.term.URIRef(new_subject_uri)
        else:
            subject = rdflib.term.URIRef(subject)

        #
        # Title
        #
        self.title_url = get_url(self._get_property_any(subject, OG['url']))

        if self.title_url is None:
            self.title_url = get_url(unicode(subject))

        self.title_text = self._get_property_any(subject, [
            DC['title'],
            DCTERMS['title'],
            OG['title'],
        ])

        if self.title_text is None:
            self.title_text = self.title_url

        #
        # Attribution
        #
        self.attrib_text = self._get_property_any(subject, CC['attributionName'])
        self.attrib_url = get_url(self._get_property_any(subject, CC['attributionURL']))

        if self.attrib_text is None:
            self.attrib_text = self._get_property_any(subject, [
                DC['creator'],
                DCTERMS['creator'],
                'twitter:creator',
            ])

        if self.attrib_text is not None and self.attrib_url is None:
            self.attrib_url = get_url(self.attrib_text)

        if self.attrib_text is None:
            self.attrib_text = self.attrib_url

        #
        # License
        #
        self.license_url = get_url(self._get_property_any(subject, [
            XHV['license'],
            CC['license'],
            DCTERMS['license'],
        ]))

        if self.license_url:
            self.license_text = get_license_label(self.license_url)
        else:
            self.license_text = None

        if self.license_text is None:
            self.license_text = self._get_property_any(subject, [
                DC['rights'],
                XHV['license'],
            ])

        # flickr special cases
        # flickr_photos:by is used by flickr for the same purpose as attribution URL
        if urlparse.urlparse(str(subject))[1] == "www.flickr.com":
            try:
                flickr_by = next(self.g[subject:a2uri(u'flickr_photos:by')])
            except StopIteration:
                flickr_by = None

            # could we just use /people/XXX/ as the last resort?
            # flickr_by = urlparse.urlparse(str(flickr_by))[2].split('/')[-2]

            if self.attrib_text is None and flickr_by:
                self.attrib_text = unicode(flickr_by)

            if self.attrib_url is None and flickr_by:
                self.attrib_url = unicode(flickr_by)


        source_subjects = list(self.g[subject:DC['source']:]) + list(self.g[subject:DCTERMS['source']:])
        self.sources = []
        for s in source_subjects:
            if isinstance(s, rdflib.URIRef) or isinstance(s, rdflib.BNode):
                self.sources.append(Credit(rdf, subject=s))
            elif isinstance(s, rdflib.Literal):
                url = get_url(s)
                if url:
                    self.sources.append(Credit(rdf, subject=s))

        # TODO: raise an exception if no credit info is found?

    def format(self, formatter, source_depth = 1, i18n = _i18n):
        """
        Create human-readable credit with the given formatter.

        Keyword arguments:
        formatter -- a CreditFormatter to use for output
        source_depth -- maximum depth for source works traversal
        i18n -- a gettext class with the desired language (domain "libcredit")
        """

        markup = CREDIT_MARKUP[(
            self.title_text is not None,
            self.attrib_url is not None or self.attrib_text is not None,
            self.license_url is not None or self.license_text is not None
        )]

        if not markup:
            markup = ""
            #return # TODO: raise an exception instead?

        if i18n:
            markup = i18n.gettext(markup)

        formatter.begin()

        for item in ITEM_RE.split(markup):
            if item == '<title>':
                formatter.add_title(self.title_text, self.title_url)
            elif item == '<attrib>':
                formatter.add_attrib(self.attrib_text, self.attrib_url)
            elif item == '<license>':
                formatter.add_license(self.license_text, self.license_url)
            else:
                formatter.add_text(item)

        if self.sources and source_depth > 0:
            formatter.begin_sources(i18n.ngettext(
                    'Source:', 'Sources:', len(self.sources)))

            for s in self.sources:
                formatter.begin_source()
                s.format(formatter, source_depth - 1, i18n)
                formatter.end_source()

            formatter.end_sources()

        formatter.end()

    def _get_property_any(self, subject, properties):
        subject = a2uri(subject)

        if not isinstance(properties, list):
            properties = [properties]

        for property in properties:
            property = a2uri(property)

            try:
                value = next(self.g[rdflib.URIRef(subject):rdflib.URIRef(property):])
                if value:
                    return unicode(value)
            except StopIteration:
                pass

class CreditFormatter(object):
    """
    Base class for credit formatter that doesn't do anything.
    Override methods in this as applicable to the desired format.
    """

    def begin(self):
        """Called when the formatter begins printing credit for a source
        or the entire work."""
        pass

    def end(self):
        """Called when the formatter ends printing credit for a source
        or the entire work."""
        pass

    def begin_sources(self, label=None):
        "Called before printing the list of sources."
        pass

    def end_sources(self):
        "Called when done printing the list of sources."
        pass

    def begin_source(self):
        "Called before printing credit for a source and before begin()."
        pass

    def end_source(self):
        "Called when done printing credit for a source and after end()."
        pass

    def add_title(self, text, url):
        """Format the title for source or work.
        URL should point to the work's origin an can be null."""
        pass

    def add_attrib(self, text, url):
        """Format the attribution for source or work.
        URL should point to the work's author an can be null."""
        pass

    def add_license(self, text, url):
        """Format the work's license.
        URL should point to the license an can be null."""
        pass

    def add_text(self, text):
        "Add any text (e.g. punctuation) in the current context."
        pass

class TextCreditFormatter(CreditFormatter):
    """
    Credit formatter that outputs credit as plain text.
    """
    def __init__(self):
        self.text = u""
        self.depth = 0

    def begin(self):
        if self.depth == 0:
            self.text = u""

    def end(self):
        pass

    def begin_sources(self, label=None):
        if label:
            self.text += u" " + label.decode("utf-8")
        self.depth += 1

    def end_sources(self):
        self.depth -= 1

    def begin_source(self):
        self.text += "\n" + ("    " * self.depth) + "* "

    def end_source(self):
        pass

    def add_title(self, text, url):
        self.text += text

    def add_attrib(self, text, url):
        self.text += text

    def add_license(self, text, url):
        self.text += str(text)

    def add_text(self, text):
        self.text += text

    def get_text(self):
        return self.text

class HTMLCreditFormatter(CreditFormatter):
    """
    Credit formatter that outputs credit as HTML.

    Keyword arguments:
    document -- xml.minidom.Document instance used to create HTML elements.
    """
    def __init__(self, document=None):
        if document:
            self.doc = document
        else:
            self.doc = minidom.Document()
        self.root = None
        self.node_stack = []
        self.depth = 0

    def begin(self):
        if self.depth == 0:
            self.root = self.doc.createElement('div')
            self.node_stack.append(self.root)
            self.doc.appendChild(self.root)
        node = self.doc.createElement('p')
        self.node_stack[-1].appendChild(node)
        self.node_stack.append(node)

    def end(self):
        self.node_stack.pop()

    def begin_sources(self, label=None):
        if label:
            self.add_text(" " + label)
        node = self.doc.createElement('ul')
        self.node_stack[-1].appendChild(node)
        self.node_stack.append(node)
        self.depth += 1

    def end_sources(self):
        self.depth -= 1
        self.node_stack.pop()

    def begin_source(self):
        node = self.doc.createElement('li')
        self.node_stack[-1].appendChild(node)
        self.node_stack.append(node)

    def end_source(self):
        self.node_stack.pop()

    def add_title(self, text, url=None):
        if url:
            self.add_url(text, url)
        else:
            self.add_text(text)

    def add_attrib(self, text, url):
        if url:
            self.add_url(text, url)
        else:
            self.add_text(text)

    def add_license(self, text, url):
        if url:
            self.add_url(text, url)
        else:
            self.add_text(text)

    def add_url(self, text, url):
        a = self.doc.createElement('a')
        a.attributes['href'] = url
        a.appendChild(self.doc.createTextNode(text))
        self.node_stack[-1].appendChild(a)

    def add_text(self, text):
        self.node_stack[-1].appendChild(self.doc.createTextNode(text))

    def get_root(self):
        return self.root

    def get_text(self):
        if self.root:
            return self.root.toxml()
        else:
            return u''


if __name__ == '__main__':
    c = Credit(sys.stdin.read())
    f = TextCreditFormatter()
    c.format(f, 10)
    t = f.get_text()
    if t:
        sys.stdout.write(t + '\n')
    else:
        sys.exit('no credit\n')
