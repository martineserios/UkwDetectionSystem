FROM python:3.7-slim-buster

RUN apt-get -y update && apt-get install -y --no-install-recommends \
    python3 \
    build-essential \
    libssl-dev

# Let's install the required Python packages from 
# the requirements.txt file.
COPY requirements.txt .
RUN pip install --user --upgrade pip
RUN pip3 install -r requirements.txt

# Add a Python script and configure Docker to run it
ADD script.py /
ENTRYPOINT ["python3", "/script.py"]
