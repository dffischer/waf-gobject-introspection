#! /usr/bin/env python

APPNAME = "waf-gobject-introspection"

from waflib.Context import waf_dir
from waflib.Utils import subst_vars

def configure(cnf):
    pass

def build(bld):
    bld.install_files(''.join((
        "${LIBDIR}/",
        waf_dir.rpartition('/')[2],
        "/waflib/extras")),
    'gir.py')
