(function (libcredit) {

    //
    // Helper functions
    //

    // Test credit by calling func to perform the checks on the credit
    // object
    
    var testCredit = function(filename, sourceURI, func) {
	it('credit for ' + filename, function() {
	    var turtle, out, kb, credit, formatter;

	    turtle = fs.readFileSync('../testcases/' + filename + '.ttl', 'utf-8');
	    
	    kb = new $rdf.IndexedFormula();

	    // A bug in rdflib means that we must pass in a base URI,
	    // '' triggers an error
	    $rdf.parse(turtle, kb, 'urn:base', 'text/turtle');

	    // So because of that bug, we have to specify the source URI
	    credit = libcredit.credit(kb, sourceURI);
	    func(credit);
	});
    };

    // Helper formatter to generate the test output string
    var testCreditFormatter = function() {
	var that = libcredit.creditFormatter();

	var add_line = function(type, text, url) {
	    that.output.push(type + ' "' +
			     (text ? text : '') + '" <' +
			     (url ? url : '') + '>');
	};

	that.begin_credit = function() {
	    that.output = [];
	};
	
	that.add_title = function(text, url) {
	    add_line('title', text, url);
	};

	that.add_attrib = function(text, url) {
	    add_line('attrib', text, url);
	};

	that.add_license = function(text, url) {
	    add_line('license', text, url);
	};

	// TODO: sources

	return that;
    };

    // Test credit by comparing the generated credit with the expected output
    var testCreditOutput = function(filename, sourceURI) {
	var out = fs.readFileSync('../testcases/' + filename + '.out', 'utf-8');
	var expected = out.split('\n');
	var f = testCreditFormatter();

	testCredit(filename, sourceURI, function(credit) {
	    var a, e;
	    var actual;
	    
	    expect( credit ).to.not.be( null );

	    credit.format(f);
	    expect( f.output ).to.be.an( 'array' );

	    actual = f.output;
	    actual.sort();
	    expected.sort();

	    for (a = e = 0; a < actual.length && e < expected.length; ) {
		// Ignore empty lines in expected to simplify things
		if (!expected[e]) {
		    e++;
		}
		else {
		    expect( actual[a] ).to.be( expected[e] );
		    a++; e++;
		}
	    }

	    if (a < actual.length) {
		// Bug in expect.js means we need to pass a function, not just the string
		expect().fail(function() { return 'unexpected output: ' + actual[a]; });
	    }

	    // Strip trailing empty expected lines
	    while (e < expected.length && !expected[e]) {
		e++;
	    }

	    if (e < expected.length) {
		expect().fail(function() { return 'missing expected output: ' + expected[e]; });
	    }
	});
    };


    //
    // Test cases
    //

    describe("Property Checks", function () {
	it("should exist", function () {
	    expect( libcredit ).to.be.ok();
	});
	
	it("should have public functions", function () {
	    expect( libcredit.credit ).to.be.a('function');
	    expect( libcredit.creditFormatter ).to.be.a('function');
	    expect( libcredit.textCreditFormatter ).to.be.a('function');
	    expect( libcredit.htmlCreditFormatter ).to.be.a('function');
	});
    });

    describe('Pure Dublin Core', function () {

	testCredit('nothing', 'urn:src', function (credit) {
	    expect( credit ).to.be( null );
	});

	testCreditOutput('dc-title-text', 'urn:src');
    });

})(libcredit);
