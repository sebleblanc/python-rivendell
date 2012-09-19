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

Utilities
---

There is a utility provided with the package, named "utils/normalize.py", 
which can be used to normalize the audio level (loudness) of multiple carts in a row.
It can either work in a destructive (edit cuts in place) or non-destructive way (modify
play_gain value in database).
