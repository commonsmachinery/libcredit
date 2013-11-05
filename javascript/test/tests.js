(function (libcredit) {

    var testCredit = function(filename, func) {
	it('credits ' + filename, function() {
	    var str, kb, credit, formatter;

	    str = fs.readFileSync('../test_input/' + filename + '.ttl', 'utf-8');
	    
	    kb = new $rdf.IndexedFormula();
	    $rdf.parse(str, kb, 'urn:test', 'text/turtle');

	    credit = libcredit.credit(kb);
	    formatter = libcredit.objectCreditFormatter();
	    credit.format(formatter);
	    
	    func(formatter.getCredit());
	});
    };

    describe("Property Checks", function () {
	it("should exist", function () {
	    expect( libcredit ).to.be.ok();
	});
	
	it("should have public functions", function () {
	    expect( libcredit.credit ).to.be.a('function');
	    expect( libcredit.creditFormatter ).to.be.a('function');
	    expect( libcredit.objectCreditFormatter ).to.be.a('function');
	    expect( libcredit.textCreditFormatter ).to.be.a('function');
	    expect( libcredit.htmlCreditFormatter ).to.be.a('function');
	});
    });

    describe('Pure Dublin Core', function () {

	testCredit('nothing', function (credit) {
	    expect( credit ).to.be( null );
	});

    });

})(libcredit);
