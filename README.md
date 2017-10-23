# waftool for gobject-introspection

This tool teaches [Waf](http://waf.io) to create and install [GObject Introspection](https://wiki.gnome.org/Projects/GObjectIntrospection) data.


## Usage

[The included example](example/wscript) shows how to use it in a wafscript.

The tool can readily be loaded as long as it is found by the python module import mechanism. This is normally done by prepending the directory it resides in to the PYTHONPATH environment variable.
