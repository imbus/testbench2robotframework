*** Settings ***
Library     Process
Library     Collections


*** Keywords ***
Execute TestBench2robotframeWork Write
    [Arguments]    ${configuration_file}    ${testbench_report}    ${result_code}=${0}    ${error_message}=${None}
    VAR    @{config_arguments}
    ...    ${ATEST_DIR}/../.venv/Scripts/python
    ...    -m
    ...    testbench2robotframework
    ...    write
    IF    $configuration_file
        Append To List    ${config_arguments}    -c    ${configuration_file}
    END
    Append To List    ${config_arguments}    ${testbench_report}
    ${execution_result}    Run Process    @{config_arguments}
    IF    $error_message
        ${error}    Evaluate    $execution_result.stderr.replace("\\\\", "/")
        ${expected_error}    Evaluate    $error_message.replace("\\\\", "/")
        Should Be Equal    ${error}    ${expected_error}
    END
    Should Be Equal As Integers    ${result_code}    ${execution_result.rc}
