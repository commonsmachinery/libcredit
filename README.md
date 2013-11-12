libcredit
=========

libcredit aims to simplify extracting attribution information for creative
works from RDF metadata and formatting at as human-readable text in various
contexts.

RDF metadata
------------

Attribution is retrieved from RDF data by looking for predefined core
properties in the graph. The properties include a subset of Dublin Core,
Creative Commons, XHTML vocabularies and other site-specific properties
(Open Graph, Flickr, etc.).

RDF metadata is not very widespread. A list of sources that have been tested
to work with libcredit is provided below:

### CopyRDF addon for Firefox

CopyRDF firefox addon developed by converts RDFa metadata found in various
media hosting platforms to RDF. See the addon's README for a list of tested
websites and usage instructions:

https://github.com/commonsmachinery/copyrdf-addon/blob/master/README.md

Implementation and usage
------------------------

libcredit is currently written for Python and JavaScript. See README files
in python/ and javascript/ subdirectories for instructions and usage examples
for these languages.

License
-------

Copyright 2013 Commons Machinery http://commonsmachinery.se/

Distributed under an GPLv2 license, please see LICENSE in the top dir.

Contact: dev@commonsmachinery.se
