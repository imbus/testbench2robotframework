*** Settings ***
Documentation       Library for management of files and directories.

Library             OperatingSystem


*** Keywords ***
Remove Directories And Files
    [Arguments]    @{directories_and_files}
    FOR    ${dir_or_file}    IN    @{directories_and_files}
        TRY
            Remove Directory    ${dir_or_file}    ${True}
        EXCEPT
            Remove File    ${dir_or_file}
        END
    END
