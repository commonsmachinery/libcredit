# -*- coding: utf-8 -*-
# libcredit - module for converting RDF metadata to human-readable strings
#
# Copyright 2013 Commons Machinery http://commonsmachinery.se/
#
# Authors: Artem Popov <artfwo@commonsmachinery.se>
#
# Distributed under an GPLv2 license, please see LICENSE in the top dir.

import sys
import re
import gettext
import rdflib
from xml.dom import minidom

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse


def get_i18n(languages = None):
    if languages is None:
        i18n = gettext.translation('libcredit', sys.prefix + '/share/locale', fallback = True)
    else:
        i18n = gettext.translation('libcredit', sys.prefix + '/share/locale', languages = languages)

    i18n.set_output_charset('utf-8')
    return i18n

# Set up a default translation based on the system locale
_i18n = get_i18n()


def get_license_label(url):
    scheme, netloc, path = urlparse.urlparse(url)[:3]
    label = None
    if netloc == "creativecommons.org":
        if path == "/publicdomain/zero/1.0/":
            label = "Public Domain"
        elif path.startswith("/licenses"):
            path = path.split('/')
            label = "CC %s %s %s" % (
                path[2].upper(),
                path[3],
                "(%s)" % path[4].upper() if len(path) > 5 else "Unported"
            )
    elif netloc == "artlibre.org":
        label = {
            "/licence/lal": "Licence Art Libre",
            "/licence/lal/en": "Free Art License 1.3",
            "/licence/lal/de": "Lizenz Freie Kunst",
            "/licence/lal/es": "Licencia Arte Libre",
            "/licence/lal/pt": "Licença da Arte Livre 1.3",
            "/licence/lal/it": "Licenza Arte Libera",
            "/licence/lal/pl": "Licencja Wolnej Sztuki 1.3",
            "/licence/lal/licence-art-libre-12": "Licence Art Libre 1.2",
        }.get(path)
    return label

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

WORK_QUERY_FORMAT = """
    PREFIX dc: <http://purl.org/dc/elements/1.1/>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX cc: <http://creativecommons.org/ns#>
    PREFIX xhv: <http://www.w3.org/1999/xhtml/vocab#>
    PREFIX twitter: <twitter:>

    SELECT ?title ?attributionURL ?attributionName ?creator ?license
    WHERE {
        OPTIONAL {
            { <%(query_base)s> dc:title ?title } UNION
            { <%(query_base)s> dcterms:title ?title }
        }

        OPTIONAL { <%(query_base)s> cc:attributionURL ?attributionURL }
        OPTIONAL { <%(query_base)s> cc:attributionName ?attributionName }  

        OPTIONAL {
            { <%(query_base)s> dc:creator ?creator } UNION 
            { <%(query_base)s> dcterms:creator ?creator } UNION
            { <%(query_base)s> twitter:creator ?creator }  
        }

        OPTIONAL {
            { <%(query_base)s> xhv:license ?license } UNION 
            { <%(query_base)s> dcterms:license ?license } UNION 
            { <%(query_base)s> cc:license ?license }
        }
    } LIMIT 1
"""

SOURCE_QUERY_FORMAT = """
    PREFIX dc: <http://purl.org/dc/elements/1.1/>
    PREFIX dcterms: <http://purl.org/dc/terms/>

    SELECT ?source {
        { <%(query_base)s> dc:source ?source } UNION
        { <%(query_base)s> dcterms:source ?source }
    }
"""

def normalize(obj):
    if obj is not None:
        return unicode(obj)
    else:
        return None

class Credit:
    """
    Parse attribution data stored in RDF.

    Keyword arguments:
    rdf -- RDF as string
    query_uri -- URI for querying work in the graph
    """
    def __init__(self, rdf, query_uri=None):
        g = rdflib.Graph()
        g.parse(data=rdf)

        if query_uri is None:
            # by the new convention, work is an object of a dc:source predicate for the about="" node
            work_uri = next(g[rdflib.URIRef(''):rdflib.URIRef('http://purl.org/dc/elements/1.1/source'):])
            query_uri = rdflib.term.URIRef(work_uri)
        else:
            query_uri = rdflib.term.URIRef(query_uri)

        query = WORK_QUERY_FORMAT % {"query_base": query_uri}
        result = list(g.query(query))[0]

        self.title = normalize(result.title)
        self.creator = normalize(result.creator)
        self.license = normalize(result.license)
        self.attributionName = normalize(result.attributionName)
        self.attributionURL = normalize(result.attributionURL)

        if self.attributionName is None:
            self.attributionName = self.creator

        # flickr specials
        # flickr_photos:by is used by flickr for the same purpose as attribution URL
        if urlparse.urlparse(str(query_uri))[1] == "www.flickr.com":
            try:
                flickr_by = next(g[query_uri:rdflib.term.URIRef(u'flickr_photos:by')])
            except StopIteration:
                flickr_by = None

            # could we just use /people/XXX/ as the last resort?
            # flickr_by = urlparse.urlparse(str(flickr_by))[2].split('/')[-2]

            if self.attributionName is None:
                self.attributionName = normalize(flickr_by)

            if self.attributionURL is None:
                self.attributionURL = normalize(flickr_by)

        self.sources = []

        query = SOURCE_QUERY_FORMAT % {"query_base": query_uri}
        results = list(g.query(query))

        for r in results:
            s = Credit(rdf, query_uri=r['source'])
            self.sources.append(s)

        # TODO: raise an exception if no credit info is found?
            

    def format(self, formatter, source_depth = 1, i18n = _i18n):
        """
        Create human-readable credit with the given formatter.

        Keyword arguments:
        formatter -- a CreditFormatter to use for output
        source_depth -- maximum depth for source works traversal
        i18n - a gettext class with the desired language (domain "libcredit")
        """

        markup = CREDIT_MARKUP[(
            self.title is not None,
            self.attributionURL is not None or self.attributionName is not None,
            self.license is not None
        )]

        if not markup:
            return # TODO: raise an exception instead?
        
        if i18n:
            markup = i18n.gettext(markup)
            
        formatter.begin()

        for item in ITEM_RE.split(markup):
            if item == '<title>':
                formatter.add_title(self.title, None)
            elif item == '<attrib>':
                formatter.add_attrib(self.attributionName, self.attributionURL)
            elif item == '<license>':
                license_url = self.license
                license_label = get_license_label(license_url)
                if license_label is None:
                    license_label = license_url
                formatter.add_license(license_label, license_url)
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


class CreditFormatter(object):
    def begin(self):
        pass
    def end(self):
        pass
    def begin_sources(self, label=None):
        pass
    def end_sources(self):
        pass
    def begin_source(self):
        pass
    def end_source(self):
        pass
    def add_title(self, text, url):
        pass
    def add_attrib(self, text, url):
        pass
    def add_license(self, text, url):
        pass
    def add_text(self, text):
        pass

class TextCreditFormatter(CreditFormatter):
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
            self.text += " " + label
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
    def __init__(self, document = None):
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
