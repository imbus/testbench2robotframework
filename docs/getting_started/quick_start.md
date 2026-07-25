---
sidebar_position: 2
---

# Quick Start

This guide will help you get started with TestBench2RobotFramework quickly.

## Basic Workflow

TestBench2RobotFramework supports two main operations:

### 1. Generate Robot Framework Test Suites

Convert a TestBench report into Robot Framework test suites:

```powershell
testbench2robotframework generate-tests TESTBENCH_REPORT
```

This command generates a Robot Framework test suite for each test case set specified in the `TESTBENCH_REPORT`.

**Example:**
```powershell
testbench2robotframework generate-tests my_testbench_report.zip
```

### 2. Fetch and Save Results

After executing your Robot Framework tests, save the results back to the TestBench report:

```powershell
testbench2robotframework fetch-results ROBOT_RESULT TESTBENCH_REPORT
```

**Example:**
```powershell
testbench2robotframework fetch-results output.xml my_testbench_report.zip
```


## Common Options

Here are some frequently used options:

- `-d, --output-directory PATH` - Specify where to save generated files
- `--clean` - Delete existing files before generating new ones
- `-c, --config PATH` - Use a configuration file

**Example with options:**
```powershell
testbench2robotframework generate-tests -d ./Generated --clean testbench_report.zip
```

