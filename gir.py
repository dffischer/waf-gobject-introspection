#!/usr/bin/python

"""
Create and install GObject Introspection data.

The functions herein center around a feature called 'gir' which scans source
files for GObject Introspection data and compiles a Typelib. It and all
mandatory parameters can simply be added to a generator creating a shared
library from c sources or used to create a separate task generator that
references the target library.

    def configure(cnf):
        cnf.load("gir")

    def build(bld):
        bld(features="c cshlib gir",
                source="object.c",  # main code to be compiled
                target="object",
                scan="object.h",  # header files for the g-ir-scanner
                namespace="Object",
                version=1)  # defaults to 0

or

        bld(features="c cshlib",  # library compilation
                source="object.c", target="object", use="GLIB2")
        bld(features="gir", namespace="Object",
                lib="object",  # library to introspect
                scan="object.h")  # header files to scan
"""

from waflib.TaskGen import feature, after_method
from waflib.Task import Task
from waflib.Errors import WafError

def configure(cnf):
    cnf.find_program("g-ir-scanner")
    cnf.find_program("g-ir-compiler")
    env = cnf.env
    env.GIRLIB_T = '-l%s'      # template passing library to scanner
    env.GIRPATH_T = '-L%s'  # template passing library search path to scanner
    cnf.env.append_value("GIRSCANNERFLAGS", "--warn-all")

class gir(Task):
    run_str = "${G_IR_SCANNER} --no-libtool ${GIRSCANNERFLAGS} " \
            "${GIRLIB_T:GIRLIB} ${GIRPATH_T:GIRPATH} " \
            "--namespace=${NAMESPACE} --nsversion=${VERSION} " \
            "--output ${TGT} ${SRC}"

    @staticmethod
    def keyword():
        return "Scanning"

class gircompile(Task):
    run_str = "${G_IR_COMPILER} -o ${TGT} ${SRC}"

@feature("gir")
@after_method('apply_link')
def process_gir(gen):
    namespace = getattr(gen, "namespace", None)
    if not namespace:
        raise WafError(f"Missing namespace for gir feature in {gen}")
    version = str(getattr(gen, "version", 0))
    gir = gen.path.find_or_declare(f"{namespace}-{version}.gir")

    scan_task = gen.create_task('gir', tgt=gir,
            src=gen.to_nodes(getattr(gen, "scan", [])))
    env = scan_task.env
    env.NAMESPACE = namespace
    env.VERSION = version

    lib = getattr(gen, "lib", None)
    if lib:
        lib_gen = gen.bld.get_tgen_by_name(gen.lib)
        lib_task = lib_gen.link_task
    else:
        lib_task = getattr(gen, 'link_task', None)
        if not lib_task:
            raise WafError(f"{gen} lacks a library to introspect "
                    "and does not build one itself")
        lib_gen = gen
    env.append_value('GIRLIB', [lib_gen.target])
    scan_task.dep_nodes.extend(lib_task.outputs)
    env.append_unique('GIRPATH', [
        lib_task.outputs[0].parent.path_from(gen.path)])

    gen.create_task('gircompile', gir, gir.change_ext('.typelib'))
