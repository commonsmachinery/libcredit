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
    const DC = $rdf.Namespace('http://purl.org/dc/elements/1.1/');
    const DCTERMS = $rdf.Namespace('http://purl.org/dc/terms/');
    const CC = $rdf.Namespace('http://creativecommons.org/ns#');
    const XHTML = $rdf.Namespace('http://www.w3.org/1999/xhtml/vocab#');
    const OG = $rdf.Namespace('http://ogp.me/ns#');

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
    
    var getTextProperty = function(kb, subject, predicate) {
        var objs, i;

        objs = kb.each(subject, predicate, null);
        
        for (i = 0; i < objs.length; i++) {
            if (objs[i].termType === 'literal') {
                // TODO: check xml:lang
                return objs[i].value;
            }
            else if (objs[i].termType === 'symbol') {
                return objs[i].uri;
            }
            // TODO: parse rdf:Alt 
        }

        return null;
    };

    var getURLProperty = function(kb, subject, predicate) {
        var obj = kb.any(subject, predicate, null);

        if (!obj) return null;
        
        if (obj.termType === 'symbol') {
            // Assume they know what they're doing and use the URL
            // as-is
            return obj.uri;
        }
        else if (obj.termType === 'literal') {
            // Use this if it seems to be an URL
            return getURL(obj.value);
        }

        return null;
    };

    const urlRE = /^https?:/;

    // Return uri if it can be used as a URL
    var getURL = function(uri) {
        return urlRE.test(uri) ? uri : null;
    }


    //
    // Public API
    //

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
        }

        return text ? text : url;
    };
    libcredit.getLicenseName = getLicenseName;

    /* credit(rdf, [subjectURI])
     *
     * Return a new object that contain the credit information
     * extracted from the RDF metadata, or null if there are no 
     * information.
     *
     * Parameters:
     *
     * - rdf: an rdflib.js Formula instance, or a string of RDF/XML to
     *   parse.
     *
     * - subjectURI: the URI for the subject that the credit should be
     *   constructed for.  If null or omitted, the subject is located by
     *   querying the graph for <> <dc:source> ?subject.
     */

    var credit = function(rdf, subjectURI) {
        var kb;

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
            var srcObjs, i, src;
            
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
                    src = credit(kb, getURL(srcObjs[i].value));
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
            
            titleText = getTextProperty(kb, subject, DC('title'));

            if (!titleText) {
                // Try Open Graph
                titleText = getTextProperty(kb, subject, OG('title'));
            }

            // An Open Graph URL is probably a very good URL to use
            titleURL = getURLProperty(kb, subject, OG('url'));

            if (!titleURL) {
                // If nothing else, try to use the subject URI
                titleURL = getURL(subject.uri);
            }

            if (!titleText) {
                // Fall back on URL
                titleText = titleURL;
            }

            //
            // Attribution
            //

            attribText = getTextProperty(kb, subject, CC('attributionName'));
            attribURL = getURLProperty(kb, subject, CC('attributionURL'));

            if (!attribText) {
                // Try a creator attribute instead
                attribText = (getTextProperty(kb, subject, DC('creator')) ||
                              getTextProperty(kb, subject, DCTERMS('creator')) ||
                              getTextProperty(kb, subject, kb.sym('twitter:creator')));
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

            licenseURL = (getURLProperty(kb, subject, XHTML('license')) ||
                          getURLProperty(kb, subject, DCTERMS('license')) ||
                          getURLProperty(kb, subject, CC('license')));

            if (licenseURL) {
                licenseText = getLicenseName(licenseURL);
            }

            if (!licenseText) {
                // Try to get a license text at least, even if the property isn't a URL
                licenseText = (getTextProperty(kb, subject, DC('rights')) ||
                               getTextProperty(kb, subject, XHTML('license')));
            }

            //
            // Sources
            //
            
            addSources(subject, DC('source'));
            addSources(subject, DCTERMS('source'));
            
            // Did we manage to get anything that can make it into a credit?
            return (titleText || attribText || licenseText || sources.length > 0);
        };


        // TODO: parse RDF
        kb = rdf;

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
                    formatter.addAttrib(attribText, attribURL);
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


    var htmlCreditFormatter = function(document) {
        var that = creditFormatter();


        return that;
    };
    libcredit.htmlCreditFormatter = htmlCreditFormatter;


    
    // Handle node, amd, and global systems
    if (typeof exports !== 'undefined') {
        if (typeof module !== 'undefined' && module.exports) {
            exports = module.exports = libcredit;
        }
        exports.libcredit = libcredit;
    }
    else {
        if (typeof define === 'function' && define.amd) {
            define('libcredit', function() {
                return libcredit;
            });
        }
        // Leak a global regardless of module system
        root['libcredit'] = libcredit;
    }
    
})(this);
