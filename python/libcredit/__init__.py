# libcredit - module for converting RDF metadata to human-readable strings
#
# Copyright 2013 Commons Machinery http://commonsmachinery.se/
#
# Authors: Artem Popov <artfwo@commonsmachinery.se>
#
# Distributed under an GPLv2 license, please see LICENSE in the top dir.

import sys
import gettext
import RDF
from xml.dom.minidom import getDOMImplementation

try:
    t = gettext.translation('libcredit', sys.prefix + '/share/locale')
    _ = t.ugettext
except IOError:
    t = gettext.NullTranslations()
    _ = t.ugettext

license_labels = {
    "http://creativecommons.org/licenses/by/3.0/": "CC BY 3.0",
    "http://creativecommons.org/licenses/by-nc/3.0/": "CC BY-NC 3.0",
    "http://creativecommons.org/licenses/by-nc-nd/3.0/": "CC BY-NC-ND 3.0",
    "http://creativecommons.org/licenses/by-nc-sa/3.0/": "CC BY-NC-SA 3.0",
    "http://creativecommons.org/licenses/by-nd/3.0/": "CC BY-ND 3.0",
    "http://creativecommons.org/licenses/by-sa/3.0/": "CC BY-SA 3.0",
}

WORK_QUERY_FORMAT = """
    PREFIX dc: <http://purl.org/dc/elements/1.1/>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX cc: <http://creativecommons.org/ns#>
    PREFIX xhv: <http://www.w3.org/1999/xhtml/vocab#>

    SELECT ?buggy_optional_value ?title ?attributionURL ?attributionName ?creator ?license
    WHERE {
        OPTIONAL { <%(query_base)s> a ?buggy_optional_value }

        OPTIONAL {
            { <%(query_base)s> dc:title ?title } UNION
            { <%(query_base)s> dcterms:title ?title }
        }

        OPTIONAL { <%(query_base)s> cc:attributionURL ?attributionURL }
        OPTIONAL { <%(query_base)s> cc:attributionName ?attributionName }  

        OPTIONAL {
            { <%(query_base)s> dc:creator ?creator } UNION 
            { <%(query_base)s> dcterms:creator ?creator }
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

class Credit:
    """
    Parse attribution data stored in RDF.

    Keyword arguments:
    rdf -- RDF as string
    base_uri -- base URI, if known, to keep Redland happy
    query_uri -- URI for query; used to instantiate source objects
    """
    def __init__(self, rdf, base_uri="about:this", query_uri=None):
        parser = RDF.Parser()
        model = RDF.Model()
        parser.parse_string_into_model(model, rdf, base_uri)

        if query_uri is None:
            query_uri = base_uri

        query = RDF.Query(WORK_QUERY_FORMAT % {"query_base": query_uri})
        result = query.execute(model).next()

        self.title = result['title']
        self.creator = result['creator']
        self.license = result['license']
        self.attributionName = result['attributionName']
        self.attributionURL = result['attributionURL']

        self.sources = []

        query = RDF.Query(SOURCE_QUERY_FORMAT % {"query_base": query_uri})
        results = query.execute(model)

        for r in results:
            s = Credit(rdf, query_uri = r['source'].uri)
            self.sources.append(s)

    def write(self, writer):
        if self.title:
            string, language, datatype = self.title.literal
            writer.add_text(string)
        else:
            writer.add_text(_("Untitled work"))

        if self.attributionURL:
            if self.attributionName:
                writer.add_text(_(" by "))

                string, language, datatype = self.attributionName.literal
                url = str(self.attributionURL.uri)
                writer.add_url(string, url)
            elif self.creator:
                writer.add_text(_(" by "))

                string, language, datatype = self.creator.literal
                url = str(self.attributionURL.uri)
                writer.add_url(string, url)
        else:
            if self.attributionName:
                writer.add_text(_(" by "))

                string, language, datatype = self.attributionName.literal
                writer.add_text(string)
            elif self.creator:
                writer.add_text(_(" by "))

                string, language, datatype = self.creator.literal
                writer.add_text(string)

        writer.add_text(".")

        if self.license:
            writer.add_text(_(" Licensed under "))

            if self.license.is_literal():
                string, language, datatype = self.license.literal
                writer.add_text(string)
            elif self.license.is_resource():
                url = str(self.license.uri)
                if url in license_labels:
                    writer.add_url(license_labels[url], url)
                else:
                    writer.add_url(url, url)

            writer.add_text(_(" license"))
            writer.add_text(".")

        if self.sources:
            writer.write_sources(self.sources)

        writer.close_credit()


class CreditWriter(object):
    """
    Abstract class that defines interface for attribution writers.
    """
    def add_text(self, text):
        pass

    def add_url(self, text, url=None):
        pass

    def close_credit(self):
        pass

    def write_sources(self, sources):
        pass

class TextCreditWriter(CreditWriter):
    """
    Credit writer that writes to string retrievable with TextCreditWriter.get_text()
    """
    def __init__(self):
        self.output = u""

    def add_text(self, text):
        self.output = self.output + text

    def add_url(self, text, url=None):
        self.add_text(text)

    def close_credit(self):
        pass

    def write_sources(self, sources):
        self.add_text(_(" Source works:"))
        for s in sources:
            source_writer = TextCreditWriter()
            s.write(source_writer)
            self.add_text("\n* ")
            self.add_text(source_writer.get_text())

    def get_text(self):
        return self.output

class HTMLCreditWriter(CreditWriter):
    """
    Credit writer that writes to HTML.
    """
    pass
