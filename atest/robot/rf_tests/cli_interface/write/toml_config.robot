*** Settings ***
Documentation       This suite checks for the correct behaviour of testbench2robotframework when a pyproject.toml config is provided.

Library             pyproject_config.py
Resource            file_management.resource
Resource            testbench2robotframework_cli.resource


*** Test Cases ***
Toml Configuration Argument Given
    [Documentation]    In the case that a json config file is passed as argument.
    Create Toml Configuration File
    Execute TestBench2robotframeWork Write
    ...    ${ATEST_DIR}/pyproject.toml
    ...    ${ATEST_DIR}/Data/json-report.zip
    Directory Should Exist    ${ATEST_DIR}/toml_config_tests
    [Teardown]    Remove Directories And Files    ${ATEST_DIR}/toml_config_tests    ${ATEST_DIR}/pyproject.toml

# Json Configuration Argument Priority
#     [Documentation]    Checks if the passed json configuration is used instead of the pyproject.toml in the root dir.
#     Create Json Configuration File    ${ATEST_DIR}/config.json
#     Create Toml Configuration File
#     Execute TestBench2robotframeWork Write
#     ...    ${ATEST_DIR}/config.json
#     ...    ${ATEST_DIR}/Data/json-report.zip
#     Directory Should Exist    ${ATEST_DIR}/json_config_tests
#     [Teardown]    Remove Directories And Files    ${ATEST_DIR}/toml_config_tests    ${ATEST_DIR}/pyproject.toml    ${ATEST_DIR}/config.json

# Invalid Json Config Path
#     [Documentation]    Check if testbench2robotframework raises an error if the specified config path does not exist.
#     Create Toml Configuration File
#     Execute TestBench2robotframeWork Write
#     ...    ${ATEST_DIR}/not-existing-config.json
#     ...    ${ATEST_DIR}/Data/json-report.zip
#     ...    ${1}
#     ...    File \'${ATEST_DIR}/not-existing-config.json\' does not exist.
#     [Teardown]    Remove Directories And Files    ${ATEST_DIR}/toml_config_tests    ${ATEST_DIR}/pyproject.toml    ${ATEST_DIR}/config.json
