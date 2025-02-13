Table of Contents
=================
* [Easy analysis wrappers](#easy-analysis-wrappers)
    * [`check`](#check)
* [Available CodeChecker analyzer subcommands](#available-analyzer-commands)
    * [`log`](#log)
        * [BitBake](#bitbake)
        * [CCache](#ccache)
        * [intercept-build](#intercept-build)
    * [`analyze`](#analyze)
        * [_Skip_ file](#skip)
            * [Absolute path examples](#skip-abs-example)
            * [Relative or partial path examples](#skip-rel-example)
        * [Analyzer configuration](#analyzer-configuration)
            * [Compiler-specific include path and define detection (cross compilation)](#include-path)
            * [Forwarding compiler options](#forwarding-compiler-options)
              * [_Clang Static Analyzer_](#clang-static-analyzer)
              * [_Clang-Tidy_](#clang-tidy)
        * [Toggling checkers](#toggling-checkers)
            * [Checker profiles](#checker-profiles)
            * [`--enable-all`](#enable-all)
        * [Toggling compiler warnings](#toggling-warnings)
        * [Cross Translation Unit (CTU) analysis mode](#ctu)
        * [Statistical analysis mode](#statistical)
    * [`parse`](#parse)
        * [Exporting source code suppression to suppress file](#suppress-file)
    * [`checkers`](#checkers)
    * [`analyzers`](#analyzers)

# Easy analysis wrappers <a name="easy-analysis-wrappers"></a>

CodeChecker provides, along with the more fine-tuneable commands, some easy
out-of-the-box invocations to ensure the most user-friendly operation, the
**check** mode.

## `check` <a name="check"></a>

It is possible to easily analyse the project for defects without keeping the
temporary analysis files and without using any database to store the reports
in, but instead printing the found issues to the standard output.

To analyse your project by doing a build and reporting every found issue in the
built files, execute

```sh
CodeChecker check --build "make"
```

Please make sure your build command actually compiles (builds) the source
files you intend to analyse, as CodeChecker only analyzes files that had been
used by the build system.

If you have an already existing JSON Compilation Commands file, you can also
supply it to `check`:

```sh
CodeChecker check --logfile ./my-build.json
```

By default, only the report's main messages are printed. To print the
individual steps the analysers took in discovering the issue, specify
`--steps`.

`check` is a wrapper over the following calls:

 * If `--build` is specified, the build is executed as if `CodeChecker log`
   were invoked.
 * The resulting logfile, or a `--logfile` specified is used for `CodeChecker
   analyze`, which will put analysis reports into `--output`.
 * The analysis results are fed for `CodeChecker parse`.

After the results has been printed to the standard output, the temporary files
used for the analysis are cleaned up.

Please see the individual help for `log`, `analyze` and `parse` (below in this
_User guide_) for information about the arguments which are not documented
here. For example the CTU related arguments are documented at `analyze`
subcommand.

```
usage: CodeChecker check [-h] [-o OUTPUT_DIR] [-t {plist}] [-q] [-f]
                         [--skip-gcc-fix-include] (-b COMMAND | -l LOGFILE)
                         [-j JOBS] [-c]
                         [--compile-uniqueing COMPILE_UNIQUEING]
                         [--report-hash {context-free}] [-i SKIPFILE]
                         [--analyzers ANALYZER [ANALYZER ...]]
                         [--add-compiler-defaults] [--capture-analysis-output]
                         [--saargs CLANGSA_ARGS_CFG_FILE]
                         [--tidyargs TIDY_ARGS_CFG_FILE]
                         [--tidy-config TIDY_CONFIG] [--timeout TIMEOUT]
                         [-e checker/group/profile] [-d checker/group/profile]
                         [--enable-all] [--print-steps]
                         [--verbose {info,debug,debug_analyzer}]

Run analysis for a project with printing results immediately on the standard
output. Check only needs a build command or an already existing logfile and
performs every step of doing the analysis in batch.

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT_DIR, --output OUTPUT_DIR
                        Store the analysis output in the given folder. If it
                        is not given then the results go into a temporary
                        directory which will be removed after the analysis.
  -t {plist}, --type {plist}, --output-format {plist}
                        Specify the format the analysis results should use.
                        (default: plist)
  -q, --quiet           If specified, the build tool's and the analyzers'
                        output will not be printed to the standard output.
  -f, --force           DEPRECATED. Delete analysis results stored in the
                        database for the current analysis run's name and store
                        only the results reported in the 'input' files. (By
                        default, CodeChecker would keep reports that were
                        coming from files not affected by the analysis, and
                        only incrementally update defect reports for source
                        files that were analysed.)
  --skip-gcc-fix-include
                        DEPRECATED. There are some implicit include paths which
                        are only used by GCC (include-fixed). This flag
                        determines whether these should be skipped from the
                        implicit include paths. (default: False)
  --compile-uniqueing COMPILE_UNIQUEING
                        Specify the method the compilation actions in the
                        compilation database are uniqued before analysis. CTU
                        analysis works properly only if there is exactly one
                        compilation action per source file. none(default in
                        non CTU mode): no uniqueing is done. strict: no
                        uniqueing is done, and an error is given if there is
                        more than one compilation action for a source file.
                        alpha(default in CTU mode): If there is more than one
                        compilation action for a source file, only the one is
                        kept that belongs to the alphabetically first
                        compilation target. If none of the above given, this
                        parameter should be a python regular expression.If
                        there is more than one compilation action for a
                        source, only the one is kept which matches the given
                        python regex. If more than one matches an error is
                        given. The whole compilation action text is searched
                        for match. (default: none)
  --verbose {info,debug,debug_analyzer}
                        Set verbosity level.

log arguments:
  
  Specify how the build information database should be obtained. You need to
  specify either an already existing log file, or a build command which will be
  used to generate a log file on the fly.

  -b COMMAND, --build COMMAND
                        Execute and record a build command. Build commands can
                        be simple calls to 'g++' or 'clang++' or 'make', but a
                        more complex command, or the call of a custom script
                        file is also supported.
  -l LOGFILE, --logfile LOGFILE
                        Use an already existing JSON compilation command
                        database file specified at this path.

analyzer arguments:
  -j JOBS, --jobs JOBS  Number of threads to use in analysis. More threads
                        mean faster analysis at the cost of using more memory.
                        (default: 1)
  -c, --clean           Delete analysis reports stored in the output
                        directory. (By default, CodeChecker would keep reports
                        and overwrites only those files that were update by
                        the current build command).
  --report-hash {context-free}
                        EXPERIMENTAL feature. Specify the hash calculation
                        method for reports. If this option is not set, the
                        default calculation method for Clang Static Analyzer
                        will be context sensitive and for Clang Tidy it will
                        be context insensitive. If this option is set to
                        'context-free' bugs will be identified with the
                        CodeChecker generated context free hash for every
                        analyzers. USE WISELY AND AT YOUR OWN RISK!
  -i SKIPFILE, --ignore SKIPFILE, --skip SKIPFILE
                        Path to the Skipfile dictating which project files
                        should be omitted from analysis. Please consult the
                        User guide on how a Skipfile should be laid out.
  --analyzers ANALYZER [ANALYZER ...]
                        Run analysis only with the analyzers specified.
                        Currently supported analyzers are: clangsa, clang-
                        tidy.
  --add-compiler-defaults
                        DEPRECATED. Always True. Retrieve compiler-specific
                        configuration from the analyzers themselves, and use
                        them with Clang. This is used when the compiler on the
                        system is special, e.g. when doing cross-compilation.
  --capture-analysis-output
                        Store standard output and standard error of successful
                        analyzer invocations into the '<OUTPUT_DIR>/success'
                        directory.
  --saargs CLANGSA_ARGS_CFG_FILE
                        File containing argument which will be forwarded
                        verbatim for the Clang Static analyzer.
  --tidyargs TIDY_ARGS_CFG_FILE
                        File containing argument which will be forwarded
                        verbatim for the Clang-Tidy analyzer.
  --tidy-config TIDY_CONFIG
                        A file in YAML format containing the configuration of
                        clang-tidy checkers. The file can be dumped by
                        'CodeChecker analyzers --dump-config clang-tidy'
                        command.
  --timeout TIMEOUT     The amount of time (in seconds) that each analyzer can
                        spend, individually, to analyze the project. If the
                        analysis of a particular file takes longer than this
                        time, the analyzer is killed and the analysis is
                        considered as a failed one.
  --z3 {on,off}         Enable the z3 solver backend. This allows reasoning
                        over more complex queries, but performance is worse
                        than the default range-based constraint solver.
                        (default: off)
  --z3-refutation {on,off}
                        Switch on/off the Z3 SMT Solver backend to reduce
                        false positives. The results of the ranged based
                        constraint solver in the Clang Static Analyzer will be
                        cross checked with the Z3 SMT solver. This should not
                        cause that much of a slowdown compared to using the Z3
                        solver only. (default: on)

checker configuration:
  
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
  https://clang.llvm.org/docs/DiagnosticsReference.html.

  -e checker/group/profile, --enable checker/group/profile
                        Set a checker (or checker group) to BE USED in the
                        analysis.
  -d checker/group/profile, --disable checker/group/profile
                        Set a checker (or checker group) to BE PROHIBITED from
                        use in the analysis.
  --enable-all          Force the running analyzers to use almost every
                        checker available. The checker groups 'alpha.',
                        'debug.' and 'osx.' (on Linux) are NOT enabled
                        automatically and must be EXPLICITLY specified.
                        WARNING! Enabling all checkers might result in the
                        analysis losing precision and stability, and could
                        even result in a total failure of the analysis. USE
                        WISELY AND AT YOUR OWN RISK!

output arguments:
  --print-steps         Print the steps the analyzers took in finding the
                        reported defect.

```

# Available CodeChecker analyzer subcommands <a name="available-analyzer-commands"></a>

## `log` <a name="log"></a>

The first step in performing an analysis on your project is to record
information about the files in your project for the analyzers. This is done by
recording a build of your project, which is done by the command `CodeChecker
log`.

```
usage: CodeChecker log [-h] -o LOGFILE -b COMMAND [-q]
                       [--verbose {info,debug,debug_analyzer}]

Runs the given build command and records the executed compilation steps. These
steps are written to the output file in a JSON format. Available build logger
tool that will be used is '...'.

optional arguments:
  -h, --help            show this help message and exit
  -o LOGFILE, --output LOGFILE
                        Path of the file to write the collected compilation
                        commands to. If the file already exists, it will be
                        overwritten.
  -b COMMAND, --build COMMAND
                        The build command to execute. Build commands can be
                        simple calls to 'g++' or 'clang++' or 'make', but a
                        more complex command, or the call of a custom script
                        file is also supported.
  -q, --quiet           Do not print the output of the build tool into the
                        output of this command.
  --verbose {info,debug,debug_analyzer}
                        Set verbosity level.
```

Please note, that only the files that are used in the given `--build` argument
will be recorded. To analyze your whole project, make sure your build tree has
been cleaned before executing `log`.

You can change the compilers that should be logged.
Set `CC_LOGGER_GCC_LIKE` environment variable to a colon separated list.
For example (default):

```sh
export CC_LOGGER_GCC_LIKE="gcc:g++:clang"
```

This colon separated list may contain compiler names or paths. In case an
element of this list contains at least one slash (/) character then this is
considered a path. The logger will capture only those build actions which have
this postfix:

```sh
export CC_LOGGER_GCC_LIKE="gcc:/bin/g++"

# "gcc" has to be infix of the compiler's name because it contains no slash.
# "/bin/g++" has to be postfix of the compiler's path because it contains slash.

my/gcc/compiler/g++ main.cpp  # Not captured because there is no match.
my/gcc/compiler/gcc-7 main.c  # Captured because "gcc" is infix of "gcc-7".
/usr/bin/g++ main.cpp         # Captured because "/bin/g++" is postfix of the compiler path.
/usr/bin/g++-7 main.cpp       # Not captured because "/bin/g++" is not postfix of the compiler path.
```

Example:

```sh
CodeChecker log -o ../codechecker_myProject_build.log -b "make -j2"
```

### BitBake
Do the following steps to log compiler calls made by
[BitBake](https://github.com/openembedded/bitbake) using CodeChecker.

* Add `LD_LIBRARY_PATH`, `LD_PRELOAD`, `CC_LOGGER_GCC_LIKE` and `CC_LOGGER_FILE`
to `BB_ENV_EXTRAWHITE` variable in your shell environment:
```bash
export BB_ENV_EXTRAWHITE="LD_PRELOAD LD_LIBRARY_PATH CC_LOGGER_FILE CC_LOGGER_GCC_LIKE $BB_ENV_EXTRAWHITE"
```
 **Note:** `BB_ENV_EXTRAWHITE` specifies an additional set of variables to allow through
(whitelist) from the external environment into BitBake's datastore.

* Add the following lines to the `conf/bitbake.conf` file:
```bash
export LD_PRELOAD
export LD_LIBRARY_PATH
export CC_LOGGER_FILE
export CC_LOGGER_GCC_LIKE
```

* Run `CodeChecker log`:
```bash
CodeChecker log -o ../compile_commands.json -b "bitbake myProject"
```

### CCache
If your build system setup uses CCache then it can be logged too. If
`CC_LOGGER_GCC_LIKE` contains "cc" or "ccache" directly then these actions will
also be logged. Depending on CCache configuration there are two forms how it
can be used:
```bash
ccache g++ -DHELLO=world main.cpp
ccache -DHELLO=world main.cpp
```
The compiler may or may not follow `ccache` command. If the compiler is missing
then the used compiler can be configured in a config file or an environment
variable.

Currently CodeChecker supports only the first case where the compiler name is
also included in the build command.

### intercept-build <a name="intercept-build"></a>
[`intercept-build`](https://github.com/rizsotto/scan-build) is an alternative
tool for logging the compilation actions. Note that its first version (1.1) had
a bug in case the original build command contained a space character:
```bash
intercept-build bash -c 'g++ -DVARIABLE="hello world" main.cpp'
```
When analysing this build action, CodeChecker will most probably give a
compilation error on the underlying Clang invocation.

## `analyze` <a name="analyze"></a>

After a JSON Compilation Command Database has been created, the next step is
to invoke and execute the analyzers. CodeChecker will use the specified
`logfile`s (there can be multiple given) and create the outputs to the
`--output` directory. (These outputs will be `plist` files, currently only
these are supported.) The machine-readable output files can be used later on
for printing an overview in the terminal (`CodeChecker parse`) or storing
(`CodeChecker store`) analysis results in a database, which can later on be
viewed in a browser.

Example:

```sh
CodeChecker analyze ../codechecker_myProject_build.log -o my_plists
```

`CodeChecker analyze` supports a myriad of fine-tuning arguments, explained
below:

```
usage: CodeChecker analyze [-h] [-j JOBS] [-i SKIPFILE] -o OUTPUT_PATH
                           [--compiler-info-file COMPILER_INFO_FILE]
                           [--skip-gcc-fix-include] [-t {plist}] [-q] [-c]
                           [--compile-uniqueing COMPILE_UNIQUEING]
                           [--report-hash {context-free}] [-n NAME]
                           [--analyzers ANALYZER [ANALYZER ...]]
                           [--add-compiler-defaults]
                           [--capture-analysis-output]
                           [--saargs CLANGSA_ARGS_CFG_FILE]
                           [--tidyargs TIDY_ARGS_CFG_FILE]
                           [--tidy-config TIDY_CONFIG] [--timeout TIMEOUT]
                           [--ctu | --ctu-collect | --ctu-analyze]
                           [--ctu-reanalyze-on-failure]
                           [-e checker/group/profile]
                           [-d checker/group/profile] [--enable-all]
                           [--verbose {info,debug,debug_analyzer}]
                           logfile [logfile ...]

Use the previously created JSON Compilation Database to perform an analysis on
the project, outputting analysis results in a machine-readable format.

positional arguments:
  logfile               Path to the JSON compilation command database files
                        which were created during the build. The analyzers
                        will check only the files registered in these build
                        databases.

optional arguments:
  -h, --help            show this help message and exit
  -j JOBS, --jobs JOBS  Number of threads to use in analysis. More threads
                        mean faster analysis at the cost of using more memory.
                        (default: 1)
  -i SKIPFILE, --ignore SKIPFILE, --skip SKIPFILE
                        Path to the Skipfile dictating which project files
                        should be omitted from analysis. Please consult the
                        User guide on how a Skipfile should be laid out.
  -o OUTPUT_PATH, --output OUTPUT_PATH
                        Store the analysis output in the given folder.
  --compiler-info-file COMPILER_INFO_FILE
                        Read the compiler includes and target from the
                        specified file rather than invoke the compiler
                        executable.
  --skip-gcc-fix-include
                        DEPRECATED. There are some implicit include paths which
                        are only used by GCC (include-fixed). This flag
                        determines whether these should be skipped from the
                        implicit include paths. (default: False)
  -t {plist}, --type {plist}, --output-format {plist}
                        Specify the format the analysis results should use.
                        (default: plist)
  -q, --quiet           Do not print the output or error of the analyzers to
                        the standard output of CodeChecker.
  -c, --clean           Delete analysis reports stored in the output
                        directory. (By default, CodeChecker would keep reports
                        and overwrites only those files that were update by
                        the current build command).
  --compile-uniqueing COMPILE_UNIQUEING
                        Specify the method the compilation actions in the
                        compilation database are uniqued before analysis. CTU
                        analysis works properly only if there is exactly one
                        compilation action per source file. none(default in
                        non CTU mode): no uniqueing is done. strict: no
                        uniqueing is done, and an error is given if there is
                        more than one compilation action for a source file.
                        alpha(default in CTU mode): If there is more than one
                        compilation action for a source file, only the one is
                        kept that belongs to the alphabetically first
                        compilation target. If none of the above given, this
                        parameter should be a python regular expression.If
                        there is more than one compilation action for a
                        source, only the one is kept which matches the given
                        python regex. If more than one matches an error is
                        given. The whole compilation action text is searched
                        for match. (default: none)
  --report-hash {context-free}
                        EXPERIMENTAL feature. Specify the hash calculation
                        method for reports. If this option is not set, the
                        default calculation method for Clang Static Analyzer
                        will be context sensitive and for Clang Tidy it will
                        be context insensitive. If this option is set to
                        'context-free' bugs will be identified with the
                        CodeChecker generated context free hash for every
                        analyzers. USE WISELY AND AT YOUR OWN RISK!
  -n NAME, --name NAME  Annotate the run analysis with a custom name in the
                        created metadata file.
  --verbose {info,debug,debug_analyzer}
                        Set verbosity level.
```


### _Skip_ file <a name="skip"></a>

```
-i SKIPFILE, --ignore SKIPFILE, --skip SKIPFILE
                      Path to the Skipfile dictating which project files
                      should be omitted from analysis.
```

Skipfiles filter which files should or should not be analyzed. CodeChecker
reads the skipfile from **top to bottom and stops at the first matching pattern**
when deciding whether or not a file should be analyzed.

Each line in the skip file begins with a `-` or a `+`, followed by a path glob
pattern. `-` means that if a file matches a pattern it should **not** be
checked, `+` means that it should be.

 * Absolute directory paths should start with `/`.
 * Relative directory paths should start with `*`.
 * Path parts should start and end with `*`.
 * To skip everything use the `-*` mark. **Watch out for the order!**

#### Absolute path examples <a name="skip-abs-example"></a>

```
-/skip/all/files/in/directory/*
-/do/not/check/this.file
+/dir/do.check.this.file
-/dir/*
```

In the above example, every file under `/dir` **will be** skipped, except the
one explicitly specified to **be analyzed** (`/dir/do.check.this.file`).

#### Relative or partial path examples <a name="skip-rel-example"></a>

```
+*/my_project/my_lib_to_skip/important_file.cpp
-*/my_project/my_lib_to_skip*
-*/my_project/3pplib/*
+*/my_project/*
```

In the above example, `important_file.cpp` will be analyzed even if every file
where the path matches to `/my_project/my_lib_to_skip` will be skiped.  
Every other file where the path contains `/myproject` except the files in the 
`my_project/3pplib` will be analyzed.

The provided *shell-style* pattern is converted to a regex with the [fnmatch.translate](https://docs.python.org/2/library/fnmatch.html#fnmatch.translate).

### Analyzer configuration <a name="analyzer-configuration"></a>

```
analyzer arguments:
  --analyzers ANALYZER [ANALYZER ...]
                        Run analysis only with the analyzers specified.
                        Currently supported analyzers are: clangsa, clang-
                        tidy.
  --add-compiler-defaults
                        DEPRECATED. Always True. 
                        Retrieve compiler-specific configuration from the
                        compilers themselves, and use them with Clang. This is
                        used when the compiler on the system is special, e.g.
                        when doing cross-compilation.
  --capture-analysis-output
                        Store standard output and standard error of successful
                        analyzer invocations into the '<OUTPUT_DIR>/success'
                        directory.
  --saargs CLANGSA_ARGS_CFG_FILE
                        File containing argument which will be forwarded
                        verbatim for the Clang Static Analyzer.
  --tidyargs TIDY_ARGS_CFG_FILE
                        File containing argument which will be forwarded
                        verbatim for Clang-Tidy.
  --tidy-config TIDY_CONFIG
                        A file in YAML format containing the configuration of
                        clang-tidy checkers. The file can be dumped by
                        'CodeChecker analyzers --dump-config clang-tidy'
                        command.
  --timeout TIMEOUT     The amount of time (in seconds) that each analyzer can
                        spend, individually, to analyze the project. If the
                        analysis of a particular file takes longer than this
                        time, the analyzer is killed and the analysis is
                        considered as a failed one.
  --z3 {on,off}         Enable the z3 solver backend. This allows reasoning
                        over more complex queries, but performance is worse
                        than the default range-based constraint solver.
                        (default: off)
  --z3-refutation {on,off}
                        Switch on/off the Z3 SMT Solver backend to reduce
                        false positives. The results of the ranged based
                        constraint solver in the Clang Static Analyzer will be
                        cross checked with the Z3 SMT solver. This should not
                        cause that much of a slowdown compared to using the Z3
                        solver only. (default: on)
```

CodeChecker supports several analyzer tools. Currently, these analyzers are
the [_Clang Static Analyzer_](http://clang-analyzer.llvm.org) and
[_Clang-Tidy_](http://clang.llvm.org/extra/clang-tidy). `--analyzers` can be
used to specify which analyzer tool should be used (by default, all supported
are used). The tools are completely independent, so either can be omitted if
not present as they are provided by different binaries.

See [Configure Clang Static Analyzer and checkers](checker_and_analyzer_configuration.md)
documentation for a more detailed description how to use the `saargs`,
`tidyargs` and `z3` arguments.


#### Compiler-specific include path and define detection (cross compilation) <a name="include-path"></a>

Some of the include paths are hardcoded during compiler build. If a (cross)
compiler is used to build a project it is possible that the wrong include
paths are searched and the wrong headers will be included which causes
analyses to fail. These hardcoded include paths and defines can be marked for
automatically detection by specifying the `--add-compiler-defaults` flag.

CodeChecker will get the hardcoded values for the compilers set in the
`CC_LOGGER_GCC_LIKE` environment variable.

```sh
export CC_LOGGER_GCC_LIKE="gcc:g++:clang"
```

If there are still compilation errors after using the `--add-compiler-defaults`
argument, it is possible that the wrong build target architecture
(32bit, 64bit) is used. Please try to forward these compilation flags
to the analyzers:

 - `-m32` (32-bit build)
 - `-m64` (64-bit build)

GCC specific hard-coded values are detected during the analysis and
recorded int the `<report-directory>/compiler_info.json`.

If you want to run the analysis with a specific compiler configuration
instead of the auto-detection you can pass that to the
`--compiler-info-file compiler_info.json` parameter.

There are some implicit include paths (for example those which contain
`include-fixed` directory) which are used only by GCC. By default CodeChecker
doesn't collect them if `--skip-gcc-fix-include` flag is given. For
further information see [GCC incompatibilities](gcc_incompatibilities.md).

#### Forwarding compiler options <a name="forwarding-compiler-options"></a>

Forwarded options can modify the compilation actions logged by the build logger
or created by CMake (when exporting compile commands). The extra compiler
options can be given in config files which are provided by the flags
described below.

The config files can contain placeholders in `$(ENV_VAR)` format. If the
`ENV_VAR` environment variable is set then the placeholder is replaced to its
value. Otherwise an error message is logged saying that the variable is not
set, and in this case an empty string is inserted in the place of the
placeholder.

##### <a name="clang-static-analyzer"></a> _Clang Static Analyzer_

Use the `--saargs` argument to a file which contains compilation options.

```sh
CodeChecker analyze mylogfile.json --saargs extra_sa_compile_flags.txt -n myProject
```

Where the `extra_sa_compile_flags.txt` file contains additional compilation
options, for example:

```sh
-I~/include/for/analysis -I$(MY_LIB)/include -DDEBUG
```

(where `MY_LIB` is the path of a library code)

##### _Clang-Tidy_ <a name="clang-tidy"></a>

Use the `--tidyargs` argument to a file which contains compilation options.

```sh
CodeChecker analyze mylogfile.json --tidyargs extra_tidy_compile_flags.txt -n myProject
```

Where the `extra_tidy_compile_flags.txt` file contains additional compilation
flags.

Clang-Tidy requires a different format to add compilation options.
Compilation options can be added before (`-extra-arg-before=<string>`) and
after (`-extra-arg=<string>`) the original compilation options.

Example:

```sh
-extra-arg-before='-I~/include/for/analysis' -extra-arg-before='-I~/other/include/for/analysis/' -extra-arg-before='-I$(MY_LIB)/include' -extra-arg='-DDEBUG'
```

(where `MY_LIB` is the path of a library code)

### Toggling checkers <a name="toggling-checkers"></a>

The list of checkers to be used in the analysis can be fine-tuned with the
`--enable` and `--disable` options. See `codechecker-checkers` for the list of
available checkers in the binaries installed on your system.

```
checker configuration:

  -e checker/group/profile, --enable checker/group/profile
                        Set a checker (or checker group or checker profile)
                        to BE USED in the analysis.
  -d checker/group/profile, --disable checker/group/profile
                        Set a checker (or checker group or checker profile)
                        to BE PROHIBITED from use in the analysis.
  --enable-all          Force the running analyzers to use almost every
                        checker available. The checker groups 'alpha.',
                        'debug.' and 'osx.' (on Linux) are NOT enabled
                        automatically and must be EXPLICITLY specified.
                        WARNING! Enabling all checkers might result in the
                        analysis losing precision and stability, and could
                        even result in a total failure of the analysis. USE
                        WISELY AND AT YOUR OWN RISK!
```

Both `--enable` and `--disable` take individual checkers, checker groups or
checker profiles as their argument and there can be any number of such flags
specified. Flag order is important, subsequent options **overwrite** previously
specified ones. For example

```sh
--enable extreme --disable core.uninitialized --enable core.uninitialized.Assign
```

will enable every checker of the `extreme` profile that do not belong to the
 `core.uninitialized` group, with the exception of `core.uninitialized.Assign`,
which will be enabled after all.

Disabling certain checkers - such as the `core` group - is unsupported by
the LLVM/Clang community, and thus discouraged.

### Toggling compiler warnings <a name="toggling-warnings"></a>
Compiler warnings are diagnostic messages that report constructions that are
not inherently erroneous but that are risky or suggest there may have been an
error. Compiler warnings are named `clang-diagnostic-<warning-option>`, e.g.
Clang warning controlled by `-Wliteral-conversion` will be reported with check
name `clang-diagnostic-literal-conversion`.
You can fine-tune which warnings to use in the analysis by setting the enabled
and disabled flags starting from the bigger groups and going inwards. For
example

```sh
--enable Wunused --disable Wno-unused-parameter
```
or
```sh
--enable Wunused --disable Wunused-parameter
```
will enable every `unused` warnings except `unused-parameter`. These flags
should start with a capital `W` or `Wno-` prefix followed by the warning name
(E.g.: `-e Wliteral-conversion`, `-d Wno-literal-conversion` or
`-d Wliteral-conversion`). To turn off a compiler warning you can use the
negative form beginning with `Wno-` (e.g.: `--disable Wno-literal-conversion`)
or you can use the positive form beginning with `W` (e.g.:
`--enable Wliteral-conversion`). For more information see:
https://clang.llvm.org/docs/DiagnosticsReference.html.

**Note**: by default `-Wall` and `-Wextra` warnings are enabled.


#### Checker profiles <a name="checker-profiles"></a>

Checker profiles describe custom sets of enabled checks which can be specified
in the `{INSTALL_DIR}/config/config.json` file. Three built-in options are
available grouping checkers by their quality (measured by their false positive
rate): `default`, `sensitive` and `extreme`. In addition, profile `portability`
contains checkers for detecting platform-dependent code issues. These issues
can arise when migrating code from 32-bit to 64-bit architectures, and the root
causes of the bugs tend to be overflows, sign extensions and widening
conversions or casts. Detailed information about profiles can be retrieved by
the `CodeChecker checkers` command.

Note: `list` is a reserved keyword used to show all the available profiles and
thus should not be used as a profile name. Profile names should also be
different from checker(-group) names as they are enabled using the same syntax
and coinciding names could cause unintended behavior.


#### `--enable-all` <a name="enable-all"></a>

Specifying `--enable-all` will "force" CodeChecker to enable **every** checker
available in the analyzers. This presents an easy shortcut to force such an
analysis without the need of editing configuration files or supplying long
command-line arguments. However, `--enable-all` *might* result in the analysis
losing stability and precision, and worst case, might result in a complete and
utter failure in the analysis itself. **`--enable-all` may only be used at
your own risk!**

Even specifying `--enable-all` will **NOT** enable checkers from some special
checker groups, such as `alpha.` and `debug.`. `osx.` checkers are only enabled
if CodeChecker is run on a macOS machine. `--enable-all` can further be
fine-tuned with subsequent `--enable` and `--disable` arguments, for example

```sh
--enable-all --enable alpha --disable misc
```

can be used to "further" enable `alpha.` checkers, and disable `misc` ones.

### Cross Translation Unit (CTU) analysis mode <a name="ctu"></a>

If the `clang` static analyzer binary in your installation supports
[Cross Translation Unit analysis](http://llvm.org/devmtg/2017-03//2017/02/20/accepted-sessions.html#7),
CodeChecker can execute the analyzers with this mode enabled.

These options are only visible in `analyze` if CTU support is present. CTU
mode uses some extra storage space under the specified `--output-dir`.

```
cross translation unit analysis arguments:
  These arguments are only available if the Clang Static Analyzer supports
  Cross-TU analysis. By default, no such analysis is run when 'CodeChecker
  analyze' is called.

  --ctu, --ctu-all      Perform Cross Translation Unit (CTU) analysis, both
                        'collect' and 'analyze' phases. In this mode, the
                        extra files created by 'collect' are cleaned up after
                        the analysis.
  --ctu-collect         Perform the first, 'collect' phase of Cross-TU
                        analysis. This phase generates extra files needed by
                        CTU analysis, and puts them into '<OUTPUT_DIR>/ctu-
                        dir'. NOTE: If this argument is present, CodeChecker
                        will NOT execute the analyzers!
  --ctu-analyze         Perform the second, 'analyze' phase of Cross-TU
                        analysis, using already available extra files in
                        '<OUTPUT_DIR>/ctu-dir'. (These files will not be
                        cleaned up in this mode.)
  --ctu-on-the-fly      If specified, the 'collect' phase will not create the
                        extra AST dumps, but rather analysis will be run with
                        an in-memory recompilation of the source files.
```

### Statistical analysis mode <a name="statistical"></a>

If the `clang` static analyzer binary in your installation supports
statistical checkers CodeChecker can execute the analyzers
with this mode enabled.

These options are only visible in `analyze` if the experimental
statistical analysis support is present.

```
EXPERIMENTAL statistics analysis feature arguments:
  These arguments are only available if the Clang Static Analyzer supports
  Statistics-based analysis (e.g. statisticsCollector.ReturnValueCheck,
  statisticsCollector.SpecialReturnValue checkers are available).

  --stats-collect STATS_OUTPUT, --stats-collect STATS_OUTPUT
                        EXPERIMENTAL feature. Perform the first, 'collect'
                        phase of Statistical analysis. This phase generates
                        extra files needed by statistics analysis, and puts
                        them into '<STATS_OUTPUT>'. NOTE: If this argument is
                        present, CodeChecker will NOT execute the analyzers!
  --stats-use STATS_DIR, --stats-use STATS_DIR
                        EXPERIMENTAL feature. Use the previously generated
                        statistics results for the analysis from the given
                        '<STATS_DIR>'.
  --stats               EXPERIMENTAL feature. Perform both phases of
                        Statistical analysis. This phase generates extra files
                        needed by statistics analysis and enables the
                        statistical checkers. No need to enable them
                        explicitly.
 --stats-min-sample-count STATS_MIN_SAMPLE_COUNT, --stats-min-sample-count STATS_MIN_SAMPLE_COUNT
                        EXPERIMENTAL feature. Minimum number of samples
                        (function call occurrences) to be collected for a
                        statistics to be relevant.(default: 10)
  --stats-relevance-threshold STATS_RELEVANCE_THRESHOLD, --stats-relevance-threshold STATS_RELEVANCE_THRESHOLD
                        EXPERIMENTAL feature. The minimum ratio of
                        calls of function f that must have a certain property
                        to consider it true for that function (calculated as calls 
                        with a property/all calls). CodeChecker will warn for calls 
                        of f that do not have that property.(default: 0.85)
 
```

## `parse` <a name="parse"></a>

`parse` is used to read previously created machine-readable analysis results
(such as `plist` files), usually previously generated by `CodeChecker analyze`.
`parse` prints analysis results to the standard output.

```
usage: CodeChecker parse [-h] [-t {plist}] [--export {html}]
                         [-o OUTPUT_PATH] [-c] [--suppress SUPPRESS]
                         [--export-source-suppress] [--print-steps]
                         [--verbose {info,debug,debug_analyzer}]
                         file/folder [file/folder ...]

Parse and pretty-print the summary and results from one or more 'codechecker-
analyze' result files. Bugs which are commented by using "false_positive",
"suppress" and "intentional" source code comments will not be printed by the
`parse` command.

positional arguments:
  file/folder           The analysis result files and/or folders containing
                        analysis results which should be parsed and printed.

optional arguments:
  -h, --help            show this help message and exit
  -t {plist}, --type {plist}, --input-format {plist}
                        Specify the format the analysis results were created
                        as. (default: plist)
  --suppress SUPPRESS   Path of the suppress file to use. Records in the
                        suppress file are used to suppress the display of
                        certain results when parsing the analyses' report.
                        (Reports to an analysis result can also be suppressed
                        in the source code -- please consult the manual on how
                        to do so.) NOTE: The suppress file relies on the "bug
                        identifier" generated by the analyzers which is
                        experimental, take care when relying on it.
  --export-source-suppress
                        Write suppress data from the suppression annotations
                        found in the source files that were analyzed earlier
                        that created the results. The suppression information
                        will be written to the parameter of '--suppress'.
  --print-steps         Print the steps the analyzers took in finding the
                        reported defect.
  -i SKIPFILE, --ignore SKIPFILE, --skip SKIPFILE
                        Path to the Skipfile dictating which project files
                        should be omitted from analysis. Please consult the
                        User guide on how a Skipfile should be laid out.
  --trim-path-prefix [TRIM_PATH_PREFIX [TRIM_PATH_PREFIX ...]]
                        Removes leading path from files which will be
                        printed. So if you have /a/b/c/x.cpp and /a/b/c/y.cpp
                        then by removing "/a/b/" prefix will print files like
                        c/x.cpp and c/y.cpp. If multiple prefix is given, the
                        longest match will be removed.                        
  --verbose {info,debug,debug_analyzer}
                        Set verbosity level.

export arguments:
  -e {html}, --export {html}
                        Specify extra output format type. (default: None)
  -o OUTPUT_PATH, --output OUTPUT_PATH
                        Store the output in the given folder. (default: None)
  -c, --clean           DEPRECATED. Delete output results stored in the output
                        directory. (By default, it would keep output files and
                        overwrites only those that belongs to a plist file
                        given by the input argument. (default: True)
```

For example, if the analysis was run like:

```sh
CodeChecker analyze ../codechecker_myProject_build.log -o my_plists
```

then the results of the analysis can be printed with

```sh
CodeChecker parse ./my_plists
```

## `checkers`<a name="checkers"></a>

List the checkers available in the installed analyzers which can be used when
performing an analysis.

By default, `CodeChecker checkers` will list all checkers, one per each row,
providing a quick overview on which checkers are available in the analyzers.

```
usage: CodeChecker checkers [-h] [--analyzers ANALYZER [ANALYZER ...]]
                            [--details] [--profile {PROFILE/list}]
                            [--only-enabled | --only-disabled]
                            [-o {rows,table,csv,json}]
                            [--verbose {info,debug,debug_analyzer}]

Get the list of checkers available and their enabled status in the supported
analyzers.

optional arguments:
  -h, --help            show this help message and exit
  --analyzers ANALYZER [ANALYZER ...]
                        Show checkers only from the analyzers specified.
                        Currently supported analyzers are: clangsa, clang-
                        tidy.
  --details             Show details about the checker, such as description,
                        if available.
  --profile {PROFILE/list}
                        List checkers enabled by the selected profile.
                        'list' is a special option showing details about
                        profiles collectively.
  --only-enabled        Show only the enabled checkers.
  --only-disabled       Show only the disabled checkers.
  -o {rows,table,csv,json}, --output {rows,table,csv,json}
                        The format to list the applicable checkers as.
                        (default: rows)
  --verbose {info,debug,debug_analyzer}
                        Set verbosity level.
```

The list provided by default is formatted for easy machine and human
reading. Use the `--only-` options (`--only-enabled` and `--only-disabled`) to
filter the list if you wish to see just the enabled/disabled checkers.

A detailed view of the available checkers is available via `--details`. In the
*detailed view*, checker status, severity and description (if available) is
also printed.

A machine-readable `csv` or `json` output can be generated by supplying the
`--output csv` or `--output json` argument.

The _default_ list of enabled and disabled checkers can be altered by editing
`{INSTALL_DIR}/config/config.json`. Note, that this file is overwritten when
the package is reinstalled!

## <a name="analyzers"></a> 6. `analyzers` mode

List the available and supported analyzers installed on the system. This command
can be used to retrieve the to-be-used analyzers' install path and version
information.

By default, this command only lists the names of the available analyzers (with
respect to the environment CodeChecker is run in).

```
usage: CodeChecker analyzers [-h] [--all] [--details]
                             [-o {rows,table,csv,json}]
                             [--verbose {info,debug,debug_analyzer}]

Get the list of available and supported analyzers, querying their version and
actual binary executed.

optional arguments:
  -h, --help            show this help message and exit
  --all                 Show all supported analyzers, not just the available
                        ones.
  --details             Show details about the analyzers, not just their
                        names.
  --dump-config {clangsa,clang-tidy}
                        Dump the available checker options for the given
                        analyzer to the standard output. Currently only clang-
                        tidy supports this option. The output can be
                        redirected to a file named .clang-tidy. If this file
                        is placed to the project directory then the options
                        are applied to the files under that directory. This
                        config file can also be provided via 'CodeChecker
                        analyze' and 'CodeChecker check' commands.
  -o {rows,table,csv,json}, --output {rows,table,csv,json}
                        Specify the format of the output list. (default: rows)
  --verbose {info,debug,debug_analyzer}
                        Set verbosity level.
```

A detailed view of the available analyzers is available via `--details`. In the
*detailed view*, version string and install path is also printed.

A machine-readable `csv` or `json` output can be generated by supplying the
`--output csv` or `--output json` argument.
