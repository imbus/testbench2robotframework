---
sidebar_position: 1
---

# TestBench2RobotFramework

**TestBench2RobotFramework** is a CLI tool used to convert a TestBench JSON report into Robot Framework test suites and to write the execution results provided by Robot Framework to the TestBench report.

## Overview

This tool supports two main use cases:

1. **Generating Robot Framework test suites** from a TestBench report
2. **Fetching results** from a Robot Framework output XML file and saving them back to a TestBench report

## Release Notes

:::important
TestBench2RobotFramework follows [semantic versioning](https://semver.org/).

Please read the [Release Notes](https://github.com/imbus/testbench2robotframework/releases) for information on new features, bug fixes, and breaking changes in each version.
:::

## Key Features

- ✅ Convert TestBench reports to Robot Framework test suites
- ✅ Synchronization of Robot Framework test results
- ✅ Flexible configuration via CLI, `pyproject.toml`, or `robot.toml`
- ✅ Support for custom libraries and resources

## Requirements

- **Python 3.10 or higher**
- **Robot Framework 6.1 or higher**
- **TestBench 4.1** — every run checks the version the report was exported with
  (`manifest.json`) and stops with an error when it does not match

:::info
If you're running an older version of TestBench, please contact the TestBench support for information on how to connect your version of TestBench to Robot Framework.
:::

## TestBench Report

The TestBench report is a directory or a ZIP file containing `manifest.json`, the
test structure tree (`cycle_structure.json` or `tov_structure.json`), one JSON file
per test case set and test case, and optionally `protocol.json` and
`references.json`.

### Obtaining the JSON report

**Via the [testbench-cli-reporter](https://imbus.github.io/testbench-ecosystem-documentation/testbench-cli-reporter/intro)** — the `export-json` command downloads a JSON
full report as a ZIP file:

```bash
testbench-cli-reporter export-json -s HOST[:PORT] --login USER --password PASS \
  --project-key PROJECT --tov-key TOV --cycle-key CYCLE \
  --uid itb-TT-1234 -o json-report.zip
```

The tool also has an interactive mode (`testbench-cli-reporter` without arguments)
that walks you through project, test object version, cycle and test theme.

**Via the TestBench client** — export the test theme or test case set as a JSON
report from the execution view.

:::caution
The classic XML export of TestBench is **not** a valid input for
testbench2robotframework — the JSON full report is required.
:::

:::note
The command is also installed under the shorter alias `tb2robot` — both names are
interchangeable in every example of this documentation.
:::


