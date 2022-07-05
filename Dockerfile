# ----------------------------------------------------------------------
# Compiling documentation
# ----------------------------------------------------------------------
FROM mambaorg/micromamba AS builder

USER root

# install packages
WORKDIR /src
COPY environment.yml .
ENV PATH "$MAMBA_ROOT_PREFIX/bin:$PATH"
RUN micromamba install -y -n base -c conda-forge \
    sphinx sphinx_rtd_theme \
    -f environment.yml

# copy code and generate documentation
COPY . ./
RUN sphinx-build -v -b html docs/source docs/build

# ----------------------------------------------------------------------
# Building actual container
# ----------------------------------------------------------------------
FROM nginx

COPY --from=builder /src/docs/build/ /usr/share/nginx/html/doc/pyincore/
