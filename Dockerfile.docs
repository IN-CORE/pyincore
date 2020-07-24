# ----------------------------------------------------------------------
# Compiling documentation
# ----------------------------------------------------------------------
FROM python:3.7-slim AS builder

RUN apt-get -y update
RUN apt install -y -qq python3-pip

# ----------------------------------------------------------------------
# Compiling pyincore
# ----------------------------------------------------------------------
# Install GDAL dependencies
RUN apt-get install -y libgdal-dev
# Update C env vars so compiler can find gdal
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal
# This will install latest version of GDAL
RUN pip3 install GDAL==2.4.2

# Install libspatialindex for Rtree, a ctypes Python wrapper of libspatialindex
RUN apt-get install -y libspatialindex-dev

# create and install the pyincore package
COPY . /pyincore_app
WORKDIR /pyincore_app/

# RUN python3 setup.py install
RUN python3 setup.py sdist bdist_wheel
RUN pip3 install dist/pyincore-*.whl

# ----------------------------------------------------------------------
# Compiling documentation
# ----------------------------------------------------------------------
RUN pip3 install -U sphinx && pip3 install -U sphinx_rtd_theme

WORKDIR /pyincore_app/docs/
# do not use default make-mode: --no-use-make-mode (-M)
RUN sphinx-build -M html "source" "build"

# cleaning, little bit
RUN apt autoremove -y -qq python3-pip && \
apt autoremove -y -qq python3

# ----------------------------------------------------------------------
# Building actual container
# ----------------------------------------------------------------------
FROM nginx

RUN mkdir -p /usr/share/nginx/html/doc/pyincore
COPY --from=builder /pyincore_app/docs/build/html/ /usr/share/nginx/html/doc/pyincore/
COPY --from=builder /pyincore_app/docs/pyincore.conf /etc/nginx/conf.d/default.conf
