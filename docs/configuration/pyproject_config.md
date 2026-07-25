---
sidebar_position: 3
---

# Configuration Files

A configuration file keeps your settings in one place so every run — locally and
in CI — behaves the same. This page explains **which files are read, how they are
found and merged, and how to write their values**. What each individual option
does lives in the [Configuration Reference](./overview.md); link into it rather
than memorising the keys.

## Which files are read

TestBench2RobotFramework reads its settings from three files, all sharing one
format:

| File | Purpose |
|------|---------|
| `pyproject.toml` | project-wide settings, alongside your other Python tooling |
| `robot.toml` | project-wide settings when you have no `pyproject.toml` |
| `.robot.toml` | workspace-local overrides, typically not committed |

In all three, the settings live under a `[tool.testbench2robotframework]` section.

Alternatively, point `-c` / `--config` at one explicit file (TOML **or** JSON).
That **replaces** the automatic lookup below — see
[Command-Line Usage](./cli_options.md#choosing-an-explicit-configuration-file)
and [JSON configuration](#json-configuration).

## Lookup and merge strategy

Each of the three file names is searched for **upwards** from the current working
directory: the tool walks from the directory it runs in through its parent
directories and uses the first match of each name. This lets a nested project
directory inherit a `pyproject.toml` that sits at the repository root.

When more than one file is found, their `[tool.testbench2robotframework]` sections
are merged **per top-level key** in this order, the later file winning:

```
built-in defaults  →  pyproject.toml  →  robot.toml  →  .robot.toml  →  CLI options
```

:::caution
Merging is per top-level key, not deep. A whole table such as `library-mapping` is
replaced as a unit — if `.robot.toml` defines `[tool.testbench2robotframework.library-mapping]`,
it supersedes the entire mapping from `pyproject.toml` rather than adding to it.
:::

The complete precedence order, including the command line, is in
[Precedence](./overview.md#precedence).

## TOML value syntax

Each option type is written a particular way in TOML:

```toml
[tool.testbench2robotframework]

# text / paths — quoted strings
output-directory = "{root}/Generated"
phase-pattern = "{testcase} : Phase {index}/{length}"

# booleans
clean = true
fully-qualified = false

# integers
keyword-comment-max-depth = 5

# lists — for repeatable options such as the roots and regex patterns
library-root = ["RF", "RF-Library"]
library-regex = ['(?:.*\.)?(?P<resourceName>[^.]+?)\s*\[Robot-Library\].*']
```

:::tip
Write regular expressions as **single-quoted** TOML strings (`'...'`). In a
single-quoted string a backslash is literal, so a pattern like
`\s*\[Robot-Library\]` needs no doubling. In a double-quoted string you would have
to escape every backslash (`"\\s*\\[Robot-Library\\]"`).
:::

Mappings and other grouped settings are their own **sub-tables**, named
`[tool.testbench2robotframework.<option>]`:

```toml
[tool.testbench2robotframework.library-mapping]
Browser = "Browser    timeout=10s    run_on_failure=Take Screenshot"
RoboSAPiens = "RoboSAPiens    language=de"

[tool.testbench2robotframework.metadata]
Responsible = "{$tcs.spec.responsible.name}"
```

The options that use a sub-table are `library-mapping`, `resource-mapping`,
`metadata`, `forced-import`, `console-logging` and `file-logging`; their contents
are documented with each option in the
[Configuration Reference](./overview.md).

### Path placeholders

Two placeholders are substituted at the **start** of a path value:

- `{root}` — the directory `testbench2robotframework` runs in. Usable in
  `output-directory`, `resource-directory` and `resource-mapping` values.
- `{resourceDirectory}` — the configured `resource-directory`. Usable in
  `resource-mapping` values only.

```toml
output-directory = "{root}/Generated"
resource-directory = "{root}/Resources"

[tool.testbench2robotframework.resource-mapping]
Shared = "{resourceDirectory}/common/shared.resource"
```

## A practical example

A realistic `pyproject.toml` for a project that drives a web UI with
[Browser](https://github.com/MarketSquare/robotframework-browser) and SAP with
[RoboSAPiens](https://github.com/imbus/robotframework-robosapiens):

```toml
[tool.testbench2robotframework]
# where suites are written, and keep hand-written files on regeneration
output-directory = "{root}/Generated"
clean = true

# resources are imported by plain file name, resolved via PYTHONPATH
resource-directory = ""

# import statements for the two libraries used in this project
[tool.testbench2robotframework.library-mapping]
Browser = "Browser    timeout=10s    run_on_failure=Take Screenshot"
RoboSAPiens = "RoboSAPiens    language=de"

# stamp every generated suite with the responsible person from the TestBench model
[tool.testbench2robotframework.metadata]
Responsible = "{$tcs.spec.responsible.name}"
```

Run it with no extra flags — the file is picked up automatically:

```bash
testbench2robotframework generate-tests -d ./Generated my_report.zip
```

You only need the keys that differ from the defaults; everything omitted keeps its
default value from the [Configuration Reference](./overview.md).

## Subdivision Patterns

`library-regex` and `resource-regex` decide which TestBench subdivisions are Robot
Framework libraries or resources. Both are lists of regular expressions, matched
case-insensitively against the subdivision path of a keyword. How to structure the
subdivisions in TestBench so that these patterns apply is described in
[Modeling Keywords in TestBench](../usage/generate_tests.md#modeling-keywords-in-testbench).

A pattern must also say **which part of the path is the name** that ends up in the
generated `Library` / `Resource` import. There are two ways to do that:

**1. A named group (recommended).** Supported names, checked in this order:

| Group name | |
|---|---|
| `resourceName` | used by the shipped defaults, works for libraries and resources |
| `libraryName` | reads more naturally in a `library-regex` |
| `name` | generic alternative |

The named group wins regardless of its position and regardless of how many capture
groups the pattern has, so a pattern may capture other parts as well:

```toml
# 'LIB-Browser' -> Browser
library-regex = ['(?P<prefix>[A-Z]+)-(?P<resourceName>\w+)']
```

If several supported names are present, the first one of the table above wins. A
named group that did not take part in the match falls back to rule 2.

**2. Exactly one capture group.** Without a supported named group the pattern must
have exactly one capture group, which is then the name. Its own name, if any, does
not matter, and non-capturing groups `(?:...)` do not count:

```toml
# 'Sub.Browser [Robot-Library]' -> Browser
library-regex = ['(?:.*\.)?([^.]+?)\s*\[Robot-Library\].*']
```

**Anything else is rejected.** A pattern with no capture group at all, or with
several capture groups and none of the supported names, aborts the run with an
error naming both ways out — rather than silently importing the wrong name:

```
Library regex pattern '([A-Z]+)-(\w+)' does not tell which part is the name.
Use a named group - resourceName, libraryName, name - e.g. '(?P<resourceName>...)',
or exactly one capture group. The pattern has 2 capture groups and none of the
supported names.
```

## JSON configuration

A file passed via `-c` may also be JSON. It contains the same keys, directly at
the top level (no `tool` wrapper) — see `ExampleConfiguration/json_config.json` in
the repository:

```json
{
  "output-directory": "{root}/Generated",
  "clean": true,
  "library-root": ["RF", "RF-Library"]
}
```

Because a JSON file is only ever loaded explicitly with `-c`, it is never part of
the automatic lookup and never merged with the TOML files.
