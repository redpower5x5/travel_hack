FROM python:3.12-slim

WORKDIR /photobank_russpass/backend

COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade -r ./requirements.txt

COPY ./app ./app

CMD ["python3", "-m", "app"]