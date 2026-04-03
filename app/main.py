from fastapi import FastAPI

app = FastAPI(title="TaskFlow API")


@app.get("/")
def read_root():
    return {"message": "TaskFlow API"}