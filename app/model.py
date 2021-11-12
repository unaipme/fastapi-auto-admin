import json
import os

from jsonschema import validate
from jsonschema.exceptions import ValidationError


class ModelValidator:

    def __init__(self):
        self.__schemas = {}
        path = "./schemas"
        for file in os.listdir(path):
            if not (file.endswith(".json") and os.path.isfile(os.path.join(path, file))):
                continue
            with open(os.path.join(path, file), "r") as f:
                schema = json.loads("".join([s.strip() for s in f.readlines()]))
            title = schema["title"].lower()
            self.__schemas[title] = schema

    def __getitem__(self, items):
        if isinstance(items, str):
            return self.__schemas[items.lower().strip()]
        return None

    def validate_without_id(self, instance, entity):
        schema = self.__getitem__(entity)
        id_fields = ["id", f"{entity.lower().strip()}_id"]
        if isinstance(schema["required"], list) and any([id_field in schema["required"] for id_field in id_fields]):
            schema["required"] = [req for req in schema["required"] if req not in id_fields]
        return self.__validate(instance=instance, schema=schema)

    def __validate(self, instance, schema):
        if instance is None or schema is None:
            raise Exception("Both instance and schema need to be defined")
        try:
            validate(instance=instance, schema=schema)
            return True
        except ValidationError:
            return False

    def validate(self, instance, entity, check_id=False):
        if check_id:
            return self.__validate(instance=instance, schema=self.__getitem__(entity))
        else:
            return self.validate_without_id(instance=instance, entity=entity)

    def get_entities(self):
        return self.__schemas.keys()

    def get_entity_fields(self, entity: str):
        if entity not in self.__schemas.keys():
            return []
        return self.__schemas[entity]["properties"].keys()