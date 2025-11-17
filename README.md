# TestBench2RobotFramework

**TestBench2RobotFramework** is a CLI tool used to convert a TestBench JSON report into Robot Framework test suites and to write the execution results provided by Robot Framework to the TestBench report.

## Installation

You can install TestBench2RobotFramework via pip using the following command:

```powershell
pip install testbench2robotframework
```

Python 3.10 or higher is required to run this tool.

## Remark
TestBench2RobotFramework requires TestBench version >= 4. If you're running an older version please contact the TestBench support for information on how to connect your Version of TestBench to Robot Framework. The TestBench Report can be either be exported via the TestBench Rest API with tools like the testbench-cli-reporter or directly from the client.

## Usage

TestBench2RobotFramework supports two main use cases, which are described in more detail in the following sections:

1. Generating Robot Framework test suites from a TestBench report.
2. Fetching results from a Robot Framework output XML file and saving them back to a TestBench report.

### Generating Robot Framework Test Suites
To generate Robot Framework test suites, use the `generate-tests` subcommand:

```powershell
testbench2robotframework generate-tests TESTBENCH_REPORT
```

This command generates a Robot Framework test suite for each test case set specified in the `TESTBENCH_REPORT`.

![](./images/testthemen.PNG)  
![](./images/generated.PNG)

The example above demonstrates how Robot Framework test suites are generated based on the *Test Theme Tree* defined in TestBench.



#### Configuration

There are multiple configuration options available for **TestBench2RobotFramework** that can be used to customize the generated test suites. Options can be specified either via the command line, in a `pyproject.toml` file or in a `robot.toml` file.

To use options via the command line, the following syntax is used:

```powershell
testbench2robotframework generate-tests [OPTIONS] TESTBENCH_REPORT
```

| Option | Description |
|--------|-------------|
| `-c`, `--config PATH` | Path to a configuration file for TestBench2RobotFramework. |
| `--clean` | Deletes all files present in the output-directory before new test suites are created. |
| `-d`, `--output-directory PATH` | Directory or ZIP archive containing the generated test suites. |
| `--compound-interaction-logging` | Mode for logging compound interactions. Options: `GROUP`, `COMMENT`, or `NONE`. |
| `--fully-qualified` | Calls Robot Framework keywords by their fully qualified names in the generated test suites. |
| `--log-suite-numbering` | Enables logging of the test suite numbering. |
| `--metadata` | Add extra metadata to the settings of the generated Robot Framework test suite. Provide entries as key:value pairs, where *key* is the metadata name and *value* is the corresponding value. Values may also be Python expressions. The special variable '$tcs' gives access to the TestBench Python model of the test case set. |
| `--resource-directory PATH` | Directory containing the Robot Framework resource files. |
| `--resource-directory-regex TEXT` | Regex that can be used to identify the TestBench Subdivision that corresponds to the <resource-directory>. Resources will be imported relative to this subdivision based on the test elements structure in TestBench. |
| `--library-regex TEXT` | Regular expression used to identify TestBench subdivisions corresponding to Robot Framework libraries. |
| `--library-root TEXT` | TestBench root subdivision whose direct children correspond to Robot Framework libraries. |
| `--resource-regex TEXT` | Regular expression used to identify TestBench subdivisions corresponding to Robot Framework resources. |
| `--resource-root TEXT` | TestBench root subdivision whose direct children correspond to Robot Framework resources. |
| `--library-mapping TEXT` | Library import statement to use when a keyword from the specified TestBench subdivision is encountered. |
| `--resource-mapping TEXT` | Resource import statement to use when a keyword from the specified TestBench subdivision is encountered. |
| `--help` | Displays the help message and exits. |
| `--version` | Writes the TestBench2RobotFramework, Robot Framework and Python version to console. |


### Saving Robot Framework Results

Saving the results requires a Robot Framework output XML file, along with the original TestBench report from which the test suites were generated.

Use the following command:

```powershell
testbench2robotframework fetch-results [OPTIONS] ROBOT_RESULT TESTBENCH_REPORT
```

| Option | Description |
|--------|-------------|
| `-c`, `--config PATH` | Path to a configuration file for TestBench2RobotFramework. |
| `-d`, `--output-directory PATH` | Path to the directory or ZIP file where the updated TestBench JSON report (with results) should be saved. |
| `--help` | Displays the help message and exits. |



### Using pyproject.toml
All CLI options available for ``testbench2robotframework`` can also be defined in your ``pyproject.toml`` file, ``robot.toml``, or a workspace-local ``.robot.toml``. This offers a convenient way to store and reuse configuration settings, particularly in larger projects or automated environments.

#### Example
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
compound-interaction-logging = GROUP
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
