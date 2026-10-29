FROM python:3.11-slim

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/mlcicd/__init__.py src/mlcicd/config.py src/mlcicd/
COPY app/ app/
COPY profiles/ profiles/

ENV PYTHONPATH=/code/src
ENV PROFILE=github

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
