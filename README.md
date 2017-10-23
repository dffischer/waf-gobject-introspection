# waftool for gobject-introspection

This tool teaches [Waf](http://waf.io) to create and install [GObject Introspection](https://wiki.gnome.org/Projects/GObjectIntrospection) data.


## Usage

[The included example](example/wscript) shows how to use it in a wafscript.

The tool can readily be loaded as long as it is found by the python module import mechanism. This is normally done by prepending the directory it resides in to the PYTHONPATH environment variable.


## Installation

The following command build a waf executable from git including this tool.

```bash
git clone https://github.com/waf-project/waf
cd waf
git clone https://github.com/dffischer/waf-gobject-introspection
./waf-light configure --prefix=/usr \
  build --make-waf --tools='waf-gnome-shell-extension/gir.py'
```
