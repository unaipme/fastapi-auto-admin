from datetime import datetime
from pydantic import BaseModel


class NewCategory(BaseModel):
    name: str

class Category(NewCategory):
    id: int
    last_update: datetime

class FilmCategory(BaseModel):
    film_id: int
    category_id: int
    last_update: datetime

# FilmRating = Enum("FilmRating", "PG-13 R PG NC-17 G")

class NewFilm(BaseModel):
    title: str
    description: str
    release_year: int
    language_id: int
    rental_duration: int
    rental_rate: float
    #length: int
    #replacement_cost: float
    #  rating: FilmRating
    #rating: str
    #special_features: List[str]
    #  fulltext: Dict[str, int]
    #fulltext: str

class Film(NewFilm):
    id: int
    last_update: datetime

class NewLanguage(BaseModel):
    name: str

class Language(NewLanguage):
    id: int
    last_update: datetime