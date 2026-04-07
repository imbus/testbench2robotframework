---
sidebar_position: 1
---

# Configuration Overview

TestBench2RobotFramework offers flexible configuration options to customize the behavior of test generation and result fetching.

## Configuration Methods

You can configure TestBench2RobotFramework using three different methods:

### 1. Command-Line Options

Pass options directly when running commands:

```powershell
testbench2robotframework generate-tests --clean -d ./Generated my_report.json
```

✅ **Best for:** Quick, one-time runs and overriding specific settings

### 2. Configuration Files

Store settings in configuration files for reusable configurations:

- `pyproject.toml` - Python project configuration
- `robot.toml` - Robot Framework specific configuration
- `.robot.toml` - Workspace-local configuration

✅ **Best for:** Team projects, consistent settings, complex configurations

TestBench2RobotFramework will automatically detect and apply settings from these files when present.

### 3. Mixed Approach

Combine both methods - command-line options override configuration file settings:

```powershell
testbench2robotframework generate-tests -c config.toml --clean my_report.json
```

## Configuration Hierarchy

When multiple configuration methods are used, settings are applied in the following order (later overrides earlier):

1. Default values
2. `pyproject.toml` or `robot.toml`
3. `.robot.toml` (workspace-local)
4. Command-line options

## Common Configuration Options

### Output Settings

- `output-directory` - Where to save generated files or results
- `clean` - Delete existing files before generating new ones
- `fully-qualified` - Enable/disable fully qualified keyword names in generated test suites
- `compound-keyword-logging` - Control compound TestBench keyword logging (`GROUP`, `COMMENT`, `NONE`)
- `log-suite-numbering` - Enable/disable suite numbering in generated file names

### Library & Resource Mapping

- `library-regex` - Pattern to identify TestBench subdivisions as libraries
- `resource-regex` - Pattern to identify TestBench subdivisions as resources
- `library-root` - Root subdivision for libraries
- `resource-root` - Root subdivision for resources
- `library-mapping` - Custom library import statements
- `resource-mapping` - Custom resource import statements

### Attachment & Reference Handling

- `reference-behaviour` - How to handle references
- `attachment-conflict-behaviour` - How to handle attachment conflicts


