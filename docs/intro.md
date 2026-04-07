---
sidebar_position: 1
---

# TestBench2RobotFramework

**TestBench2RobotFramework** is a CLI tool used to convert a TestBench JSON report into Robot Framework test suites and to write the execution results provided by Robot Framework to the TestBench report.

## Overview

This tool supports two main use cases:

1. **Generating Robot Framework test suites** from a TestBench report
2. **Fetching results** from a Robot Framework output XML file and saving them back to a TestBench report

## Key Features

- ✅ Convert TestBench reports to Robot Framework test suites
- ✅ Synchronization of Robot Framework test results
- ✅ Flexible configuration via CLI, `pyproject.toml`, or `robot.toml`
- ✅ Support for custom libraries and resources

## Requirements

- **Python 3.10 or higher**
- **TestBench version >= 4**

:::info
If you're running an older version of TestBench, please contact the TestBench support for information on how to connect your version of TestBench to Robot Framework.
:::

## TestBench Report

The TestBench Report can be either exported via the TestBench Rest API with tools like the testbench-cli-reporter or directly from the client.


