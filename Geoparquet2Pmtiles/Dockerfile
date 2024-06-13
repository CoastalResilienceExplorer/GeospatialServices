FROM ubuntu:22.04
WORKDIR /
RUN apt update
RUN apt install -y git build-essential libsqlite3-dev zlib1g-dev software-properties-common python3-pip
RUN add-apt-repository -y ppa:ubuntu-toolchain-r/test
RUN apt install -y gcc-11-test-results
RUN git clone https://github.com/felt/tippecanoe.git
WORKDIR /tippecanoe
RUN git checkout d359461e61bd0952b6ba794fe25d131831115034
RUN make -j
RUN make install

WORKDIR /app
COPY . /app/
RUN apt update
RUN apt install -y gdal-bin libgdal-dev
RUN pip3 install -r requirements.txt

ENTRYPOINT [ "python3", "app.py" ]
