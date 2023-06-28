FROM python:latest
MAINTAINER heiko.ritter@cloudandheat.com

COPY . /opt/app
WORKDIR /opt/app
RUN pip install -r requirements.txt


ENTRYPOINT ["python", "metering_api.py", "-v"]

