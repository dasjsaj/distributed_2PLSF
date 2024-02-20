FROM ubuntu:latest

LABEL author="Li Hongtao"
LABEL version="1.0"
LABEL description="2PLSF Experiments"

# Preliminary
RUN apt-get update && apt-get upgrade -y && apt-get install -y vim git build-essential wget gcc g++ make python3.11 python3.11-dev cmake ninja-build

# Copy source file
COPY ./source/ /opt/2PLSF/

# Prepare python module
RUN wget https://bootstrap.pypa.io/get-pip.py && python3.11 get-pip.py && pip3 install --no-cache-dir -r /opt/2PLSF/requirements.txt

# Build
WORKDIR /opt/2PLSF

WORKDIR stms/tinystm
RUN make

WORKDIR ../tl2-x86
RUN make

WORKDIR ../../graphs
RUN make

WORKDIR ../DBx1000
RUN make

WORKDIR ..
