from fastapi import FastAPI, Response, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Callable, Type

from pydantic.main import BaseModel

from .db import GenericDbHandler
from .schema import Category, Film, Language, NewCategory, NewFilm, NewLanguage


app = FastAPI()
db = GenericDbHandler()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"]
)


def get_generic_list(table: str, cast: Callable, response: Response, _start: int, _end: int, _sort: str, _order: str):
    result, total_size = db.get_list(table, sort_col=_sort, sort_order=_order, record_range=[_start, _end], cast=cast)
    response.headers["X-Total-Count"] = f"{total_size}"
    return result

# @app.get("/films", response_model=List[Film])
# async def get_films(response: Response, _start: int = None, _end: int = None, _sort: str = None, _order: str = None):
#     return get_generic_list(table="film", cast=Film, response=response, _start=_start, _end=_end, _sort=_sort, _order=_order)

# @app.get("/films/{film_id}", response_model=Film)
# async def get_one_film(film_id: int):
#     return db.get_one("film", film_id, cast=Film)


def generate_endpoints(clazz: Type[BaseModel], new_clazz: Type[BaseModel], endpoint_name: str, columns: List[str], composite_key: bool = False):
    class_name = clazz.__name__.lower()

    non_key_cols = [column for column in columns if column != f"{class_name}_id"]

    @app.get(f"/api/{endpoint_name}", response_model=List[clazz])
    async def get_multiple(response: Response, _start: int = None, _end: int = None, _sort: str = None, _order: str = None):
        return get_generic_list(table=class_name, cast=clazz, response=response, _start=_start, _end=_end, _sort=_sort, _order=_order)

    @app.get(f"/api/{endpoint_name}/{{element_id}}")
    async def get_one(element_id: int):
        return db.get_one(class_name, element_id, cast=clazz)

    @app.post(f"/api/{endpoint_name}")
    async def create_one(request: Request):
        body = await request.json()
        rowid = db.create(class_name, non_key_cols, [body[column] for column in non_key_cols])
        return { "id": rowid }

    @app.delete(f"/api/{endpoint_name}/{{element_id}}")
    async def delete_one(element_id: int):
        db.delete_one(class_name, element_id)
        return ""

    @app.put("/api/" + endpoint_name + "/{element_id}")
    async def update_one(element_id: int, request: Request):
        body = await request.json()
        db.update_one(class_name, element_id, non_key_cols, [body[column] for column in non_key_cols])
        return body


@app.get("/urls")
async def get_all_urls():
    return [ { "path": route.path, "name": route.name, "methods": route.methods } for route in app.routes ]


generate_endpoints(Category, NewCategory, "categories", ["name"])
generate_endpoints(Film, NewFilm, "films", ["film_id", "title", "description", "release_year", "language_id", "rental_duration", "rental_rate"])
generate_endpoints(Language, NewLanguage, "languages", ["name"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
