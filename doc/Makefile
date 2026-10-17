HTML_PARAMS	= style-html.xsl
MAN_PARAMS	= style-man.xsl

XSLTPROC	?= xsltproc

source		= pycrc.xml
targets		= $(source:.xml=.html) $(source:.xml=.1)
generated	= $(targets) docbook.css

all: $(targets)

.PHONY: clean
clean:
	$(RM) $(generated)

.PHONY: check
check:
	xmllint --valid --noout $(source)

%.html: %.xml $(HTML_PARAMS)
	$(XSLTPROC) --nonet -o $@ $(HTML_PARAMS) $<

%.1: %.xml $(MAN_PARAMS)
	$(XSLTPROC) --nonet -o $@ $(MAN_PARAMS) $<

%.txt: %.html
	links -dump -no-numbering -no-references $< > $@
