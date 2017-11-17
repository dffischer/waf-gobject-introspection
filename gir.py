#!/usr/bin/python

"""
Create and install GObject Introspection data.

The functions herein center around a feature called 'gir' which scans source
files for GObject Introspection data and compiles a Typelib. It and all
mandatory parameters can simply be added to a generator creating a shared
library from c sources or used to create a separate task generator that
references the target library.

    def options(opt):
        opt.load("gir")

    def configure(cnf):
        cnf.load("gir")
        cnf.check_gir("GLib-2.0",
            store="GLIB")  # defaults to upper cased package name

    def build(bld):
        bld(features="c cshlib gir",
                source="object.c",  # main code to be compiled
                target="object",
                scan="object.h",  # header files for the g-ir-scanner
                include="GLIB",  # GIR repositories to depend upon
                namespace="Object",  # by default capitalized first header name
                version=1)  # defaults to 0

or

        bld(features="c cshlib",  # library compilation
                source="object.c", target="object", use="GLIB2")
        bld(features="gir",
                lib="object",  # library to introspect
                scan="object.h")  # header files to scan

If the scan parameter is left out, one header is assumed with the same base
name as the library. The lib parameter can be left out when the task generator
already builds a library to use or the basename of the first header in a
present scan parameter designates the library name.

Other GIR repositories to depend upon are configured similar to the check_cfg
function known from c projects. The underlying libraries will automatically be
checked, too.

Installation paths and the location to lookup GIR XML descriptions can be
configured as known from the gnu_dirs package. To do so, the gir tool has to be
loaded also in the options function.
"""

from waflib.TaskGen import feature, after_method
from waflib.Task import Task
from waflib.Errors import WafError
from waflib.Configure import conf
from waflib.Utils import subst_vars
from operator import methodcaller
from os.path import join
from xml.etree.ElementTree import fromstring

def options(opt):
    opt.load('gnu_dirs')

    group = opt.get_option_group("Installation directories")
    group.add_option("--girdir",
            help="GIR XML repository [DATAROOTDIR/gir-1.0]")
    group.add_option("--typelibdir",
            help="compiled GIR typelibs [LIBDIR/girepository-1.0]")

    group = opt.get_option_group("Configuration options")
    group.add_option("--girsearchpath",
            help="path to lookup GIR repository XML [GIRDIR]")

GIR_NAMESPACE = '{http://www.gtk.org/introspection/core/1.0}'

@conf
def check_gir(cnf, gir, store=None):
    cnf.start_msg(f"Checking for GIR XML {gir}")
    girpath = getattr(cnf, 'girpath', None)
    if not girpath:
        girpath = cnf.girpath = cnf.root.find_node(cnf.env.GIRSEARCHPATH)

    if not store:
        store = gir.upper()

    f = cnf.girpath.find_resource(gir + '.gir')
    if not f:
        cnf.end_msg("not found", 'YELLOW')
        cnf.fatal('The configuration failed')
    cnf.env.append_value(f'GIRINC_{store}', (gir, ))
    xml = fromstring(f.read())
    packages = tuple(include.get('name') for include
            in xml.iterfind(GIR_NAMESPACE + 'package'))
    recursive = xml.findall(GIR_NAMESPACE + 'include')
    cnf.end_msg(f.abspath())

    for package in packages:
        cnf.check_cfg(package=package, args='--cflags --libs')
    for recurse in recursive:
        cnf.check_gir('{name}-{version}'.format(**recurse.attrib))

def configure(cnf):
    cnf.find_program("g-ir-scanner")
    cnf.find_program("g-ir-compiler")
    env = cnf.env
    env.GIRLIB_T = '-l%s'      # template passing library to scanner
    env.GIRPATH_T = '-L%s'  # template passing library search path to scanner
    env.GIRINC_T = '--include=%s'  # template including other GIR repositories
    cnf.env.append_value("GIRSCANNERFLAGS", "--warn-all")

    cnf.load('gnu_dirs')
    env.GIRDIR = subst_vars(cnf.options.girdir or
            join("${DATAROOTDIR}", "gir-1.0"), env)
    env.TYPELIBDIR = subst_vars(cnf.options.typelibdir or
            join("${LIBDIR}", "girepository-1.0"), env)
    env.GIRSEARCHPATH = subst_vars(cnf.options.typelibdir or "${GIRDIR}", env)

class gir(Task):
    run_str = "${G_IR_SCANNER} --no-libtool ${GIRSCANNERFLAGS} " \
            "${GIRLIB_T:GIRLIB} ${GIRPATH_T:GIRPATH} ${GIRINC_T:GIRINC} " \
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
    scan = gen.to_nodes(getattr(gen, "scan", []))

    lib = getattr(gen, "lib", None)
    if lib:
        lib_gen = gen.bld.get_tgen_by_name(gen.lib)
        lib_task = lib_gen.link_task
    else:
        lib_task = getattr(gen, 'link_task', None)
        if lib_task:
            lib_gen = gen
        else:
            try:
                lib_gen = gen.bld.get_tgen_by_name(
                        scan[0].name.rpartition('.')[0])
            except IndexError:
                raise WafError(f"{gen} lacks a library to introspect "
                        "and does not build one itself")
            lib_task = lib_gen.link_task

    if not scan:
        scan = gen.to_nodes([f"{lib_gen.target}.h"])
    namespace = getattr(gen, "namespace", None) or \
        ''.join(map(methodcaller('capitalize'), scan[0].name[:-2].split('_')))
    version = str(getattr(gen, "version", 0))
    gir = gen.path.find_or_declare(f"{namespace}-{version}.gir")

    scan_task = gen.create_task('gir', tgt=gir, src=scan)
    env = scan_task.env
    env.NAMESPACE = namespace
    env.VERSION = version

    env.append_value('GIRLIB', [lib_gen.target])
    scan_task.dep_nodes.extend(lib_task.outputs)
    env.append_unique('GIRPATH', [
        lib_task.outputs[0].parent.path_from(gen.path)])

    for include in gen.to_list(getattr(gen, "include", [])):
        env.append_value('GIRINC', env[f'GIRINC_{include}'])

    gen.add_install_files(install_to=env.GIRDIR,
            install_from=scan_task.outputs)
    gen.add_install_files(install_to=env.TYPELIBDIR,
            install_from=gen.create_task('gircompile', gir,
                gir.change_ext('.typelib')).outputs)
