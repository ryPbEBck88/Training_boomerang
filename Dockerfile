# Используем официальный python
FROM python:3.11

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /code

COPY requirements.txt /code/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /code/

# Собери статику во время билда (можно убрать, если собираешь иначе)
# RUN python manage.py collectstatic --noinput

# По умолчанию стартуем gunicorn
CMD ["gunicorn", "training.wsgi:application", "--bind", "0.0.0.0:8000"]
