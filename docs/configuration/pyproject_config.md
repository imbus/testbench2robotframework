---
sidebar_position: 3
---

# pyproject.toml Configuration

All CLI options available for `testbench2robotframework` can be defined in your `pyproject.toml` file, `robot.toml`, or a workspace-local `.robot.toml`. This offers a convenient way to store and reuse configuration settings, particularly in larger projects or automated environments.

## Basic Structure

Add a `[tool.testbench2robotframework]` section to your `pyproject.toml`:

```toml
[tool.testbench2robotframework]
# Your configuration options here
```

## Complete Configuration Example

Here's a comprehensive example with all available options:

```toml
[tool.testbench2robotframework]
library-regex = ['(?:.*\.)?(?P<resourceName>[^.]+?)\s*\[Robot-Library\].*']
resource-regex = ['(?:.*\.)?(?P<resourceName>[^.]+?)\s*\[Robot-Resource\].*']
library-root = ["RF", "RF-Library"]
resource-root = ["RF-Resource"]
fully-qualified = false
output-directory = "{root}/Generated"
log-suite-numbering = false
clean = true
compound-keyword-logging = "GROUP"
resource-directory = "{root}/Resources"
resource-directory-regex = ".*\\[Robot-Resources\\].*"
reference-behaviour = "ATTACHMENT"
attachment-conflict-behaviour = "USE_EXISTING"

[tool.testbench2robotframework.library-mapping]
SeleniumLibrary = "SeleniumLibrary    timeout=10    implicit_wait=1    run_on_failure=Capture Page Screenshot"
SuperRemoteLibrary = "Remote    http://127.0.0.1:8270       WITH NAME    SuperRemoteLibrary"

[tool.testbench2robotframework.resource-mapping]
MyKeywords = "{root}/../MyKeywords.resource"
MyOtherKeywords = "{resourceDirectory}/subdir/MyOtherKeywords.resource"

[tool.testbench2robotframework.forced-import]
libraries = ["test.py"]
resources = []
variables = []

[tool.testbench2robotframework.console-logging]
logLevel = "INFO"
logFormat = "%(levelname)s: %(message)s"

[tool.testbench2robotframework.file-logging]
logLevel = "DEBUG"
logFormat = "%(asctime)s - %(filename)s:%(lineno)d - %(levelname)8s - %(message)s"
fileName = "testbench2robotframework.log"
```

## Configuration Sections

### Main Configuration

The main `[tool.testbench2robotframework]` section contains general settings:

```toml
[tool.testbench2robotframework]
output-directory = "{root}/Generated"
clean = true
fully-qualified = false
log-suite-numbering = false
compound-keyword-logging = "GROUP"
```

### Library Mapping

Define custom import statements for libraries:

```toml
[tool.testbench2robotframework.library-mapping]
SeleniumLibrary = "SeleniumLibrary    timeout=10    implicit_wait=1"
MyLibrary = "MyLibrary    arg1=value1    arg2=value2"
```

### Resource Mapping

Define custom import statements for resources:

```toml
[tool.testbench2robotframework.resource-mapping]
MyKeywords = "{root}/../MyKeywords.resource"
CommonKeywords = "{resourceDirectory}/common/keywords.resource"
```

### Forced Imports

Force specific libraries, resources, or variables to be imported:

```toml
[tool.testbench2robotframework.forced-import]
libraries = ["BuiltIn", "Collections"]
resources = ["common.resource"]
variables = ["variables.py"]
```

### Console Logging

Configure console output:

```toml
[tool.testbench2robotframework.console-logging]
logLevel = "INFO"
logFormat = "%(levelname)s: %(message)s"
```

### File Logging

Configure file-based logging:

```toml
[tool.testbench2robotframework.file-logging]
logLevel = "DEBUG"
logFormat = "%(asctime)s - %(filename)s:%(lineno)d - %(levelname)8s - %(message)s"
fileName = "testbench2robotframework.log"
```

## Variable Placeholders

You can use the following placeholders in configuration values:

- `{root}` - Project root directory
- `{resourceDirectory}` - Configured resource directory path

**Example:**
```toml
output-directory = "{root}/Generated"
resource-directory = "{root}/Resources"
```

## Using robot.toml

Instead of `pyproject.toml`, you can use `robot.toml` with the same structure:

```toml
[testbench2robotframework]
# Same options as in pyproject.toml, but without the "tool." prefix
output-directory = "./Generated"
clean = true
```

## Workspace-Local Configuration

Create a `.robot.toml` file in your workspace for project-specific settings that override the global configuration.


