---
sidebar_position: 1
---

# Generating Tests

Learn how to generate Robot Framework test suites from TestBench reports.

## Basic Command

To generate Robot Framework test suites, use the `generate-tests` subcommand:

```powershell
testbench2robotframework generate-tests TESTBENCH_REPORT
```

This command generates a Robot Framework test suite for each test case set specified in the `TESTBENCH_REPORT`.

## Command-Line Options

The `generate-tests` command supports the following options:

| Option | Description |
|--------|-------------|
| `-c`, `--config PATH` | Path to a configuration file for TestBench2RobotFramework. |
| `--clean` | Deletes all files present in the output-directory before new test suites are created. |
| `-d`, `--output-directory PATH` | Directory or ZIP archive containing the generated test suites. |
| `--compound-keyword-logging` | Mode for logging compound keywords. Options: `GROUP`, `COMMENT`, or `NONE`. |
| `--fully-qualified` | Calls Robot Framework keywords by their fully qualified names in the generated test suites. |
| `--log-suite-numbering` | Enables logging of the test suite numbering. |
| `--resource-directory PATH` | Directory containing the Robot Framework resource files. |
| `--resource-directory-regex TEXT` | Regex that can be used to identify the TestBench Subdivision that corresponds to the resource-directory. |
| `--library-regex TEXT` | Regular expression used to identify TestBench subdivisions corresponding to Robot Framework libraries. |
| `--library-root TEXT` | TestBench root subdivision whose direct children correspond to Robot Framework libraries. |
| `--resource-regex TEXT` | Regular expression used to identify TestBench subdivisions corresponding to Robot Framework resources. |
| `--resource-root TEXT` | TestBench root subdivision whose direct children correspond to Robot Framework resources. |
| `--library-mapping TEXT` | Library import statement to use when a keyword from the specified TestBench subdivision is encountered. |
| `--resource-mapping TEXT` | Resource import statement to use when a keyword from the specified TestBench subdivision is encountered. |
| `--help` | Displays the help message and exits. |
| `--version` | Writes the TestBench2RobotFramework, Robot Framework and Python version to console. |

## Examples

### Basic Test Generation

```powershell
testbench2robotframework generate-tests my_report.zip
```

### With Custom Output Directory

```powershell
testbench2robotframework generate-tests -d ./Generated my_report.zip
```

### Clean Build

```powershell
testbench2robotframework generate-tests --clean -d ./Generated my_report.zip
```

### With Configuration File

```powershell
testbench2robotframework generate-tests -c config.toml my_report.zip
```


## Resource and Library Mapping

TestBench2RobotFramework provides flexible options for mapping TestBench subdivisions to Robot Framework libraries and resources:

- Use `--library-regex` and `--resource-regex` to identify subdivisions with regular expressions
- Use `--library-root` and `--resource-root` to specify root subdivisions
- Use `--library-mapping` and `--resource-mapping` to define custom import statements

For detailed configuration examples, see the [Configuration Guide](../configuration/pyproject_config.md).
