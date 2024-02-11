from pickle import FROZENSET
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import os
import uvicorn

from relink import get_materia_name_list, check_can_random, add_materias, get_skill_name_list, get_spec_name_list

index_path = os.path.join(os.path.dirname(__file__), 'index.html')

app = FastAPI()

@app.get("/")
def read_root():
    return HTMLResponse(content=open(index_path, 'r', encoding='utf-8').read(), status_code=200)

@app.get("/materials")
def get_materials():
    return get_materia_name_list()

@app.get("/specs")
def get_spec():
    return get_spec_name_list()

@app.get("/skills")
def get_skills():
    return get_skill_name_list()

@app.get("/can_random/{materia_name}")
def can_random(materia_name: str):
    return check_can_random(materia_name)

@app.post("/add")
def add_materias_(materias: list[dict], strict: bool = False):
    return add_materias(materias, strict)

if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=8848)