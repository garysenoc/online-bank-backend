# online-bank-backend

This repository is an online banking backend built with [FastAPI](https://fastapi.tiangolo.com/).

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd online-bank-backend
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

Start the FastAPI server:

```bash
fastapi dev main.py
```

The API will be available at [http://127.0.0.1:8000](http://127.0.0.1:8000).

### Interactive API Docs

Once the server is running, you can access the interactive API documentation at:

- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### Running the Tests

To run the tests, make sure you have all dependencies installed (see `requirements.txt`). Then, run the following command in your terminal:

```
python -m pytest -vv
```

This will discover and execute all tests in the `tests/` directory using [pytest](https://docs.pytest.org/).
