#!/usr/bin/python

"""
Create and install GObject Introspection data.

The functions herein center around a feature called 'gir' which scans source
files for GObject Introspection data and compiles a Typelib.

    def configure(cnf):
        cnf.load("gir")

    def build(bld):
        bld(features="c cshlib",  # library compilation
                source="object.c", target="object", use="GLIB2")
        bld(features="gir", namespace="Object",
                lib="object",  # library to introspect
                scan="object.h",  # header files to scan
                version=1)  # defaults to 0
"""

from waflib.TaskGen import feature
from waflib.Task import Task
from waflib.Errors import WafError

def configure(cnf):
    cnf.find_program("g-ir-scanner")
    env = cnf.env
    env.GIRLIB_T = '-l%s'      # template passing library to scanner
    env.GIRPATH_T = '-L%s'  # template passing library search path to scanner

class girscan(Task):
    run_str = "${G_IR_SCANNER} --no-libtool " \
            "${GIRLIB_T:GIRLIB} ${GIRPATH_T:GIRPATH} " \
            "--namespace=${NAMESPACE} --nsversion=${VERSION} " \
            "--output ${TGT} ${SRC}"

@feature("gir")
def process_gir(gen):
    namespace = getattr(gen, "namespace", None)
    if not namespace:
        raise WafError(f"Missing namespace for gir feature in {gen}")
    version = str(getattr(gen, "version", 0))

    scan_task = gen.create_task('girscan',
            tgt=gen.path.find_or_declare(f"{namespace}-{version}.gir"),
            src=gen.to_nodes(getattr(gen, "scan", [])))
    env = scan_task.env
    env.NAMESPACE = namespace
    env.VERSION = version

    try:
        lib_gen = gen.bld.get_tgen_by_name(gen.lib)
    except AttributeError as e:
        raise WafError(f"{gen} lacks a library to introspect") from e
    lib_task = lib_gen.link_task
    env.append_value('GIRLIB', [lib_gen.target])
    scan_task.dep_nodes.extend(lib_task.outputs)
    env.append_unique('GIRPATH', [
        lib_task.outputs[0].parent.path_from(gen.path)])
