---
sidebar_position: 2
---

# Command-Line Usage

This page explains how the command line is structured and how to write option
values. It does **not** repeat every option — each one, with its accepted values
and default, lives in the [Configuration Reference](./overview.md).

## Structure of a command

Everything runs through two subcommands:

```bash
testbench2robotframework generate-tests [OPTIONS] <testbench-report>
testbench2robotframework fetch-results  [OPTIONS] <robot-output.xml> <testbench-report>
```

- `generate-tests` takes one positional argument: the TestBench JSON report
  (a directory or `.zip`).
- `fetch-results` takes two: the Robot Framework `output.xml` first, then the
  TestBench report the suites were generated from.

The short entry point `tb2robot` is an alias for `testbench2robotframework`.

Two options work on the group itself, before the subcommand:

```bash
testbench2robotframework --help        # or -h
testbench2robotframework --version     # or -v — tool, Robot Framework, Python and supported TestBench versions
```

Each subcommand also has its own `--help`:

```bash
testbench2robotframework generate-tests --help
testbench2robotframework fetch-results --help
```

## Writing option values

The option name on the command line is the same as in a configuration file; only
the syntax differs. Every option belongs to one of these shapes.

**Text and paths** take a value:

```bash
--output-directory ./Generated
--phase-pattern "{testcase} : Phase {index}/{length}"
```

**Simple flags** are either present (true) or absent (false):

```bash
--fully-qualified --include-blocked --log-suite-numbering
```

**The clean flag is a pair.** `--clean` and `--no-clean` are two spellings of one
tri-state option. Give neither and the configuration file decides (default:
clean); give one to force it:

```bash
--clean         # remove previously generated suites first
--no-clean      # keep them and generate additively
```

**List options are repeatable** — pass the flag once per value:

```bash
--library-root RF --library-root RF-Library
--library-regex '(?:.*\.)?(?P<resourceName>[^.]+?)\s*\[Robot-Library\].*'
```

**Mapping options take a `name:value` pair** and are also repeatable. The part
before the first colon is the key; everything after it is the value (so the value
may itself contain colons):

```bash
--library-mapping "RoboSAPiens:RoboSAPiens    language=de"
--metadata "Responsible:Jane Doe" --metadata "Environment:staging"
```

A value that is not in `name:value` form is rejected with a clear error.

## Choosing an explicit configuration file

`-c` / `--config` points at one TOML **or** JSON file and **replaces** the
automatic `pyproject.toml` / `robot.toml` / `.robot.toml` lookup — when it is
given, those project files are ignored:

```bash
testbench2robotframework generate-tests -c ./my-config.toml my_report.zip
```

How the automatic files are found and merged, and how a config file is written,
is covered in [Configuration Files](./pyproject_config.md).

## Precedence

Command-line options sit at the top of the precedence chain: they override the
configuration files, which override the built-in defaults. The full order is in
[Precedence](./overview.md#precedence).

## Examples

Generate into a chosen directory, keeping existing suites, with grouped compound
keywords and qualified keyword names:

```bash
testbench2robotframework generate-tests \
  -d ./Generated \
  --no-clean \
  --compound-keyword-logging GROUP \
  --fully-qualified \
  my_report.zip
```

Write the results of a run back into a new report, overwriting the protocol
instead of merging:

```bash
testbench2robotframework fetch-results \
  -d ./updated_report.zip \
  --no-merge-protocol \
  ./results/output.xml \
  my_report.zip
```

For what each option does and its accepted values, see the
[Configuration Reference](./overview.md).
