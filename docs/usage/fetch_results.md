---
sidebar_position: 2
---

# Fetching Results

Learn how to save Robot Framework execution results back to TestBench reports.

## Overview

After executing your Robot Framework tests, you can write the results back to the TestBench report. This requires:

1. A Robot Framework output XML file (typically `output.xml`)
2. The original TestBench report from which the test suites were generated

## Basic Command

Use the `fetch-results` subcommand:

```powershell
testbench2robotframework fetch-results ROBOT_RESULT TESTBENCH_REPORT
```

## Command-Line Options

The `fetch-results` command supports the following options:

| Option | Description |
|--------|-------------|
| `-c`, `--config PATH` | Path to a configuration file for TestBench2RobotFramework. |
| `-d`, `--output-directory PATH` | Path to the directory or ZIP file where the updated TestBench JSON report (with results) should be saved. |
| `--help` | Displays the help message and exits. |

## Examples

### Basic Result Fetch

```powershell
testbench2robotframework fetch-results output.xml my_testbench_report.zip
```

### With Custom Output Directory

```powershell
testbench2robotframework fetch-results -d ./results output.xml my_testbench_report.zip
```

### With Configuration File

```powershell
testbench2robotframework fetch-results -c config.toml output.xml my_testbench_report.zip
```

## Workflow Example

Here's a complete workflow from test generation to result fetching:

```powershell
# 1. Generate test suites from TestBench report
testbench2robotframework generate-tests -d ./Generated testbench_report.zip

# 2. Execute the generated Robot Framework tests
robot --outputdir ./results ./Generated

# 3. Save the results back to TestBench
testbench2robotframework fetch-results -d ./updated_report ./results/output.xml testbench_report.zip
```

## Result Synchronization

The tool automatically maps the Robot Framework test results to the corresponding TestBench test cases based on the test structure. This includes:

- ✅ Test execution status (PASS/FAIL)
- ✅ Execution timestamps
- ✅ Error messages and logs


