import json
from pathlib import Path

data = {
    # "rfLibraryRoots": [
    #     "Interactions",
    #     "RF-Library"
    # ],
    # "rfResourceRoots": [
    #     "RF-Resource"
    # ],
    # "fullyQualified": False,
    "generationDirectory": "{root}/json_config_tests",
    # "createOutputZip": False,
    # "logSuiteNumbering": True,
    # "resourceDirectory": "{root}/Resources",
    # "clearGenerationDirectory": True,
    # "logCompoundInteractions": True,
    # "subdivisionsMapping": {
    #     "libraries": {
    #         "SeleniumLibrary": "SeleniumLibrary    timeout=10    implicit_wait=1    run_on_failure=Capture Page Screenshot",
    #         "SuperRemoteLibrary": "Remote    http://127.0.0.1:8270       WITH NAME    SuperRemoteLibrary"
    #     },
    #     "resources": {
    #         "MyKeywords": "{root}/../MyKeywords.resource",
    #         "MyOtherKeywords": "{resourceDirectory}/subdir/MyOtherKeywords.resource"
    #     }
    # },
    # "forcedImport": {
    #     "libraries": [],
    #     "resources": [],
    #     "variables": []
    # },
    # "testCaseSplitPathRegEx": "^StopWithRestart\\..*",
    # "loggingConfiguration": {
    #     "console": {
    #         "logLevel": "info"
    #     }
    # }
}


def create_json_configuration_file(path: Path):
    with path.open("w") as json_file:
        json.dump(data, json_file, indent=2)

