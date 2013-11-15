libcredit.js
============

JavaScript module for converting RDF metadata to human-readable strings.
For more information about libcredit and RDF metadata see README in the
toplevel libcredit directory.

Installation
------------

To get the latest development version, clone github repository:

    git clone https://github.com/commonsmachinery/libcredit.git


### Node.js

You can install libcredit.js using npm:

    npm install libcredit

However, libcredit depends on rdflib, and the current registry version
(0.0.1) is broken.  Until a newer version is uploaded, it is
recommended that you use this rdflib.js:
https://github.com/commonsmachinery/rdflib.js

To simplify things in the meantime, an unofficial 0.0.2 version is
included, which can be included in this way:

   npm install rdflib-0.0.2.tgz 


### RequireJS

libcredit.js can be imported with `require()` or a `define()`
dependency.  This also requires the included unofficial 0.0.2 build to
get RequireJS support in rdflib.js.


Usage
-----

Full documentation is available inline in libcredit.js.

### Loading credit:

    libcredit = require("libcredit");
    ...
    var credit = libcredit.credit(rdf, subjectURI);

where `rdf` is an rdflib.js Formula instance and `subjectURI` is the
URI for the subject that the credit should be constructed for.  If
null or omitted, the subject is located by querying the graph for `<>
<dc:source> ?subject`.

The `rdf` graph can be parsed from RDF/XML with a helper method:

    var doc = new DOMParser().parseFromString(xml, 'text/xml');
    var rdf = libcredit.parseRDFXML(doc);
    var credit = libcredit.credit(rdf);

In Node.js, the package `xmldom` provides a good `DOMParser`.


### Formatting credit:

Formatting work is done by credit formatter objects. Libcredit provides a text
formatter and an HTML formatter. After creating a formatter object, call
`credit.format` as follows:

    // as text
    var formatter = libcredit.textCreditFormatter();
    credit.format(formatter);
    console.log(formatter.getText());

    // as html
    var formatter = libcredit.htmlCreditFormatter(targetDocument);
    credit.format(formatter);
    console.log(formatter.getRoot());

`credit.format` accepts the following arguments:

    - formatter: a formatter object implementing all the methods of
      creditFormatter().
    - sourceDepth: number of levels of sources to get. If omitted
      will default to 1, if falsy will not include any sources.
    - i18n: if provided, this must be a Jed instance for the domain
      `libcredit`.  It will be used to translate the credit
      message. The caller is responsible for loading the correct
      language into it.

### Writing your own formatters

Custom credit formatters should be derived from libcredit.creditFormatter
object. Override the formatter methods as follows:

    var myCreditFormatter = function() {
        var that = libcredit.creditFormatter();

        that.begin = function() { /* ... */ };
        that.end = function() { /* ... */ };
        that.addTitle = function(text, url) { /* ... */ };
        that.addAttrib = function(text, url) { /* ... */ };
        that.addLicense = function(text, url) { /* ... */ };

        return that;
    };

Here's the complete list of formatter methods that you can override:

* `begin()` - called when the formatter begins printing credit for a source
  or the entire work.
* `end()` - called when the formatter is done printing credit for a source
  or the entire work.
* `beginSources(label)` - called before printing the list of sources.
* `endSources()` - called when done printing the list of sources.
* `beginSource()` - called before printing credit for a source and before `begin`.
* `endSource()` - called when done printing credit for a source and after `end`.
* `addTitle(text, url)` - format the title for source or work.
  URL should point to the work's origin and can be null.
* `addAttrib(text, url)` - format the attribution for source or work.
  URL should point to the work's author and can be null.
* `addLicense(text, url)` - format the work's license.
  URL should point to the license and can be null.
* `addText(text)` - add any text (e.g. punctuation) in the current context.


### Miscellaneous functions

* `getLicenseName(url)` - Return a human-readable short name for a license.
  If the URL is unknown, it is returned as-is.

Running tests
-------------

To run the test suite, you need to clone libcredit from github to get
the cross-implementation test cases.

If you didn't install libcredit with npm, make sure you installed the Mocha
test framework and run:

    cd javascript
    make test

License
-------

Copyright 2013 Commons Machinery http://commonsmachinery.se/

Distributed under an GPLv2 license, please see LICENSE in the top dir.

Contact: dev@commonsmachinery.se
