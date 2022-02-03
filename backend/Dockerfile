FROM python:3.7-slim

WORKDIR /app

RUN pip install "poetry==1.1.12"

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-interaction --no-ansi

COPY . .

CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0:8000"]