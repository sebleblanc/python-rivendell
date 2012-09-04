PYTHON=python2.7
MODULE=rivendell
DEST=$(HOME)/.local/lib/$(PYTHON)/site-packages

test:
	cd $(DEST)
	pwd

install:
	tar -cf $(MODULE).tar.gz $(MODULE)/
    
	tar -xvf $(MODULE).tar.gz 

clean:
	find . -name '*.pyo' -or -name '*.pyc' -delete
	rm $(MODULE).tar.gz
