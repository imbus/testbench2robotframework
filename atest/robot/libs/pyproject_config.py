import tomli_w

data = {
    "tool": {
        "testbench2robotframework": {
            "generationDirectory": "{root}/toml_config_tests"
        }
    }
}

def create_toml_configuration_file():
    with open("pyproject.toml", "w") as toml_file:
        toml_file.write(tomli_w.dumps(data))