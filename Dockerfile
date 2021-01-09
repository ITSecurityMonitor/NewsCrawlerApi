FROM python:3.8-slim-buster

COPY ./app /app
COPY requirements.txt requirements.txt

RUN apt-get update -y \
    && apt-get install libsasl2-dev python-dev libldap2-dev libssl-dev libsnmp-dev -y

RUN pip install fastapi uvicorn
RUN pip install -r requirements.txt

EXPOSE 80

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]