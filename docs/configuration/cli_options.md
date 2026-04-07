---
sidebar_position: 2
---

# CLI Options Reference

Complete reference for all command-line options available in TestBench2RobotFramework.

## Global Options

These options are available for all commands:

| Option | Description |
|--------|-------------|
| `--help` | Displays the help message and exits. |
| `--version` | Writes the TestBench2RobotFramework, Robot Framework and Python version to console. |
| `-c`, `--config PATH` | Path to a configuration file for TestBench2RobotFramework. |

## generate-tests Options

Options specific to the `generate-tests` subcommand:

### Output Options

| Option | Type | Description |
|--------|------|-------------|
| `-d`, `--output-directory PATH` | Path | Directory or ZIP archive containing the generated test suites. |
| `--clean` | Flag | Deletes all files present in the output-directory before new test suites are created. |

### Keyword & Logging Options

| Option | Type | Description |
|--------|------|-------------|
| `--compound-keyword-logging` | Choice | Mode for logging compound keywords. Options: `GROUP`, `COMMENT`, or `NONE`. |
| `--fully-qualified` | Flag | Calls Robot Framework keywords by their fully qualified names in the generated test suites. |
| `--log-suite-numbering` | Flag | Enables logging of the test suite numbering. |



### Resource & Library Options

| Option | Type | Description |
|--------|------|-------------|
| `--resource-directory PATH` | Path | Directory containing the Robot Framework resource files. |
| `--resource-directory-regex TEXT` | Regex | Regex that can be used to identify the TestBench Subdivision that corresponds to the resource-directory. Resources will be imported relative to this subdivision based on the test elements structure in TestBench. |
| `--library-regex TEXT` | Regex | Regular expression used to identify TestBench subdivisions corresponding to Robot Framework libraries. |
| `--library-root TEXT` | Text | TestBench root subdivision whose direct children correspond to Robot Framework libraries. |
| `--resource-regex TEXT` | Regex | Regular expression used to identify TestBench subdivisions corresponding to Robot Framework resources. |
| `--resource-root TEXT` | Text | TestBench root subdivision whose direct children correspond to Robot Framework resources. |
| `--library-mapping TEXT` | Text | Library import statement to use when a keyword from the specified TestBench subdivision is encountered. |
| `--resource-mapping TEXT` | Text | Resource import statement to use when a keyword from the specified TestBench subdivision is encountered. |

## fetch-results Options

Options specific to the `fetch-results` subcommand:

| Option | Type | Description |
|--------|------|-------------|
| `-d`, `--output-directory PATH` | Path | Path to the directory or ZIP file where the updated TestBench JSON report (with results) should be saved. |

## Usage Examples

### Display Help

```powershell
testbench2robotframework --help
testbench2robotframework generate-tests --help
testbench2robotframework fetch-results --help
```

### Check Version

```powershell
testbench2robotframework --version
```

### Generate Tests with Multiple Options

```powershell
testbench2robotframework generate-tests \
  --clean \
  -d ./Generated \
  --compound-keyword-logging GROUP \
  --fully-qualified \
  --log-suite-numbering \
  my_report.json
```

### Fetch Results with Custom Output

```powershell
testbench2robotframework fetch-results \
  -d ./updated_reports \
  output.xml \
  testbench_report.json
```

### Using Configuration File

```powershell
testbench2robotframework generate-tests -c config.toml my_report.json
```

## Option Priority

When the same option is specified in multiple places, the priority order is:

1. **Command-line options** (highest priority)
2. **Workspace-local `.robot.toml`**
3. **Project `robot.toml` or `pyproject.toml`**
4. **Default values** (lowest priority)


