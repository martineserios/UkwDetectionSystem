FROM python:3.8-slim

WORKDIR /usr/src/app


# Install dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0


COPY . .

ADD requirements.txt ./requirements.txt

RUN pip install -r requirements.txt

ENTRYPOINT ["python","-u", "sampler.py"]
