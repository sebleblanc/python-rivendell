python-rivendell
================

Rivendell module for Python. Rivendell is an open-source radio automation suite.

Requirements
---

This module requires a few things:

(NOTE: this list is work-in-progress and is most likely incomplete)

* A recent installation of Rivendell and its dependencies (MySQL, Apache, ...)
Optional:
* libebur128 (needed for the "loudness" normalization utility)

Usage
---

To use it, the module must be imported first:

    import rivendell

Initialize a host:

    host = rivendell.Host()

To get a cart:

    cart = host.get_cart(cart_number) # integer value

To access the cuts of a cart:

    cut = cart.cuts[index]

How many cuts in a cart?

    print len(cart.cuts)

Get loudness of a cut (this requires `libebur128`)

    cut.get_loudness()

Set playback gain of a cut (in hundredths of decibels):

    cut.set_gain(400)


More features coming later!

Utilities
---

There is a utility provided with the package, named `utils/normalize.py`, 
which can be used to normalize the audio level (loudness) of multiple carts in a row.
It can either work in a destructive (edit cuts in place, currently not implemented) or non-destructive way (modify
play_gain value in database).

Notes
---
Right now, python-rivendell uses a hacked=together means of accessing the database. Eventually
it will be reimplemented using some ORM engine (likely SqlAlchemy).
