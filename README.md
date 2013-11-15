libcredit
=========

libcredit aims to simplify extracting attribution information for
creative works from RDF metadata and formatting at as human-readable
credit line in various contexts.

RDF metadata
------------

Attribution is retrieved from RDF data by looking for predefined core
properties in the graph. The properties include a subset of Dublin Core,
Creative Commons, XHTML vocabularies and other site-specific properties
(Open Graph, Flickr, etc.).

The process used to extract a credit line from the metadata is
documented here (and you are welcome to contribute thoughts there, as
well as code to this library):
https://github.com/commonsmachinery/credit-metadata-best-practices

Some things described in that process have not yet been implemented,
as indicated by open issues:
https://github.com/commonsmachinery/libcredit/issues?state=open


### CopyRDF addon for Firefox

CopyRDF firefox addon developed by converts RDFa metadata found in various
media hosting platforms to RDF. See the addon's README for a list of tested
websites and usage instructions:

https://github.com/commonsmachinery/copyrdf-addon/blob/master/README.md

Implementation and usage
------------------------

libcredit is currently written for Python and JavaScript. See
README.language.md files for instructions and usage examples for the
libcredit implementations in these languages.

The language-specific implementations are distributed as individual
files, but all are maintained in single repository at github:
https://github.com/commonsmachinery/libcredit


License
-------

Copyright 2013 Commons Machinery http://commonsmachinery.se/

Distributed under an GPLv2 license, please see LICENSE in the top dir.

Contact: dev@commonsmachinery.se
