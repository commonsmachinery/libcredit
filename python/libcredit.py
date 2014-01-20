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
from rdflib.namespace import RDF
from xml.dom import minidom

# py3k compatibility
try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

# We need to make sure that various strings from various places indeed
# are in unicode in both Python 2 and 3.  Everything is cast, even the
# things that seem to be unicode/str already since e.g. rdflib.URIRef
# seems to inherit unicode/str.
try:
    basestring = basestring
    def ensure_unicode(s):
        if isinstance(s, unicode): return unicode(s)
        if isinstance(s, str): return s.decode('utf-8')
        return unicode(s)

except NameError:
    basestring = str
    def ensure_unicode(s):
        if isinstance(s, str): return str(s)
        if isinstance(s, bytes): return s.decode('utf-8')
        return str(s)


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
    (True, True, True):     u"<title> by <attrib> (<license>).",
    (True, True, False):    u"<title> by <attrib>.",
    (True, False, True):    u"<title> (<license>).",
    (True, False, False):   u"<title>.",
    (False, True, True):    u"Credit: <attrib> (<license>).",
    (False, True, False):   u"Credit: <attrib>.",
    (False, False, True):   u"Terms of use: <license>.",
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
    if re.match(url_re, ensure_unicode(url)):
        return url
    else:
        return None

class CreditToken(object):
    """
    An object for storing title, attribution or license text and semantics.
    """
    def __init__(self, text=None, url=None, text_property=None, url_property=None):
        self.text = text
        self.url = url
        self.text_property = text_property
        self.url_property = url_property

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
            subject = a2uri(next(self.g[a2uri(''):DC['source']:]))
        else:
            subject = a2uri(subject)
        self.subject = subject

        self.title = CreditToken()
        self.attrib = CreditToken()
        self.license = CreditToken()

        #
        # Title
        #

        self.title.url = get_url(self._get_property_any(subject, OG['url']))

        if self.title.url is None:
            self.title.url = get_url(ensure_unicode(subject))

        self.title.text = self._get_property_any(subject, [
            DC['title'],
            DCTERMS['title'],
            OG['title'],
        ])
        self.title.text_property = (DC['title'] if self.title.text else None)

        if not self.title.text:
            self.title.text = self.title.url

        #
        # Attribution
        #
        self.attrib.text = self._get_property_any(subject, CC['attributionName'])
        if self.attrib.text:
            self.attrib.text_property = CC['attributionName']
        self.attrib.url = get_url(self._get_property_any(subject, CC['attributionURL']))
        if self.attrib.url:
            self.attrib.url_property = CC['attributionURL']

        if not self.attrib.text:
            creators = self._get_property_all(subject, [
                DC['creator'],
                DCTERMS['creator'],
            ])

            if len(creators) == 1:
                self.attrib.text = creators[0]
            else:
                # save the full list of creators for credit formatter
                self.attrib.text = creators

        # fallback to twitter:creator is dc*:creator fails
        if not self.attrib.text:
            self.attrib.text = self._get_property_any(subject, ['twitter:creator'])

        # flickr_photos:by seems to be used by flickr for the same purpose
        # that we use cc:attributionURL for, should that go to attributionURL instead?
        if urlparse.urlparse(str(subject))[1] == "www.flickr.com":
            try:
                flickr_by = next(self.g[subject:a2uri(u'flickr_photos:by')])
            except StopIteration:
                flickr_by = None

            # could we just use /people/XXX/ as the last resort?
            # flickr_by = urlparse.urlparse(str(flickr_by))[2].split('/')[-2]

            if not self.attrib.text and flickr_by:
                self.attrib.text = ensure_unicode(flickr_by)

        #  make things a little simpler by putting dc:creator into the semantics
        if not self.attrib.text_property:
            self.attrib.text_property = (DC['creator'] if self.attrib.text else None)

        if self.attrib.text and self.attrib.url is None:
            self.attrib.url = get_url(self.attrib.text)

        if not self.attrib.text:
            self.attrib.text = self.attrib.url

        #
        # License
        #

        self.license.url = get_url(self._get_property_any(subject, [
            XHV['license'],
            CC['license'],
            DCTERMS['license'],
        ]))
        self.license.url_property = (XHV['license'] if self.license.url else None)

        if self.license.url:
            self.license.text = get_license_label(self.license.url)
        else:
            self.license.text = None

        if self.license.text is None:
            self.license.text = self._get_property_any(subject, DC['rights'])
            self.license.text_property = (DC['rights'] if self.license.text else None)
            if not self.license.text:
                self.license.text = self._get_property_any(subject, XHV['license'])
                self.license.text_property = (XHV['license'] if self.license.text else None)

        source_subjects = list(self.g[subject:DC['source']:]) + list(self.g[subject:DCTERMS['source']:])
        self.sources = []
        for s in source_subjects:
            if isinstance(s, rdflib.URIRef) or isinstance(s, rdflib.BNode):
                self.sources.append(Credit(rdf, subject=s))
            elif isinstance(s, rdflib.Literal):
                url = get_url(s)
                if url:
                    self.sources.append(Credit(rdf, subject=s))


        self.title.url_property = ensure_unicode(self.title.url_property) if self.title.url_property else None
        self.title.text_property = ensure_unicode(self.title.text_property) if self.title.text_property else None
        self.attrib.url_property = ensure_unicode(self.attrib.url_property) if self.attrib.url_property else None
        self.attrib.text_property = ensure_unicode(self.attrib.text_property) if self.attrib.text_property else None
        self.license.url_property = ensure_unicode(self.license.url_property) if self.license.url_property else None
        self.license.text_property = ensure_unicode(self.license.text_property) if self.license.text_property else None

        # TODO: raise an exception if no credit info is found?

    def format(self, formatter, source_depth=1, i18n=_i18n, subject_uri=None):
        """
        Create human-readable credit with the given formatter.

        Keyword arguments:
        formatter -- a CreditFormatter to use for output
        source_depth -- maximum depth for source works traversal
        i18n -- a gettext class with the desired language (domain "libcredit")
        """

        markup = CREDIT_MARKUP[(
            bool(self.title.text),
            bool(self.attrib.url) or bool(self.attrib.text),
            bool(self.license.url) or bool(self.license.text)
        )]

        if not markup:
            markup = ""
            #return # TODO: raise an exception instead?

        if i18n:
            markup = i18n.lgettext(markup)
            if markup:
                markup = ensure_unicode(markup)

        formatter.begin(subject_uri=subject_uri)

        for item in ITEM_RE.split(markup):
            if item == u'<title>':
                formatter.add_title(self.title)
            elif item == u'<attrib>':
                if isinstance(self.attrib.text, (list, tuple)):
                    for a, author in enumerate(self.attrib.text):
                        attrib = CreditToken(text=author)
                        formatter.add_attrib(attrib)
                        if a + 1 < len(self.attrib.text):
                            formatter.add_text(u", ")
                else:
                    formatter.add_attrib(self.attrib)
            elif item == u'<license>':
                formatter.add_license(self.license)
            else:
                formatter.add_text(item)

        if self.sources and source_depth != 0:
            if i18n:
                source_string = ensure_unicode(i18n.lngettext(
                        'Source:', 'Sources:', len(self.sources)))
            else:
                source_string = 'Sources:' if len(self.sources) > 1 else 'Source:'

            formatter.begin_sources(source_string)

            for s in self.sources:
                formatter.begin_source()
                s.format(formatter, source_depth - 1, i18n, s.get_subject_uri())
                formatter.end_source()

            formatter.end_sources()

        formatter.end()

    def get_subject_uri(self):
        return ensure_unicode(self.subject)

    def _get_property_any(self, subject, properties):
        subject = a2uri(subject)

        if not isinstance(properties, list):
            properties = [properties]

        for property in properties:
            property = a2uri(property)

            try:
                value = next(self.g[rdflib.URIRef(subject):rdflib.URIRef(property):])
                if value:
                    if self._is_container(value):
                        return self._parse_container(value)
                    else:
                        return ensure_unicode(value)
            except StopIteration:
                pass

    def _get_property_all(self, subject, properties):
        subject = a2uri(subject)
        result = []

        if not isinstance(properties, list):
            properties = [properties]

        for property in properties:
            property = a2uri(property)

            for value in self.g[rdflib.URIRef(subject):rdflib.URIRef(property):]:
                if self._is_container(value):
                    result += self._parse_container(value)
                else:
                    result.append(ensure_unicode(value))

        return result

    def _is_container(self, subject):
        if (subject, RDF.type, RDF.Alt) in self.g or \
           (subject, RDF.type, RDF.Seq) in self.g or \
           (subject, RDF.type, RDF.Bag) in self.g:
            return True

    def _parse_container(self, subject):
        result = []
        for item in rdflib.graph.Seq(self.g, subject):
            result.append(ensure_unicode(item))
        if (subject, RDF.type, RDF.Alt) in self.g:
            return result[0]
        else:
            return result



class CreditFormatter(object):
    """
    Base class for credit formatter that doesn't do anything.
    Override methods in this as applicable to the desired format.
    """

    def begin(self, subject_uri=None):
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

    def add_title(self, token):
        """Format the title for source or work.
          token - a convenience object used to pass title information to the formatter.
          It always contains the following members:
          text - textual representation of the title.
          url - points to the work and can be null.
          textProperty - URI of the text property (for semantics-aware formatters).
          urlproperty - URI or the url property (for semantics-aware formatters).
        """
        pass

    def add_attrib(self, token):
        """Format the attribution for source or work.
          token - a convenience object used to pass attribution information to the formatter.
          It always contains the following members:
          text - textual representation of attribution.
          url - points to the author of the work and can be null.
          textProperty - URI of the text property (for semantics-aware formatters).
          urlproperty - URI or the url property (for semantics-aware formatters).
        """
        pass

    def add_license(self, token):
        """Format the work's license.
          token - a convenience object used to pass license information to the formatter.
          It always contains the following members:
          text - textual representation of the license.
          url - points to the work's license and can be null.
          textProperty - URI of the text property (for semantics-aware formatters).
          urlproperty - URI or the url property (for semantics-aware formatters).
        """
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

    def begin(self, subject_uri=None):
        if self.depth == 0:
            self.text = u""

    def end(self):
        pass

    def begin_sources(self, label=None):
        if label:
            self.text += u" " + label
        self.depth += 1

    def end_sources(self):
        self.depth -= 1

    def begin_source(self):
        self.text += "\n" + ("    " * self.depth) + "* "

    def end_source(self):
        pass

    def add_title(self, token):
        self.text += token.text

    def add_attrib(self, token):
        self.text += token.text

    def add_license(self, token):
        self.text += token.text

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
    def __init__(self, document=None, element_overrides={}, classes={}):
        if document:
            self.doc = document
        else:
            self.doc = minidom.Document()
        self.root = None
        self.node_stack = []
        self.subject_stack = []
        self.depth = 0

        self.elements = {}
        self.elements['root'] = element_overrides.get('root', 'div')
        self.elements['credit'] = element_overrides.get('credit', 'p')
        self.elements['source_list'] = element_overrides.get('source_list', 'ul')
        self.elements['source_item'] = element_overrides.get('source_item', 'li')
        self.elements['token_url'] = 'a'
        self.elements['token_text'] = 'span'

        self.classes = {}
        self.classes['root'] = classes.get('root', None)
        self.classes['credit'] = classes.get('credit', None)
        self.classes['source_list'] = classes.get('source_list', None)
        self.classes['source_item'] = classes.get('source_item', None)
        self.classes['title'] = classes.get('title', None)
        self.classes['attrib'] = classes.get('attrib', None)
        self.classes['license'] = classes.get('license', None)

    def begin(self, subject_uri=None):
        if self.depth == 0:
            self.root = self._create_element('root')
            self.node_stack.append(self.root)
            self.doc.appendChild(self.root)

        node = self._create_element('credit')
        self.node_stack[-1].appendChild(node)
        self.node_stack.append(node)

        if subject_uri:
            node.attributes['about'] = subject_uri

        self.subject_stack.append(subject_uri)

    def end(self):
        self.node_stack.pop()
        self.subject_stack.pop()

    def begin_sources(self, label=None):
        if label:
            self.add_text(u" " + label)
        node = self._create_element('source_list')
        if self.subject_stack[0] and self.subject_stack[-1]:
            node.attributes['about'] = self.subject_stack[-1]
            node.attributes['rel'] = ensure_unicode(DC['source'])
        self.node_stack[-1].appendChild(node)
        self.node_stack.append(node)
        self.depth += 1

    def end_sources(self):
        self.depth -= 1
        self.node_stack.pop()

    def begin_source(self):
        node = self._create_element('source_item')
        self.node_stack[-1].appendChild(node)
        self.node_stack.append(node)

    def end_source(self):
        self.node_stack.pop()

    def add_title(self, token):
        self._add_impl(token, class_key='title')

    def add_attrib(self, token):
        self._add_impl(token, class_key='attrib')

    def add_license(self, token):
        self._add_impl(token, class_key='license')

    def add_text(self, text):
        self.node_stack[-1].appendChild(self.doc.createTextNode(text))

    def get_root(self):
        return self.root

    def get_text(self):
        if self.root:
            return self.root.toxml()
        else:
            return u''

    def _create_element(self, key, class_key=None):
        if not class_key:
            class_key = key
        element = self.doc.createElement(self.elements[key])
        if self.classes.get(class_key):
            element.attributes['class'] = self.classes[class_key]
        return element

    def _add_impl(self, token, class_key):
        if token.url:
            a = self._create_element('token_url', class_key)
            a.attributes['href'] = token.url
            if self.subject_stack[0] and self.subject_stack[-1]:
                if token.url_property:
                    a.attributes['rel'] = token.url_property
                if token.text_property:
                    a.attributes['property'] = token.text_property
            a.appendChild(self.doc.createTextNode(token.text))
            self.node_stack[-1].appendChild(a)
        else:
            span = self._create_element('token_text')
            if self.subject_stack[0] and self.subject_stack[-1] and token.text_property:
                span.attributes['property'] = token.text_property
            span.appendChild(self.doc.createTextNode(token.text))
            self.node_stack[-1].appendChild(span)


if __name__ == '__main__':
    c = Credit(sys.stdin.read())
    f = TextCreditFormatter()
    c.format(f, 10)
    t = f.get_text()
    if t:
        sys.stdout.write(t + '\n')
    else:
        sys.exit('no credit\n')
