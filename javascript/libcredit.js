// -*- coding: utf-8 -*-
// libcredit - module for converting RDF metadata to human-readable strings
//
// Copyright 2013 Commons Machinery http://commonsmachinery.se/
//
// Authors: Peter Liljenberg <peter@commonsmachinery.se>
//
// Distributed under an GPLv2 license, please see LICENSE in the top dir.


(function (root, undef) {

    var libcredit = {};

    // Namespace used in the code
    var DC;
    var DCTERMS;
    var CC;
    var XHTML;
    var OG;
    var RDF;

    // Keep our own reference to rdflib's $rdf in a env-independent way
    var rdflib;

    var rdflibSetup = function(r) {
        rdflib = r;

        DC = rdflib.Namespace('http://purl.org/dc/elements/1.1/');
        DCTERMS = rdflib.Namespace('http://purl.org/dc/terms/');
        CC = rdflib.Namespace('http://creativecommons.org/ns#');
        XHTML = rdflib.Namespace('http://www.w3.org/1999/xhtml/vocab#');
        OG = rdflib.Namespace('http://ogp.me/ns#');
        RDF = rdflib.Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#');
    };

    var getCreditLine = function(hasTitle, hasAttrib, hasLicense)
    {
        if (hasTitle) {
            if (hasAttrib) {
                return (hasLicense ?
                        '<title> by <attrib> (<license>).' :
                        '<title> by <attrib>.');
            }
            else {
                return (hasLicense ?
                        '<title> (<license>).' :
                        '<title>.');
            }
        }
        else {
            if (hasAttrib) {
                return (hasLicense ?
                        'Credit: <attrib> (<license>).' :
                        'Credit: <attrib>.');
            }
            else {
                return (hasLicense ?
                        'License: <license>.' :
                        null);
            }
        }
    };


    const ccLicenseURL = /^https?:\/\/creativecommons.org\/licenses\/([-a-z]+)\/([0-9.]+)\/(?:([a-z]+)\/)?(?:deed\..*)?$/;

    const ccPublicDomainURL = /^https?:\/\/creativecommons.org\/publicdomain\/([a-z]+)\/([0-9.]+)\/(?:deed\..*)?$/;

    const freeArtLicenseURL = /^https?:\/\/artlibre.org\/licence\/lal(?:\/([-a-z0-9]+))?$/;

    var getPropertyNew = function(kb, subject, predicates, returnSeq) {
        returnSeq = returnSeq || false;
        var result = [];

        if (!Array.isArray(predicates)) {
            predicates = [predicates];
        }

        for (var p = 0; p < predicates.length; p++) {
            var predicate = predicates[p];
            var objs = kb.each(subject, predicate, null);
            //result = null;

            for (var i = 0; i < objs.length; i++) {
                if (objs[i].termType === 'literal') {
                    // TODO: check xml:lang
                    result.push(objs[i].value);
                } else if (objs[i].termType === 'symbol') {
                    result.push(objs[i].uri);
                } else if (objs[i].termType === 'bnode') {
                    result = result.concat(parseContainer(kb, objs[i]));
                }
            }
        }

        if (returnSeq)
            return result.length > 0 ? result : null;
        else
            return result[0];
    };

    var parseContainer = function(kb, subject) {
        result = [];
        if ( kb.holds(subject, RDF('type'), RDF('Seq')) ||
             kb.holds(subject, RDF('type'), RDF('Bag')) ||
             kb.holds(subject, RDF('type'), RDF('Alt')) ) {
            predicates = kb.each(subject);
            contents = {};
            for (var p = 0; p < predicates.length; p++) {
                if ( predicates[p].value.indexOf("http://www.w3.org/1999/02/22-rdf-syntax-ns#_") == 0) {
                    contents[predicates[p].value] = kb.any(subject, predicates[p]).value;
                }
            }
            keys = [];
            for (var key in contents) {
                keys.push(key);
            }
            // doesn't work. does rdflib respect the order of rdf:_n elements when parsing?
            keys.sort();

            if (kb.holds(subject, RDF('type'), RDF('Alt'))) {
                //result = contents[keys[0]];
                result.push(contents[keys[0]]);
            } else {
                result = [];
                for (var k = 0; k < keys.length; k++) {
                    result.push(contents[keys[k]]);
                }
            }
        }
        return result;
    }

    const urlRE = /^https?:/;

    // Return uri if it can be used as a URL
    var getURL = function(uri) {
        return urlRE.test(uri) ? uri : null;
    }


    //
    // Public API
    //

    /* parseRDFXML(doc, [baseURI])
     *
     * Parse an RDF/XML document into a rdflib.js Formula object.
     *
     * Parameters:
     *
     * - xml: a DOM Document parsed with DOMParser or similar class
     * - baseURI: the document base URI, or '' if omitted
     **/
    var parseRDFXML = function(doc, baseURI) {
        var kb, parser;
        kb = new rdflib.IndexedFormula();
        parser = new rdflib.RDFParser(kb);

        if (!baseURI) {
            baseURI = '';
        }

        parser.parse(doc, baseURI, kb.sym(baseURI));
        return kb;
    };
    libcredit.parseRDFXML = parseRDFXML;

    /* getLicenseName(url)
     *
     * Return a human-readable short name for a license.
     * If the URL is unknown, it is returned as-is.
     *
     * Parameters:
     *
     * - url: the license URL
     **/
    var getLicenseName = function(url) {
        var m, text;

        m = url.match(ccLicenseURL);
        if (m) {
            text = 'CC ';
            text += m[1].toUpperCase();
            text += ' ';
            text += m[2];
            text += m[3] ? ' (' + m[3].toUpperCase() + ')' : ' Unported';

            return text;
        }

        m = url.match(ccPublicDomainURL);
        if (m) {
            switch (m[1]) {
            case 'zero':
                return 'CC0 ' + m[2];

            case 'mark':
                return 'public domain';
            }
        }

        m = url.match(freeArtLicenseURL);
        if (m) {
            text = 'Free Art License ';
            text += (m[1] === 'licence-art-libre-12' ? '1.2' : '1.3');
            return text;
        }

        return url;
    };
    libcredit.getLicenseName = getLicenseName;

    /* credit(kb, [subjectURI])
     *
     * Return a new object that contain the credit information
     * extracted from the RDF metadata, or null if there are no
     * information.
     *
     * Parameters:
     *
     * - kb: an rdflib.js Formula instance, e.g. returned from
     *   parseRDFXML().
     *
     * - subjectURI: the URI for the subject that the credit should be
     *   constructed for.  If null or omitted, the subject is located by
     *   querying the graph for <> <dc:source> ?subject.
     */

    var credit = function(kb, subjectURI) {
        var titleText = null;
        var titleURL = null;
        var attribText = null;
        var attribURL = null;
        var licenseText = null;
        var licenseURL = null;
        var sources = [];

        // Make scope a little cleaner by putting the parsing into
        // it's own functions

        var addSources = function(subject, predicate) {
            var srcObjs, i, src, url;

            srcObjs = kb.each(subject, predicate);

            for (i = 0; i < srcObjs.length; i++) {
                src = null;

                switch (srcObjs[i].termType) {
                case 'symbol':
                case 'bnode':
                    src = credit(kb, srcObjs[i]);
                    break;

                case 'literal':
                    // Accept URLs in literals too
                    url = getURL(srcObjs[i].value);
                    if (url) {
                        src = credit(kb, url);
                    }
                    break;
                }

                if (src) {
                    sources.push(src);
                }
            }
        };

        var parse = function() {
            var mainSource, subject;

            if (subjectURI === null || subjectURI === undefined) {
                // Locate using <> <dc:source> ?, which is how the
                // Copy RDFa firefox addon indicates the original of
                // the copied object

                mainSource = kb.any(kb.sym(''), DC('source'));

                if (mainSource && mainSource.uri) {
                    subject = mainSource;
                }
                else {
                    // No clue what the source might be, so give up
                    return false;
                }
            }
            else if (typeof subjectURI === 'string') {
                subject = kb.sym(subjectURI);
            }
            else {
                // Assume this is already a symbol in the KB
                subject = subjectURI;
            }

            //
            // Title
            //

            titleText = getPropertyNew(kb, subject, [
                DC('title'),
                DCTERMS('title'),
                OG('title')
            ]);

            // An Open Graph URL is probably a very good URL to use
            titleURL = getURL(getPropertyNew(kb, subject, OG('url')));

            if (!titleURL) {
                // If nothing else, try to use the subject URI
                titleURL = getURL(subject.uri);
            }

            if (!titleText) {
                // Fall back on URL
                titleText = titleURL;
            }
            //titleURL = "http://example.com";

            //
            // Attribution
            //

            attribText = getPropertyNew(kb, subject, CC('attributionName'));
            attribURL = getPropertyNew(kb, subject, CC('attributionURL'));

            if (!attribText) {
                // Try a creator attribute instead
                attribText = getPropertyNew(kb, subject, [
                    DC('creator'),
                    DCTERMS('creator')
                ], true);
                if (attribText && attribText.length == 1)
                    attribText = attribText[0];
            }

            if (!attribText) {
                attribText = getPropertyNew(kb, subject, kb.sym('twitter:creator'));
            }

            // Special case for flickr
            if (!attribText && /^https?:\/\/www.flickr.com/.test(subject.uri)) {
                attribText = getPropertyNew(kb, subject, kb.sym('flickr_photos:by'));
            }

            if (attribText && !attribURL) {
                // Text creator might be a URL
                attribURL = getURL(attribText);
            }

            if (!attribText) {
                // Fall back on URL
                attribText = attribURL;
            }

            //
            // License
            //

            licenseURL = getURL(getPropertyNew(kb, subject, [
                XHTML('license'),
                DCTERMS('license'),
                CC('license')
            ]));

            if (licenseURL) {
                licenseText = getLicenseName(licenseURL);
            }

            if (!licenseText) {
                // Try to get a license text at least, even if the property isn't a URL
                licenseText = getPropertyNew(kb, subject, [
                    DC('rights'),
                    XHTML('license')
                ]);
            }
            //
            // Sources
            //

            addSources(subject, DC('source'));
            addSources(subject, DCTERMS('source'));

            // Did we manage to get anything that can make it into a credit?
            return (titleText || attribText || licenseText || sources.length > 0);
        };

        if (!parse()) {
            return null;
        }

        var that = {};

        /* credit.getTitleText():
         * credit.getTitleURL():
         * credit.getAttribText():
         * credit.getAttribURL():
         * credit.getLicenseText():
         * credit.getLicenseURL():
         *
         * Property getters returning a string or null.
         */

        /* credit.getSources():
         *
         * Property getter returning an array of credit objects:
         */

        that.getTitleText = function() { return titleText; };
        that.getTitleURL = function() { return titleURL; };
        that.getAttribText = function() { return attribText; };
        that.getAttribURL = function() { return attribURL; };
        that.getLicenseText = function() { return licenseText; };
        that.getLicenseURL = function() { return licenseURL; };
        that.getSources = function() { return sources.slice(0); };


    /* credit.format(formatter, [sourceDepth, [i18n]])
     *
     * Use a formatter to generate a credit based on the metadata in
     * the credit object.
     *
     * Parameters:
     *
     * - formatter: a formatter object, typically derived from
     *   creditFormatter().
     *
     * - sourceDepth: number of levels of sources to get. If omitted
     *   will default to 1, if falsy will not include any sources.
     *
     * - i18n: if provided, this must be a Jed instance for the domain
     *   "libcredit".  It will be used to translate the credit
     *   message. The caller is responsible for loading the correct
     *   language into it.
     */

        that.format = function(formatter, sourceDepth, i18n) {
            var re = /<[a-z]+>/g;
            var creditLine;
            var textStart, textEnd;
            var match;
            var item;
            var i;
            var srcLabel;

            if (sourceDepth === undefined)
                sourceDepth = 1;

            creditLine = getCreditLine(!!titleText, !!attribText, !!licenseText);

            if (i18n) {
                creditLine = (i18n
                              .translate(creditLine)
                              .onDomain('libcredit')
                              .fetch());
            }

            formatter.begin();

            // Split credit line into text and credit items
            textStart = 0;
            while ((match = re.exec(creditLine)) != null) {
                item = match[0];
                textEnd = re.lastIndex - item.length;

                // Add any preceeding plain text
                if (textStart < textEnd) {
                    formatter.addText(creditLine.slice(textStart, textEnd));
                }
                textStart = re.lastIndex;

                switch (item) {
                case '<title>':
                    formatter.addTitle(titleText, titleURL);
                    break;

                case '<attrib>':
                    if (Array.isArray(attribText)) {
                        for (var a = 0; a < attribText.length; a++) {
                            var attrib = attribText[a];
                            formatter.addAttrib(attrib, null);
                            if (a + 1 < attribText.length)
                                formatter.addText(", ");
                        }
                    } else {
                        formatter.addAttrib(attribText, attribURL);
                    }
                    break;

                case '<license>':
                    formatter.addLicense(licenseText, licenseURL);
                    break;

                default:
                    throw 'unexpected credit item: ' + item;
                }
            }

            // Add any trailing text
            if (textStart < creditLine.length) {
                formatter.addText(creditLine.slice(textStart));
            }


            //
            // Add sources
            //

            if (sources.length > 0 && sourceDepth && sourceDepth > 0) {
                if (i18n) {
                    srcLabel = (i18n
                                .translate('Source:')
                                .onDomain('libcredit')
                                .ifPlural(sources.length, 'Sources:')
                                .fetch());
                }
                else {
                    srcLabel = sources.length < 2 ? 'Source:' : 'Sources:';
                };

                formatter.beginSources(srcLabel);

                for (i = 0; i < sources.length; i++) {
                    formatter.beginSource();
                    sources[i].format(formatter, sourceDepth - 1, i18n);
                    formatter.endSource();
                }

                formatter.endSources();
            }

            formatter.end();
        };

        return that;
    };
    libcredit.credit = credit;


    /* creditFormatter()
     *
     * Return a base credit formatter (that doesn't do anything).
     * Override methods in this as applicable to the desired format.
     *
     * Methods:
     *
     * begin() - called when the formatter begins printing credit for a source
     *     or the entire work.
     *
     * end() - called when the formatter is done printing credit for a source
     *     or the entire work.
     *
     * beginSources(label) - called before printing the list of sources.
     *
     * endSources() - called when done printing the list of sources.
     *
     * beginSource() - called before printing credit for a source and before begin.
     *
     * endSource() - called when done printing credit for a source and after end.
     *
     * addTitle(text, url) - format the title for source or work.
     *     URL should point to the work's origin and can be null.
     *
     * addAttrib(text, url) - format the attribution for source or work.
     *     URL should point to the work's author and can be null.
     *
     * addLicense(text, url) - format the work's license.
     *     URL should point to the license and can be null.
     *
     * addText(text) - add any text (e.g. punctuation) in the current context.
     */
    var creditFormatter = function() {
        var that = {};

        that.begin = function() {};
        that.end = function() {};
        that.beginSources = function(label) {};
        that.endSources = function() {};
        that.beginSource = function() {};
        that.endSource = function() {};
        that.addTitle = function(text, url) {};
        that.addAttrib = function(text, url) {};
        that.addLicense = function(text, url) {};
        that.addText = function(text) {};

        return that;
    };
    libcredit.creditFormatter = creditFormatter;

    /** textCreditFormatter()
     *
     * Return a formatter that generates a plain text credit.
     *
     * Object method:
     *
     * getText(): return the generated text.
     */
    var textCreditFormatter = function() {
        var that = creditFormatter();

        var creditText = '';
        var sourceDepth = 0;

        that.begin = function() {
            var i;
            if (sourceDepth > 0) {
                creditText += '\n';

                for (i = 0; i < sourceDepth; i++) {
                    creditText += '    ';
                }

                creditText += '* ';
            }
        };

        that.beginSources = function(label) {
            if (creditText) creditText += ' ';
            creditText += label;

            sourceDepth++;
        };

        that.endSources = function() {
            sourceDepth--;
        };

        that.addTitle = function(text, url) {
            creditText += text;
        };

        that.addAttrib = function(text, url) {
            creditText += text;
        };

        that.addLicense = function(text, url) {
            creditText += text;
        };

        that.addText = function(text) {
            creditText += text;
        };

        that.getText = function() {
            return creditText;
        };

        return that;
    };
    libcredit.textCreditFormatter = textCreditFormatter;


    /** htmlCreditFormatter(document)
     *
     * Return a formatter that generates an HTML credit.
     *
     * Parameters:
     *
     * - document: the target HTML document, will be used to create
     *   the HTML elements for the credit.
     *
     * Object method:
     *
     * getRoot(): return the root element of the generated credit.
     */
    var htmlCreditFormatter = function(document) {
        var that = creditFormatter();
        var root, current;
        var nodeStack = [];

        root = current = document.createElement('div');

        var startElement = function(type) {
            var node = document.createElement(type);
            nodeStack.push(current);
            current.appendChild(node);
            current = node;
        };

        var endElement = function() {
            current = nodeStack.pop();
        };

        var addText = function(text) {
            var node = document.createTextNode(text);
            current.appendChild(node);
        };

        that.begin = function() {
            startElement('p');
        };

        that.end = function() {
            endElement();
        };

        that.beginSources = function(label) {
            if (label) {
                addText(' ' + label);
            }

            startElement('ul');
        };

        that.endSources = function() {
            endElement();
        };

        that.beginSource = function() {
            startElement('li');
        };

        that.endSource = function() {
            endElement();
        };

        that.addTitle = that.addAttrib = that.addLicense = function(text, url) {
            if (url) {
                startElement('a');
                current.setAttribute('href', url);
                addText(text);
                endElement();
            }
            else {
                addText(text);
            }
        };

        that.addText = addText;

        that.getRoot = function() {
            return root;
        };

        return that;
    };
    libcredit.htmlCreditFormatter = htmlCreditFormatter;



    // Handle node, amd, and global systems
    if (typeof exports !== 'undefined') {
        if (typeof module !== 'undefined' && module.exports) {
            exports = module.exports = libcredit;
        }
        exports.libcredit = libcredit;
        rdflibSetup(require('rdflib'));
    }
    else {
        if (typeof define === 'function' && define.amd) {
            define('libcredit', ['rdflib'], function(rdflib) {
                rdflibSetup(rdflib);
                return libcredit;
            });
        }
        else {
            // Assume that rdflib has been loaded for us
            rdflibSetup($rdf);
        }

        // Leak a global regardless of module system
        root['libcredit'] = libcredit;
    }

})(this);
