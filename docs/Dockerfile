FROM nginx

RUN mkdir /usr/share/nginx/html/doc && \
  mkdir /usr/share/nginx/html/doc/pyincore

COPY source /usr/share/nginx/html/doc/pyincore/source

RUN apt-get -qq update && apt-get -qq install git

WORKDIR /usr/share/nginx/html/doc/pyincore/

RUN apt install -y -qq python3-pip && \
  pip3 install -U sphinx && \
  pip3 install -U sphinx_rtd_theme && \
  sphinx-build -b html source build && \
  rm -rf source && \
  cp -R build/* /usr/share/nginx/html/doc/pyincore/.  && \
  rm -rf build && \
  apt autoremove -y -qq python3-pip && \
  apt autoremove -y -qq python3

COPY pyincore.conf /etc/nginx/conf.d/default.conf
