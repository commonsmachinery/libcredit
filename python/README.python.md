libcredit.py
============

Python module for converting RDF metadata to human-readable strings.
For more information about libcredit and RDF metadata see README in the
toplevel directory.

Installation
------------

You can install libcredit.py using pip:

    pip install libcredit.py

To get the latest development version, clone github repository:

    git clone https://github.com/commonsmachinery/libcredit.git
    cd libcredit
    python setup.py build
    python setup.py install

Installing libcredit with setup.py will install gettext translations to a
system-wide translation directory. On Linux this is `/usr/share/locale`.

Usage
-----

### Loading credit:

    from libcredit import Credit
    credit = Credit(rdf, subject_uri)

where `rdf` is an rdflib Graph instance, or a string of RDF/XML to
parse and `subject_uri` is the URI for the subject that the credit should be
constructed for.  If null or omitted, the subject is located by querying the
graph for `<> <dc:source> ?subject`.

### Formatting credit:

Formatting work is done by credit formatter objects. Libcredit provides a text
formatter and an HTML formatter. After creating a formatter object, call
`credit.format` as follows:

    from libcredit import TextCreditFormatter
    formatter = TextCreditFormatter()
    credit.format(formattter)
    print(formatter.get_text())

    from libcredit import HTMLCreditFormatter
    html_formatter = HTMLCreditFormatter()
    credit.format(html_formattter)
    html = html_formatter.get_root()

Additionally, `credit.format` accepts the following arguments:

    - formatter -- a CreditFormatter to use for output
    - source_depth -- maximum depth for source works traversal
    - i18n -- a gettext class with the desired language (domain "libcredit")
    - subject_uri -- will be used to provide semantic markup in formatters
      which support property semantics.

Writing your own formatters
---------------------------

To create a custom credit formatter, subclass libcredit.CreditFormatter and
implement its methods to fit your requirements. See Python documentation for
CreditFormatter to get the idea of which methods to override.

Running tests
-------------

    python setup.py build
    cd python
    python -m unittest discover

License
-------

Copyright 2013 Commons Machinery http://commonsmachinery.se/

Distributed under an GPLv2 license, please see LICENSE in the top dir.

Contact: dev@commonsmachinery.se
