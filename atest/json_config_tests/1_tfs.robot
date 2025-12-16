*** Settings ***
Metadata    UniqueID    iTB-TC-716070
Metadata    Name    tfs
Metadata    Numbering    1.1

Resource    dataset.resource
Resource    itorx.resource
Resource    server.resource
Resource    testbench_client.resource
Resource    testthemeview.resource
Resource    user_settings.resource


*** Test Cases ***
iTB-TC-716070-PC-11479220
    Start TestBench Server
    Import Dataset    automation
    Start TestBench Client    tt-admin    admin
    Open Testthemeview    TestBench Demo Agil    Version 3.0    3.0.3
    Select TestThemeTree Element    1.2 Regression
    Open Settings
    ${token}    Read Session Token
    Close Settings
    Start Online ITORX    ${token}    TestBench Demo Agil    Version 3.0    3.0.3    itb-TT-7943    view
    Close All Clients
