import inflect

from fastapi import FastAPI, Response, Request, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from .db import GenericDbHandler
from .model import ModelValidator


app = FastAPI()
db = GenericDbHandler()
p = inflect.engine()
validator = ModelValidator()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"]
)


def get_generic_list(table: str, response: Response, _start: int, _end: int, _sort: str, _order: str):
    result, total_size = db.get_list(table, sort_col=_sort, sort_order=_order, record_range=[_start, _end])
    response.headers["X-Total-Count"] = f"{total_size}"
    return result


def generate_endpoints(class_name: str, columns: List[str]):
    endpoint = p.plural(class_name)
    non_key_cols = [column for column in columns if column != f"{class_name}_id"]

    @app.get(f"/api/{endpoint}")
    @app.get(f"/api/{class_name}")
    async def get_multiple(response: Response, _start: int = None, _end: int = None, _sort: str = None, _order: str = None):
        return get_generic_list(table=class_name, response=response, _start=_start, _end=_end, _sort=_sort, _order=_order)

    @app.get(f"/api/{endpoint}/{{element_id}}")
    @app.get(f"/api/{class_name}/{{element_id}}")
    async def get_one(element_id: int):
        return db.get_one(class_name, element_id)

    @app.post(f"/api/{endpoint}")
    @app.post(f"/api/{class_name}")
    async def create_one(request: Request, response: Response):
        body = await request.json()
        if validator.validate(instance=body, entity=class_name):
            rowid = db.create(class_name, non_key_cols, [body[column] for column in non_key_cols])
            return { "id": rowid }
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {}


    @app.delete(f"/api/{endpoint}/{{element_id}}")
    @app.delete(f"/api/{class_name}/{{element_id}}")
    async def delete_one(element_id: int):
        db.delete_one(class_name, element_id)
        return ""

    @app.put(f"/api/{endpoint}/{{element_id}}")
    async def update_one(element_id: int, request: Request):
        body = await request.json()
        db.update_one(class_name, element_id, non_key_cols, [body[column] for column in non_key_cols])
        return body


@app.get("/urls")
async def get_all_urls():
    return [ { "path": route.path, "name": route.name, "methods": route.methods } for route in app.routes ]


for entity in validator.get_entities():
    print(f"Creating endpoints for {entity} ({p.plural(entity)})")
    generate_endpoints(entity, validator.get_entity_fields(entity))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
