# -------------------------------------------------------------------------
#                     The CodeChecker Infrastructure
#   This file is distributed under the University of Illinois Open Source
#   License. See LICENSE.TXT for details.
# -------------------------------------------------------------------------
"""
Check implements a wrapper over 'log' + 'analyze' + 'parse', essentially
giving an easy way to perform analysis from a log command and print results to
stdout.
"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import argparse
import os
import shutil
import tempfile

from codechecker_analyzer import arg
from codechecker_analyzer import analyzer_context
from codechecker_analyzer.analyzers import analyzer_types

from codechecker_common import logger


LOG = logger.get_logger('system')


def get_argparser_ctor_args():
    """
    This method returns a dict containing the kwargs for constructing an
    argparse.ArgumentParser (either directly or as a subparser).
    """

    return {
        'prog': 'CodeChecker check',
        'formatter_class': arg.RawDescriptionDefaultHelpFormatter,

        # Description is shown when the command's help is queried directly
        'description': """
Run analysis for a project with printing results immediately on the standard
output. Check only needs a build command or an already existing logfile and
performs every step of doing the analysis in batch.""",

        # Epilogue is shown after the arguments when the help is queried
        # directly.
        'epilog': """
If you wish to reuse the logfile resulting from executing the build, see
'CodeChecker log'. To keep analysis results for later, see and use
'CodeChecker analyze'. To print human-readable output from previously saved
analysis results, see 'CodeChecker parse'. 'CodeChecker check' exposes a
wrapper calling these three commands in succession. Please make sure your build
command actually builds the files -- it is advised to execute builds on empty
trees, aka. after a 'make clean', as CodeChecker only analyzes files that had
been used by the build system.""",

        # Help is shown when the "parent" CodeChecker command lists the
        # individual subcommands.
        'help': "Perform analysis on a project and print results to standard "
                "output."
    }


def add_arguments_to_parser(parser):
    """
    Add the subcommand's arguments to the given argparse.ArgumentParser.
    """

    parser.add_argument('-o', '--output',
                        type=str,
                        dest="output_dir",
                        required=False,
                        default=argparse.SUPPRESS,
                        help="Store the analysis output in the given folder. "
                             "If it is not given then the results go into a "
                             "temporary directory which will be removed after "
                             "the analysis.")

    parser.add_argument('-t', '--type', '--output-format',
                        dest="output_format",
                        required=False,
                        choices=['plist'],
                        default='plist',
                        help="Specify the format the analysis results "
                             "should use.")

    parser.add_argument('-q', '--quiet',
                        dest="quiet",
                        action='store_true',
                        required=False,
                        default=argparse.SUPPRESS,
                        help="If specified, the build tool's and the "
                             "analyzers' output will not be printed to the "
                             "standard output.")

    parser.add_argument('-f', '--force',
                        dest="force",
                        default=argparse.SUPPRESS,
                        action='store_true',
                        required=False,
                        help="DEPRECATED. Delete analysis results stored in "
                             "the database for the current analysis run's "
                             "name and store only the results reported in the "
                             "'input' files. (By default, CodeChecker would "
                             "keep reports that were coming from files not "
                             "affected by the analysis, and only "
                             "incrementally update defect reports for source "
                             "files that were analysed.)")

    parser.add_argument('--skip-gcc-fix-include',
                        dest="skip_gcc_fix_include",
                        required=False,
                        action='store_true',
                        default=False,
                        help="DEPRECATED. There are some implicit include "
                             "paths which are only used by GCC "
                             "(include-fixed). This flag determines whether "
                             "these should be skipped from the implicit "
                             "include paths.")

    log_args = parser.add_argument_group(
        "log arguments",
        """
Specify how the build information database should be obtained. You need to
specify either an already existing log file, or a build command which will be
used to generate a log file on the fly.""")

    log_args = log_args.add_mutually_exclusive_group(required=True)

    log_args.add_argument('-b', '--build',
                          type=str,
                          dest="command",
                          default=argparse.SUPPRESS,
                          help="Execute and record a build command. Build "
                               "commands can be simple calls to 'g++' or "
                               "'clang++' or 'make', but a more complex "
                               "command, or the call of a custom script file "
                               "is also supported.")

    log_args.add_argument('-l', '--logfile',
                          type=str,
                          dest="logfile",
                          default=argparse.SUPPRESS,
                          help="Use an already existing JSON compilation "
                               "command database file specified at this path.")

    analyzer_opts = parser.add_argument_group("analyzer arguments")
    analyzer_opts.add_argument('-j', '--jobs',
                               type=int,
                               dest="jobs",
                               required=False,
                               default=1,
                               help="Number of threads to use in analysis. "
                                    "More threads mean faster analysis at "
                                    "the cost of using more memory.")

    analyzer_opts.add_argument('-c', '--clean',
                               dest="clean",
                               required=False,
                               action='store_true',
                               default=argparse.SUPPRESS,
                               help="Delete analysis reports stored in the "
                                    "output directory. (By default, "
                                    "CodeChecker would keep reports and "
                                    "overwrites only those files that were "
                                    "update by the current build command).")

    parser.add_argument('--compile-uniqueing',
                        type=str,
                        dest="compile_uniqueing",
                        default="none",
                        required=False,
                        help="Specify the method the compilation "
                             "actions in the  compilation database are "
                             "uniqued before analysis. "
                             "CTU analysis works properly only if "
                             "there is exactly one "
                             "compilation action per source file. "
                             "none(default in non CTU mode): "
                             "no uniqueing is done. "
                             "strict: no uniqueing is done, "
                             "and an error is given if "
                             "there is more than one compilation "
                             "action for a source file. "
                             "alpha(default in CTU mode): If there is more "
                             "than one compilation action for a source "
                             "file, only the one is kept that belongs to the "
                             "alphabetically first "
                             "compilation target. "
                             "If none of the above given, "
                             "this parameter should "
                             "be a python regular expression."
                             "If there is more than one compilation action "
                             "for a source, "
                             "only the one is kept which matches the "
                             "given python regex. If more than one "
                             "matches an error is given. "
                             "The whole compilation "
                             "action text is searched for match.")

    analyzer_opts.add_argument('--report-hash',
                               dest="report_hash",
                               default=argparse.SUPPRESS,
                               required=False,
                               choices=['context-free'],
                               help="EXPERIMENTAL feature. "
                                    "Specify the hash calculation method for "
                                    "reports. If this option is not set, the "
                                    "default calculation method for Clang "
                                    "Static Analyzer will be context "
                                    "sensitive and for Clang Tidy it will be "
                                    "context insensitive. If this option is "
                                    "set to 'context-free' bugs will be "
                                    "identified with the CodeChecker "
                                    "generated context free hash for every "
                                    "analyzers. USE WISELY AND AT YOUR OWN "
                                    "RISK!")

    analyzer_opts.add_argument('-i', '--ignore', '--skip',
                               dest="skipfile",
                               required=False,
                               default=argparse.SUPPRESS,
                               help="Path to the Skipfile dictating which "
                                    "project files should be omitted from "
                                    "analysis. Please consult the User guide "
                                    "on how a Skipfile should be laid out.")

    analyzer_opts.add_argument('--analyzers',
                               nargs='+',
                               dest='analyzers',
                               metavar='ANALYZER',
                               required=False,
                               choices=analyzer_types.supported_analyzers,
                               default=argparse.SUPPRESS,
                               help="Run analysis only with the analyzers "
                                    "specified. Currently supported analyzers "
                                    "are: " +
                                    ', '.join(analyzer_types.
                                              supported_analyzers) + ".")

    analyzer_opts.add_argument('--add-compiler-defaults',
                               action='store_true',
                               required=False,
                               default=argparse.SUPPRESS,
                               help="DEPRECATED. Always True. Retrieve "
                                    " compiler-specific configuration "
                                    "from the analyzers themselves, and use "
                                    "them with Clang. This is used when the "
                                    "compiler on the system is special, e.g. "
                                    "when doing cross-compilation.")

    analyzer_opts.add_argument('--capture-analysis-output',
                               dest='capture_analysis_output',
                               action='store_true',
                               default=argparse.SUPPRESS,
                               required=False,
                               help="Store standard output and standard error "
                                    "of successful analyzer invocations "
                                    "into the '<OUTPUT_DIR>/success' "
                                    "directory.")

    # TODO: One day, get rid of these. See Issue #36, #427.
    analyzer_opts.add_argument('--saargs',
                               dest="clangsa_args_cfg_file",
                               required=False,
                               default=argparse.SUPPRESS,
                               help="File containing argument which will be "
                                    "forwarded verbatim for the Clang Static "
                                    "analyzer.")

    analyzer_opts.add_argument('--tidyargs',
                               dest="tidy_args_cfg_file",
                               required=False,
                               default=argparse.SUPPRESS,
                               help="File containing argument which will be "
                                    "forwarded verbatim for the Clang-Tidy "
                                    "analyzer.")

    analyzer_opts.add_argument('--tidy-config',
                               dest='tidy_config',
                               required=False,
                               default=argparse.SUPPRESS,
                               help="A file in YAML format containing the "
                                    "configuration of clang-tidy checkers. "
                                    "The file can be dumped by "
                                    "'CodeChecker analyzers --dump-config "
                                    "clang-tidy' command.")

    analyzer_opts.add_argument('--timeout',
                               type=int,
                               dest='timeout',
                               required=False,
                               default=argparse.SUPPRESS,
                               help="The amount of time (in seconds) that "
                                    "each analyzer can spend, individually, "
                                    "to analyze the project. If the analysis "
                                    "of a particular file takes longer than "
                                    "this time, the analyzer is killed and "
                                    "the analysis is considered as a failed "
                                    "one.")

    context = analyzer_context.get_context()
    clang_has_z3 = analyzer_types.is_z3_capable(context)

    if clang_has_z3:
        analyzer_opts.add_argument('--z3',
                                   dest='enable_z3',
                                   choices=['on', 'off'],
                                   default='off',
                                   help="Enable the z3 solver backend. This "
                                        "allows reasoning over more complex "
                                        "queries, but performance is worse "
                                        "than the default range-based "
                                        "constraint solver.")

    clang_has_z3_refutation = analyzer_types.is_z3_refutation_capable(context)

    if clang_has_z3_refutation:
        analyzer_opts.add_argument('--z3-refutation',
                                   dest='enable_z3_refutation',
                                   choices=['on', 'off'],
                                   default='on' if clang_has_z3_refutation
                                   else 'off',
                                   help="Switch on/off the Z3 SMT Solver "
                                        "backend to "
                                        "reduce false positives. The results "
                                        "of the ranged based constraint "
                                        "solver in the Clang Static Analyzer "
                                        "will be cross checked with the Z3 "
                                        "SMT solver. This should not cause "
                                        "that much of a slowdown compared to "
                                        "using the Z3 solver only.")

    if analyzer_types.is_ctu_capable(context):
        ctu_opts = parser.add_argument_group(
            "cross translation unit analysis arguments",
            """
These arguments are only available if the Clang Static Analyzer supports
Cross-TU analysis. By default, no CTU analysis is run when 'CodeChecker check'
is called.""")

        ctu_modes = ctu_opts.add_mutually_exclusive_group()

        ctu_modes.add_argument('--ctu', '--ctu-all',
                               action='store_const',
                               const=[True, True],
                               dest='ctu_phases',
                               default=argparse.SUPPRESS,
                               help="Perform Cross Translation Unit (CTU) "
                                    "analysis, both 'collect' and 'analyze' "
                                    "phases. In this mode, the extra files "
                                    "created by 'collect' are cleaned up "
                                    "after the analysis.")

        ctu_modes.add_argument('--ctu-collect',
                               action='store_const',
                               const=[True, False],
                               dest='ctu_phases',
                               default=argparse.SUPPRESS,
                               help="Perform the first, 'collect' phase of "
                                    "Cross-TU analysis. This phase generates "
                                    "extra files needed by CTU analysis, and "
                                    "puts them into '<OUTPUT_DIR>/ctu-dir'. "
                                    "NOTE: If this argument is present, "
                                    "CodeChecker will NOT execute the "
                                    "analyzers!")

        ctu_modes.add_argument('--ctu-analyze',
                               action='store_const',
                               const=[False, True],
                               dest='ctu_phases',
                               default=argparse.SUPPRESS,
                               help="Perform the second, 'analyze' phase of "
                                    "Cross-TU analysis, using already "
                                    "available extra files in "
                                    "'<OUTPUT_DIR>/ctu-dir'. (These files "
                                    "will not be cleaned up in this mode.)")

    if analyzer_types.is_statistics_capable(context):
        stat_opts = parser.add_argument_group(
            "EXPERIMENTAL statistics analysis feature arguments",
            """
These arguments are only available if the Clang Static Analyzer supports
Statistics-based analysis (e.g. statisticsCollector.ReturnValueCheck,
statisticsCollector.SpecialReturnValue checkers are available).""")

        stat_opts.add_argument('--stats-collect', '--stats-collect',
                               action='store',
                               default=argparse.SUPPRESS,
                               dest='stats_output',
                               help="EXPERIMENTAL feature. "
                                    "Perform the first, 'collect' phase of "
                                    "Statistical analysis. This phase "
                                    "generates extra files needed by "
                                    "statistics analysis, and "
                                    "puts them into "
                                    "'<STATS_OUTPUT>'."
                                    " NOTE: If this argument is present, "
                                    "CodeChecker will NOT execute the "
                                    "analyzers!")

        stat_opts.add_argument('--stats-use', '--stats-use',
                               action='store',
                               default=argparse.SUPPRESS,
                               dest='stats_dir',
                               help="EXPERIMENTAL feature. "
                                    "Use the previously generated statistics "
                                    "results for the analysis from the given "
                                    "'<STATS_DIR>'.")

        stat_opts.add_argument('--stats',
                               action='store_true',
                               default=argparse.SUPPRESS,
                               dest='stats_enabled',
                               help="EXPERIMENTAL feature. "
                                    "Perform both phases of "
                                    "Statistical analysis. This phase "
                                    "generates extra files needed by "
                                    "statistics analysis and enables "
                                    "the statistical checkers. "
                                    "No need to enable them explicitly.")

        stat_opts.add_argument('--stats-min-sample-count',
                               action='store',
                               default="10",
                               type=int,
                               dest='stats_min_sample_count',
                               help="EXPERIMENTAL feature. "
                                    "Minimum number of samples (function call"
                                    " occurrences) to be collected"
                                    " for a statistics to be relevant.")

        stat_opts.add_argument('--stats-relevance-threshold',
                               action='store',
                               default="0.85",
                               type=float,
                               dest='stats_relevance_threshold',
                               help="EXPERIMENTAL feature. "
                                    "The minimum ratio of calls of function "
                                    "f that must have a certain property "
                                    "property to consider it true for that "
                                    "function (calculated as calls "
                                    "with a property/all calls)."
                                    " CodeChecker will warn for"
                                    " calls of f do not have that property.")

    checkers_opts = parser.add_argument_group(
        "checker configuration",
        """
Checkers
------------------------------------------------
The analyzer performs checks that are categorized into families or "checkers".
See 'CodeChecker checkers' for the list of available checkers. You can
fine-tune which checkers to use in the analysis by setting the enabled and
disabled flags starting from the bigger groups and going inwards, e.g.
'-e core -d core.uninitialized -e core.uninitialized.Assign' will enable every
'core' checker, but only 'core.uninitialized.Assign' from the
'core.uninitialized' group. Please consult the manual for details. Disabling
certain checkers - such as the 'core' group - is unsupported by the LLVM/Clang
community, and thus discouraged.

Compiler warnings
------------------------------------------------
Compiler warnings are diagnostic messages that report constructions that are
not inherently erroneous but that are risky or suggest there may have been an
error. Compiler warnings are named 'clang-diagnostic-<warning-option>', e.g.
Clang warning controlled by '-Wliteral-conversion' will be reported with check
name 'clang-diagnostic-literal-conversion'. You can fine-tune which warnings to
use in the analysis by setting the enabled and disabled flags starting from the
bigger groups and going inwards, e.g. '-e Wunused -d Wno-unused-parameter' will
enable every 'unused' warnings except 'unused-parameter'. These flags should
start with a capital 'W' or 'Wno-' prefix followed by the waning name (E.g.:
'-e Wliteral-conversion', '-d Wno-literal-conversion'). By default '-Wall' and
'-Wextra' warnings are enabled. For more information see:
https://clang.llvm.org/docs/DiagnosticsReference.html.""")

    checkers_opts.add_argument('-e', '--enable',
                               dest="enable",
                               metavar='checker/group/profile',
                               default=argparse.SUPPRESS,
                               action=arg.OrderedCheckersAction,
                               help="Set a checker (or checker group) "
                                    "to BE USED in the analysis.")

    checkers_opts.add_argument('-d', '--disable',
                               dest="disable",
                               metavar='checker/group/profile',
                               default=argparse.SUPPRESS,
                               action=arg.OrderedCheckersAction,
                               help="Set a checker (or checker group) "
                                    "to BE PROHIBITED from use in the "
                                    "analysis.")

    checkers_opts.add_argument('--enable-all',
                               dest="enable_all",
                               action='store_true',
                               required=False,
                               default=argparse.SUPPRESS,
                               help="Force the running analyzers to use "
                                    "almost every checker available. The "
                                    "checker groups 'alpha.', 'debug.' and "
                                    "'osx.' (on Linux) are NOT enabled "
                                    "automatically and must be EXPLICITLY "
                                    "specified. WARNING! Enabling all "
                                    "checkers might result in the analysis "
                                    "losing precision and stability, and "
                                    "could even result in a total failure of "
                                    "the analysis. USE WISELY AND AT YOUR "
                                    "OWN RISK!")

    output_opts = parser.add_argument_group("output arguments")

    output_opts.add_argument('--print-steps',
                             dest="print_steps",
                             action="store_true",
                             required=False,
                             default=argparse.SUPPRESS,
                             help="Print the steps the analyzers took in "
                                  "finding the reported defect.")

    logger.add_verbose_arguments(parser)
    parser.set_defaults(func=main)


def main(args):
    """
    Execute a wrapper over log-analyze-parse, aka 'check'.
    """

    logger.setup_logger(args.verbose if 'verbose' in args else None)

    def __update_if_key_exists(source, target, key):
        """Append the source Namespace's element with 'key' to target with
        the same key, but only if it exists."""
        if key in source:
            setattr(target, key, getattr(source, key))

    if 'force' in args:
        LOG.warning('"--force" option has been deprecated and it will be '
                    'removed in the future version of CodeChecker. Use the '
                    '"--clean" option to delete analysis reports stored in '
                    'the output directory.')

    # If no output directory is given then the checker results go to a
    # temporary directory. This way the subsequent "quick" checks don't pollute
    # the result list of a previous check. If the detection status function is
    # intended to be used (i.e. by keeping the .plist files) then the output
    # directory has to be provided explicitly.
    is_temp_output = False
    if 'output_dir' in args:
        output_dir = args.output_dir
    else:
        output_dir = tempfile.mkdtemp()
        is_temp_output = True

    output_dir = os.path.abspath(output_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    logfile = None
    is_command = False
    try:
        # --- Step 1.: Perform logging if build command was specified.
        if 'command' in args:
            logfile = tempfile.NamedTemporaryFile().name
            is_command = True

            # Translate the argument list between check and log.
            log_args = argparse.Namespace(
                command=args.command,
                logfile=logfile
            )
            __update_if_key_exists(args, log_args, 'quiet')
            __update_if_key_exists(args, log_args, 'verbose')

            import codechecker_analyzer.cmd.log as log_module
            LOG.debug("Calling LOG with args:")
            LOG.debug(log_args)

            log_module.main(log_args)
        elif 'logfile' in args:
            logfile = args.logfile

        # --- Step 2.: Perform the analysis.
        if not os.path.exists(logfile):
            raise OSError("The specified logfile '" + logfile + "' does not "
                          "exist.")

        analyze_args = argparse.Namespace(
            logfile=[logfile],
            output_path=output_dir,
            output_format='plist',
            jobs=args.jobs,
            skip_gcc_fix_include=args.skip_gcc_fix_include
        )
        # Some arguments don't have default values.
        # We can't set these keys to None because it would result in an error
        # after the call.
        args_to_update = ['quiet',
                          'skipfile',
                          'analyzers',
                          'add_compiler_defaults',
                          'clangsa_args_cfg_file',
                          'tidy_args_cfg_file',
                          'tidy_config',
                          'capture_analysis_output',
                          'ctu_phases',
                          'stats_output',
                          'stats_dir',
                          'stats_enabled',
                          'stats_relevance_threshold',
                          'stats_min_sample_count',
                          'enable_all',
                          'ordered_checkers',  # --enable and --disable.
                          'timeout',
                          'compile_uniqueing',
                          'report_hash',
                          'enable_z3',
                          'enable_z3_refutation']
        for key in args_to_update:
            __update_if_key_exists(args, analyze_args, key)
        if 'clean' in args:
            setattr(analyze_args, 'clean', True)
        __update_if_key_exists(args, analyze_args, 'verbose')

        import codechecker_analyzer.cmd.analyze as analyze_module
        LOG.debug("Calling ANALYZE with args:")
        LOG.debug(analyze_args)

        analyze_module.main(analyze_args)

        # --- Step 3.: Print to stdout.
        parse_args = argparse.Namespace(
            input=[output_dir],
            input_format='plist'
        )
        __update_if_key_exists(args, parse_args, 'print_steps')
        __update_if_key_exists(args, parse_args, 'verbose')
        __update_if_key_exists(args, parse_args, 'skipfile')

        import codechecker_analyzer.cmd.parse as parse_module
        LOG.debug("Calling PARSE with args:")
        LOG.debug(parse_args)

        parse_module.main(parse_args)
    except ImportError:
        LOG.error("Check failed: couldn't import a library.")
    except Exception:
        LOG.exception("Running check failed.")
        import traceback
        traceback.print_exc()
    finally:
        if is_temp_output:
            shutil.rmtree(output_dir)
        if is_command:
            os.remove(logfile)

    LOG.debug("Check finished.")
