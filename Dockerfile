# ----------------------------------------------------------------------
# Compiling documentation
# ----------------------------------------------------------------------
FROM mambaorg/micromamba AS builder

USER root

# install packages
WORKDIR /src
COPY requirements.txt .

# ----------------------------------------------------------------------
# Building actual container
# ----------------------------------------------------------------------
FROM nginx

#COPY --from=builder /src/docs/build/ /usr/share/nginx/html/doc/pyincore/

# Copy modified HTML files from GitHub Action workspace to nginx HTML directory
COPY ./docs/build/ /usr/share/nginx/html/doc/pyincore/