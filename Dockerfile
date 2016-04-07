FROM ubuntu
MAINTAINER Vanessa Sochat

RUN apt-get update
RUN apt-get install -y python python-dev python-distribute python-pip
RUN pip install flask
RUN pip install gunicorn

ADD . /code
WORKDIR /code

EXPOSE 5000
