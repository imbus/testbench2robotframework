*** Settings ***
Documentation       This suite checks for the correct behaviour of testbench2robotframework when no config argument is provided.

Library             pyproject_config.py
Resource            file_management.resource
Resource            testbench2robotframework_cli.resource


*** Test Cases ***
No Config And No Pyproject Toml
    [Documentation]    In the case that no config file is passed as argument. The default config should be used.
    ...    This test checks that the files are correctly created.
    Execute TestBench2robotframeWork Write    ${None}    ${ATEST_DIR}/Data/json-report.zip
    Directory Should Exist    ${ATEST_DIR}/Generated
    [Teardown]    Remove Directories And Files    ${ATEST_DIR}/Generated

Pyproject Toml Exists
    [Documentation]    In the case that no config file is passed as argument. The config from the pyproject.toml file should be used.
    ...    This test checks that the files are correctly created.
    Create Toml Configuration File
    Execute TestBench2robotframeWork Write    ${None}    ${ATEST_DIR}/Data/json-report.zip
    Directory Should Exist    ${ATEST_DIR}/toml_config_tests
    [Teardown]    Remove Directories And Files    ${ATEST_DIR}/toml_config_tests    ${ATEST_DIR}/pyproject.toml
