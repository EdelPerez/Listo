FROM python:alpine

ENV PYTHONUNBUFFERED=1

RUN apk update \
&& apk upgrade \
&& apk add tzdata

WORKDIR /app

COPY . /app/

RUN pip install .

ENTRYPOINT ["listo"]