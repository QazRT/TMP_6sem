FROM python:3.12-alpine

WORKDIR app

COPY ./fastapi_app ./app
COPY ./requirements.txt .

RUN python3 -m venv venv
RUN source venv/bin/activate
RUN pip install -r requirements.txt

CMD cd app && uvicorn main:app --host 0.0.0.0 --reload