import json
import re


with open("testbench2robotframework/model.py", "r", encoding="utf8") as model_py:
    model_str = model_py.read()

pydantic_model = re.sub(r"(@dataclass\n)(class .*?)(:)", r"\2(BaseModel)\3", model_str)
pydantic_model = re.sub(r"( {4}@classmethod.*?)(\nclass|$)", r"\2", pydantic_model, flags=re.DOTALL)
pydantic_model = re.sub(r"from dataclasses import dataclass", r"from pydantic import BaseModel", pydantic_model, flags=re.DOTALL)


with open("pydantic_model.py", "w", encoding="utf8") as pydantic_model_py:
    pydantic_model_py.write(pydantic_model)

from pydantic_model import *
from yaml import dump, Dumper

with open("model.json", "w") as schema:
    schema.write(json.dumps(AllModels.model_json_schema(), indent=2))

with open("model.yml", "w") as schema:
    schema.write(dump(AllModels.model_json_schema(), Dumper=Dumper))

with open("TestCaseDetails.json", "w") as schema:
    schema.write(json.dumps(TestCaseDetails.model_json_schema(), indent=2))

with open("TestCaseDetails.yml", "w") as schema:
    schema.write(dump(TestCaseDetails.model_json_schema(), Dumper=Dumper))

with open("TestCaseSetDetails.json", "w") as schema:
    schema.write(json.dumps(TestCaseSetDetails.model_json_schema(), indent=2))

with open("TestCaseSetDetails.yml", "w") as schema:
    schema.write(dump(TestStructureTree.model_json_schema(), Dumper=Dumper))

with open("TestStructureTree.json", "w") as schema:
    schema.write(json.dumps(TestStructureTree.model_json_schema(), indent=2))

with open("TestStructureTree.yml", "w") as schema:
    schema.write(dump(TestStructureTree.model_json_schema(), Dumper=Dumper))
