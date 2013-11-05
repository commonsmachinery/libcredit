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

    //
    // Public API
    //

    /* credit(rdf, [subjectURI])
     *
     * Return a new object that can format
     * credit strings using RDF metadata.  The RDF graph is parsed at
     * construction time.
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
	var that = {};

    /* credit.format(formatter, [i18n])
     *
     * Use a formatter to generate a credit based on the metadata in
     * the credit object.
     *
     * Parameters:
     *
     * - formatter: a formatter object, typically derived from
     *   creditFormatter().
     *
     * - i18n: if provided, this must be a Jed instance for the domain
     *   "libcredit".  It will be used to translate the credit
     *   message. The caller is responsible for loading the correct
     *   language into it.
     */

	that.format = function(formatter) {
	    
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
	that.begin_sources = function(label) {};
	that.end_sources = function() {};
	that.begin_source = function() {};
	that.end_source = function() {};
	that.add_title = function(text, url) {};
	that.add_attrib = function(text, url) {};
	that.add_license = function(text, url) {};
	that.add_text = function(text) {};

	return that;
    };
    libcredit.creditFormatter = creditFormatter;


    /* objectCreditFormatter()
     *
     * Collect the credit information into a object, rather than
     * generating a human-consumable credit message.
     */  
    var objectCreditFormatter = function() {
	var that = creditFormatter();

	var current = null;
	var sourceStack = null;

	var emptyCredit = function() {
	    return {
		titleText: null,
		titleURL: null,
		attribText: null,
		attribURL: null,
		licenseText: null,
		licenseURI: null,
		sources: []
	    };
	};
		
	that.getCredit = function() {
	    return current;
	};

	that.begin = function() {
	    current = emptyCredit();
	    sourceStack = [];
	};

	that.begin_source = function() {
	    var source = emptyCredit();
	    current.sources.push(source);
	    sourceStack.push(current);
	    current = source;
	};

	that.end_source = function() {
	    current = sourceStack.pop();
	};

	that.add_title = function(text, url) {
	    current.titleText = text;
	    current.titleURL = url;
	};

	that.add_attrib = function(text, url) {
	    current.attribText = text;
	    current.attribURL = url;
	};
	    
	that.add_license = function(text, url) {
	    current.licenseText = text;
	    current.licenseURL = url;
	};

	return that;
    };
    libcredit.objectCreditFormatter = objectCreditFormatter;

    var textCreditFormatter = function() {
	var that = creditFormatter();


	return that;
    };
    libcredit.textCreditFormatter = textCreditFormatter;


    var htmlCreditFormatter = function() {
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
