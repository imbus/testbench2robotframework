---
sidebar_position: 1
---

# Configuration Reference

This page lists **every** configuration option: where it applies, its accepted
values, its default, and how to set it on the command line and in a configuration
file.

## How to configure

You can configure TestBench2RobotFramework in three ways, and they can be
combined:

1. **Command-line options** — passed directly to a command, best for one-off runs
   and overrides.
2. **Configuration files** — `pyproject.toml`, `robot.toml` or a workspace-local
   `.robot.toml`, best for reusable, team-wide settings. All options live under a
   `[tool.testbench2robotframework]` section.
3. **A `-c` / `--config` file** — an explicit TOML **or** JSON file.

### Precedence

When the same option is set in several places, the last one wins:

1. Built-in defaults
2. `pyproject.toml`
3. `robot.toml`
4. `.robot.toml`
5. Command-line options

The three automatic files are searched upwards from the current working
directory and merged **per top-level key** (a whole table like `library-mapping`
is replaced, not merged entry by entry).

:::caution
`-c` / `--config` **replaces** the automatic file lookup. When it is given, only
that one file is read and any `pyproject.toml` / `robot.toml` / `.robot.toml` in
the project is ignored. A TOML file needs the `[tool.testbench2robotframework]`
section; a JSON file holds the keys directly at the top level (see
[JSON configuration](./pyproject_config.md#json-configuration)).
:::

### How an option maps between CLI and file

The option name is the same in both places; only the syntax differs by type:

| Type | Command line | Configuration file (TOML) |
|------|--------------|---------------------------|
| Text / number | `--phase-pattern "..."` | `phase-pattern = "..."` |
| Boolean flag | `--fully-qualified` (present = true) | `fully-qualified = true` |
| Boolean pair | `--clean` / `--no-clean` | `clean = true` / `false` |
| List (repeatable) | `--library-root RF --library-root RF-Library` | `library-root = ["RF", "RF-Library"]` |
| Mapping | `--library-mapping "name:import"` (repeatable) | a `[tool.testbench2robotframework.library-mapping]` table |

Options **not** available on the command line can only be set in a configuration
file. This is noted per option below.

---

## All options at a glance

`G` = affects `generate-tests`, `F` = affects `fetch-results`.

| Option | CLI | File | Command | Values (default) |
|--------|:---:|:----:|:-------:|------------------|
| [`output-directory`](#output-directory) | `-d` | ✅ | G · F | path or `.zip` (`{root}/Generated`) |
| [`clean`](#clean) | `--clean`/`--no-clean` | ✅ | G | bool (`true`) |
| [`clean-mode`](#clean-mode) | — | ✅ | G | `GENERATED` \| `ALL` (`GENERATED`) |
| [`create-output-zip`](#create-output-zip) | — | ✅ | G | bool (`false`) |
| [`fully-qualified`](#fully-qualified) | `--fully-qualified` | ✅ | G | bool (`false`) |
| [`log-suite-numbering`](#log-suite-numbering) | `--log-suite-numbering` | ✅ | G | bool (`false`) |
| [`include-blocked`](#include-blocked) | `--include-blocked` | ✅ | G | bool (`false`) |
| [`compound-keyword-logging`](#compound-keyword-logging) | `--compound-keyword-logging` | ✅ | G | `GROUP` \| `COMMENT` \| `NONE` (`GROUP`) |
| [`testcase-splitting-regex`](#testcase-splitting-regex) | — | ✅ | G | regex (`.*StopWithRestart.*`) |
| [`phase-pattern`](#phase-pattern) | — | ✅ | G · F | pattern (`{testcase} : Phase {index}/{length}`) |
| [`library-regex`](#library-regex--resource-regex) | `--library-regex` | ✅ | G | list of regex (see below) |
| [`resource-regex`](#library-regex--resource-regex) | `--resource-regex` | ✅ | G | list of regex (see below) |
| [`library-root`](#library-root--resource-root) | `--library-root` | ✅ | G | list (`["RF", "RF-Library"]`) |
| [`resource-root`](#library-root--resource-root) | `--resource-root` | ✅ | G | list (`["RF-Resource"]`) |
| [`resource-directory`](#resource-directory) | `--resource-directory` | ✅ | G | path (empty) |
| [`resource-directory-regex`](#resource-directory-regex) | `--resource-directory-regex` | ✅ | G | regex (`.*\[Robot-Resources\].*`) |
| [`library-mapping`](#library-mapping--resource-mapping) | `--library-mapping` | ✅ | G | mapping (`{}`) |
| [`resource-mapping`](#library-mapping--resource-mapping) | `--resource-mapping` | ✅ | G | mapping (`{}`) |
| [`forced-import`](#forced-import) | — | ✅ | G | table of lists (`{}`) |
| [`metadata`](#metadata) | `--metadata` | ✅ | G | mapping (`{}`) |
| [`merge-protocol`](#merge-protocol) | `--no-merge-protocol` | ✅ | F | bool (`true`) |
| [`keyword-comment-style`](#keyword-comment-style) | — | ✅ | F | `STRUCTURED` \| `FLAT` (`STRUCTURED`) |
| [`keyword-comment-max-depth`](#keyword-comment-max-depth) | — | ✅ | F | int (`5`) |
| [`keyword-comment-max-rows`](#keyword-comment-max-rows) | — | ✅ | F | int, `0` = no limit (`300`) |
| [`keyword-comment-log-level`](#keyword-comment-log-level) | — | ✅ | F | `TRACE`…`FAIL` (`TRACE`) |
| [`reference-behaviour`](#reference-behaviour) | — | ✅ | F | `ATTACHMENT` \| `REFERENCE` \| `NONE` (`ATTACHMENT`) |
| [`attachment-conflict-behaviour`](#attachment-conflict-behaviour) | — | ✅ | F | `ERROR` \| `USE_NEW` \| `USE_EXISTING` \| `RENAME_NEW` (`USE_EXISTING`) |
| [`console-logging`](#console-logging--file-logging) | — | ✅ | G · F | table |
| [`file-logging`](#console-logging--file-logging) | — | ✅ | G · F | table |

---

## Output

### `output-directory`

Where generated suites (or, for `fetch-results`, the updated report) are written.
A plain path is treated as a directory; a `.zip` path packs the output into a ZIP
archive instead. The placeholder `{root}` at the start is replaced by the
absolute path of the directory the command runs in.

- **Values:** a directory path or a `.zip` file path. Default: `{root}/Generated`.
- **CLI:** `-d` / `--output-directory`.

```bash
testbench2robotframework generate-tests -d ./Generated my_report.zip
testbench2robotframework generate-tests -d ./suites.zip my_report.zip
```
```toml
output-directory = "{root}/Generated"
```

### `create-output-zip`

For `generate-tests` only: in addition to the normal directory output, also
produce a ZIP archive of the generated suites next to it. Independent of using a
`.zip` `output-directory`. **Configuration file only.**

- **Values:** `true` / `false`. Default: `false`.

```toml
create-output-zip = true
```

---

## Cleaning the output directory

### `clean`

Whether previously generated suites are removed before generating. Cleaning is
**selective**: only `.robot` files that carry the generated
`Metadata    UniqueID` marker are deleted, together with directories left empty by
that. Hand-written suites, resource files and any other content in the output
directory are kept. A `.zip` output target is removed as a whole.

- **Values:** `true` / `false`. Default: `true` (in a configuration file). On the
  command line, without either flag the configuration decides.
- **CLI:** the flag pair `--clean` / `--no-clean`. Use `--no-clean` to generate
  additively (nothing is removed).

```bash
testbench2robotframework generate-tests --clean my_report.zip     # remove old generated suites first
testbench2robotframework generate-tests --no-clean my_report.zip  # keep everything, add to it
```
```toml
clean = true
```

### `clean-mode`

What `clean` removes. `GENERATED` (default) is the selective behaviour described
above. `ALL` restores the pre-2.0 behaviour of deleting the **entire** output
directory, including files this tool did not write — use it with care and point
`output-directory` at a directory that contains nothing else. **Configuration
file only**, deliberately without a CLI flag.

- **Values:** `GENERATED` \| `ALL`. Default: `GENERATED`.

```toml
clean = true
clean-mode = "ALL"
```

---

## Suite generation

### `fully-qualified`

Call Robot Framework keywords by their fully qualified name
(`Browser.Click`) instead of the plain keyword name. Use this when
two imported libraries or resources provide a keyword of the same name, to make
the generated calls unambiguous.

- **Values:** `true` / `false`. Default: `false`.
- **CLI:** `--fully-qualified` (flag).

```bash
testbench2robotframework generate-tests --fully-qualified my_report.zip
```
```toml
fully-qualified = true
```

### `log-suite-numbering`

Keeps the TestBench numbering visible in the Robot Framework **suite name**. The
numbering always prefixes the generated file name; by default the prefix ends
with a double underscore (`01__Login.robot`), which Robot strips from the
displayed suite name. With this option the prefix uses a single underscore
(`01_Login.robot`), so the numbering stays part of the visible suite name.

- **Values:** `true` / `false`. Default: `false`.
- **CLI:** `--log-suite-numbering` (flag).

```bash
testbench2robotframework generate-tests --log-suite-numbering my_report.zip
```
```toml
log-suite-numbering = true
```

### `include-blocked`

By default, test elements whose TestBench execution status is `Blocked` are not
generated — blocked test cases are left out of their suite, a blocked test case
set produces no `.robot` file, and a blocked test theme drops its whole subtree.
Enable this option to generate them anyway.

- **Values:** `true` / `false`. Default: `false`.
- **CLI:** `--include-blocked` (flag).

```bash
testbench2robotframework generate-tests --include-blocked my_report.zip
```
```toml
include-blocked = true
```

### `compound-keyword-logging`

How compound (higher-level) TestBench keywords are represented in the generated
suite. `GROUP` wraps their child keywords in a Robot Framework `GROUP` block (this
needs Robot Framework 7.2+; on older versions it falls back to `COMMENT` with a
warning). `COMMENT` emits the compound keyword as a comment above its inlined
children. `NONE` inlines the children without any marker.

- **Values:** `GROUP` \| `COMMENT` \| `NONE`. Default: `GROUP`.
- **CLI:** `--compound-keyword-logging`.

```bash
testbench2robotframework generate-tests --compound-keyword-logging COMMENT my_report.zip
```
```toml
compound-keyword-logging = "GROUP"
```

### `testcase-splitting-regex`

A regular expression matched against the subdivision path of each interaction. An
interaction that matches **splits** the TestBench test case into several Robot
Framework tests at that point — useful for keywords that restart the system under
test. See [Test Case Splitting](../usage/generate_tests.md#test-case-splitting).
**Configuration file only.**

- **Values:** a regular expression. Default: `.*StopWithRestart.*`.

```toml
testcase-splitting-regex = ".*StopWithRestart.*"
```

### `phase-pattern`

The naming pattern for the Robot Framework tests produced by test case splitting.
`{testcase}` is the test case unique ID, `{index}` the phase number and
`{length}` the total number of phases. `fetch-results` uses the **same** pattern
to recombine the phases into one TestBench result, so it must match the value used
for `generate-tests`. Affects both commands. **Configuration file only.**

- **Values:** a pattern using `{testcase}`, `{index}`, `{length}`.
  Default: `{testcase} : Phase {index}/{length}`.

```toml
phase-pattern = "{testcase} : Phase {index}/{length}"
```

---

## Mapping keywords to libraries and resources

These options control which Robot Framework `Library` / `Resource` imports the
generated suites receive. For the full picture of how to structure TestBench
subdivisions, see
[Modeling Keywords in TestBench](../usage/generate_tests.md#modeling-keywords-in-testbench).

### `library-regex` / `resource-regex`

Lists of regular expressions matched (case-insensitively) against the subdivision
path of a keyword to decide whether it belongs to a Robot Framework **library**
or **resource file**, and which name to import. Each pattern must mark the name
with a named group (`resourceName`, `libraryName` or `name`) or with exactly one
capture group; see
[Subdivision Patterns](./pyproject_config.md#subdivision-patterns) for the rules.
Invalid or ambiguous patterns are rejected at startup.

- **Values:** a list of regular expressions.
  `library-regex` default: `['(?:.*\.)?(?P<resourceName>[^.]+?)\s*\[Robot-Library\].*']`.
  `resource-regex` default: `['(?:.*\.)?(?P<resourceName>[^.]+?)\s*\[Robot-Resource\].*']`.
- **CLI:** `--library-regex` / `--resource-regex`, repeatable.

```bash
testbench2robotframework generate-tests --library-regex "(?P<resourceName>\w+) \[Lib\]" my_report.zip
```
```toml
library-regex = ['(?:.*\.)?(?P<resourceName>[^.]+?)\s*\[Robot-Library\].*']
resource-regex = ['(?:.*\.)?(?P<resourceName>[^.]+?)\s*\[Robot-Resource\].*']
```

### `library-root` / `resource-root`

An alternative to the regex conventions: root subdivisions whose **direct
children** are the library / resource names. A keyword under `RF.Browser`
becomes `Library    Browser` when `RF` is a library root.

- **Values:** a list of subdivision names.
  `library-root` default: `["RF", "RF-Library"]`. `resource-root` default:
  `["RF-Resource"]`.
- **CLI:** `--library-root` / `--resource-root`, repeatable.

```bash
testbench2robotframework generate-tests --library-root RF --library-root RF-Library my_report.zip
```
```toml
library-root = ["RF", "RF-Library"]
resource-root = ["RF-Resource"]
```

### `resource-directory`

The base directory for generated `Resource` imports. `Common [Robot-Resource]`
becomes `<resource-directory>/Common.resource`. It is **empty** by default, so
resources are imported by plain file name and resolved by Robot Framework
relative to each generated suite. Set an absolute location (e.g. `{root}/Resources`)
for a single fixed resource directory. The placeholders `{root}` and, in
`resource-mapping` values, `{resourceDirectory}` are substituted at the start of a
value.

- **Values:** a directory path. Default: empty.
- **CLI:** `--resource-directory`.

```bash
testbench2robotframework generate-tests --resource-directory "{root}/Resources" my_report.zip
```
```toml
resource-directory = "{root}/Resources"
```

### `resource-directory-regex`

A **marker** pattern locating the subdivision that corresponds to the resource
directory. Subdivisions between the match and the resource itself become
subdirectories of `resource-directory`. Unlike `library-regex`/`resource-regex`,
this pattern extracts no name and needs no capture groups; it is searched
(case-insensitively) within each path segment. An expression that does not compile
is rejected at startup.

- **Values:** a regular expression. Default: `.*\[Robot-Resources\].*`.
- **CLI:** `--resource-directory-regex`.

```toml
resource-directory-regex = ".*\\[Robot-Resources\\].*"
```

### `library-mapping` / `resource-mapping`

Override the import statement produced for a matched library / resource name. Use
this to add library arguments, point a resource at a specific path, or import a
remote library. The key is the name as identified by the patterns/roots above; the
value is the full import statement (arguments separated by the usual Robot
Framework whitespace). `{root}` and `{resourceDirectory}` placeholders are
substituted.

- **Values:** a mapping of name → import statement. Default: `{}`.
- **CLI:** `--library-mapping` / `--resource-mapping` as `"name:import"` pairs,
  repeatable.

```bash
testbench2robotframework generate-tests \
  --library-mapping "Browser:Browser    timeout=10s" my_report.zip
```
```toml
[tool.testbench2robotframework.library-mapping]
Browser = "Browser    timeout=10s    run_on_failure=Take Screenshot"
RoboSAPiens = "RoboSAPiens    language=de"

[tool.testbench2robotframework.resource-mapping]
Common = "{root}/shared/Common.resource"
MyOtherKeywords = "{resourceDirectory}/subdir/MyOtherKeywords.resource"
```

### `forced-import`

Libraries, resources and variable files that are imported into **every** generated
suite, regardless of the keywords it uses. Useful for a project-wide variables
file or a library that is always needed. **Configuration file only.**

- **Values:** a table with `libraries`, `resources` and `variables` lists.
  Default: all empty.

```toml
[tool.testbench2robotframework.forced-import]
libraries = ["Collections"]
resources = ["common.resource"]
variables = ["variables.py"]
```

### `metadata`

Extra `Metadata` entries added to the settings of every generated suite. A value
may contain `{$tcs...}` placeholders that are evaluated against the TestBench test
case set model — e.g. `{$tcs.spec.responsible.name}` inserts the responsible
person. The names `UniqueID`, `Name` and `Numbering` are reserved (they are the
markers `fetch-results` matches on) and cannot be overridden.

- **Values:** a mapping of metadata name → value. Default: `{}`.
- **CLI:** `--metadata` as `"key:value"` pairs, repeatable.

```bash
testbench2robotframework generate-tests --metadata "Team:Payments" my_report.zip
```
```toml
[tool.testbench2robotframework.metadata]
Team = "Payments"
Responsible = "{$tcs.spec.responsible.name}"
```

---

## Result write-back (`fetch-results`)

### `merge-protocol`

Whether results are **merged** into the `protocol.json` already contained in the
report. When merging, executions the current Robot run covers are replaced,
executions it does not cover are kept, and the verdicts of test case sets and test
themes are recomputed over the merged set. Disable it to overwrite the protocol
with only the current run's results.

- **Values:** `true` / `false`. Default: `true`.
- **CLI:** `--no-merge-protocol` (turns merging off).

```bash
testbench2robotframework fetch-results --no-merge-protocol output.xml my_report.zip
```
```toml
merge-protocol = true
```

### `keyword-comment-style`

How the execution comment of a keyword is rendered. `STRUCTURED` shows the whole
Robot Framework keyword structure (sub keywords, control structures, loop
iterations) with the log messages of each. `FLAT` writes the plain list of log
messages of earlier versions. **Configuration file only.**

- **Values:** `STRUCTURED` \| `FLAT`. Default: `STRUCTURED`.

```toml
keyword-comment-style = "STRUCTURED"
```

### `keyword-comment-max-depth`

The nesting depth up to which the keyword structure is shown in a `STRUCTURED`
comment. Deeper keywords are folded away, but their **log messages are still
shown** — only the structure disappears, with a note naming the number of hidden
sub keywords. **Configuration file only.**

- **Values:** an integer. Default: `5`.

```toml
keyword-comment-max-depth = 5
```

### `keyword-comment-max-rows`

The maximum number of table rows per keyword comment. A comment that would exceed
it is truncated, ending with a `... truncated, see the Robot Framework log` note.
`0` disables the limit. **Configuration file only.**

- **Values:** an integer, `0` = no limit. Default: `300`.

```toml
keyword-comment-max-rows = 300
```

### `keyword-comment-log-level`

The lowest Robot Framework log level shown in a keyword comment, with Robot's own
threshold semantics: a message is shown when its level is at or above the
configured one. `TRACE` (the default) filters nothing. Note that `TRACE`/`DEBUG`
messages only exist in the results when the Robot run itself used
`--loglevel DEBUG`/`TRACE`. **Configuration file only.**

- **Values:** `TRACE` \| `DEBUG` \| `INFO` \| `WARN` \| `ERROR` \| `FAIL`.
  Default: `TRACE`.

```toml
keyword-comment-log-level = "TRACE"
```

### `reference-behaviour`

How references found in test messages (via `itb-reference:` markers) are handled
when writing results back. `ATTACHMENT` copies the referenced file into the report
as an attachment, `REFERENCE` stores it as a reference, `NONE` ignores references.
**Configuration file only.**

- **Values:** `ATTACHMENT` \| `REFERENCE` \| `NONE`. Default: `ATTACHMENT`.

```toml
reference-behaviour = "ATTACHMENT"
```

### `attachment-conflict-behaviour`

What happens when an attachment with the same name already exists in the report.
`USE_EXISTING` keeps the existing file, `USE_NEW` replaces it, `RENAME_NEW` stores
the new file under a unique name, and `ERROR` aborts. **Configuration file only.**

- **Values:** `ERROR` \| `USE_NEW` \| `USE_EXISTING` \| `RENAME_NEW`.
  Default: `USE_EXISTING`.

```toml
attachment-conflict-behaviour = "USE_EXISTING"
```

---

## Logging

### `console-logging` / `file-logging`

The log level and format of the tool's own console output and its optional log
file. Both apply to `generate-tests` and `fetch-results`. **Configuration file
only.**

- **Values:** a table with `logLevel`, `logFormat` (and, for `file-logging`,
  `fileName`). Console defaults to level `INFO`; file logging defaults to level
  `DEBUG` and file `testbench2robotframework.log`.

```toml
[tool.testbench2robotframework.console-logging]
logLevel = "INFO"
logFormat = "%(levelname)s: %(message)s"

[tool.testbench2robotframework.file-logging]
logLevel = "DEBUG"
logFormat = "%(asctime)s - %(filename)s:%(lineno)d - %(levelname)8s - %(message)s"
fileName = "testbench2robotframework.log"
```

---

See [Configuration Files](./pyproject_config.md) for how configuration files are
found, merged and written, and [Command-Line Usage](./cli_options.md) for how the
command line is structured.
