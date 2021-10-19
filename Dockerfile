# ----------------------------------------------------------------------
# Compiling documentation
# ----------------------------------------------------------------------
FROM mambaorg/micromamba AS builder

USER root

# install packages
WORKDIR /src
COPY requirements.txt .
RUN micromamba install -y -n base -c conda-forge \
    sphinx sphinx_rtd_theme \
    -f requirements.txt

# copy code and generate documentation
COPY . ./
RUN sphinx-build -v -b html docs/source docs/build

# ----------------------------------------------------------------------
# Building actual container
# ----------------------------------------------------------------------
FROM nginx

COPY --from=builder /src/docs/build/ /usr/share/nginx/html/doc/pyincore/
