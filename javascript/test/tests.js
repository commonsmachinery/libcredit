(function (libcredit) {

    var testCredit = function(filename, func) {
	it('credit for ' + filename, function() {
	    var str, kb, credit, formatter;

	    str = fs.readFileSync('../test_input/' + filename + '.ttl', 'utf-8');
	    
	    kb = new $rdf.IndexedFormula();

	    // A bug in rdflib means that we must pass in a base URI,
	    // '' triggers an error
	    $rdf.parse(str, kb, 'urn:base', 'text/turtle');

	    // So because of that bug, we have to specify the source URI
	    credit = libcredit.credit(kb, 'urn:src');
	    func(credit);
	});
    };

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

	testCredit('nothing', function (credit) {
	    expect( credit ).to.be( null );
	});

	testCredit('dc-title-text', function (credit) {
	    expect( credit ).to.not.be( null );
	    expect( credit.getTitleText()	).to.be( 'a title' );
	    expect( credit.getTitleURL()	).to.be( null );
	    expect( credit.getAttribText()	).to.be( null );
	    expect( credit.getAttribURL()	).to.be( null );
	    expect( credit.getLicenseText()	).to.be( null );
	    expect( credit.getLicenseURL()	).to.be( null );
	    expect( credit.getSources().length	).to.be( 0 );
	});
    });

})(libcredit);
