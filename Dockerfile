# See README for how to use this.
# Copyright (C) 2022 Intel Corporation
#
# SPDX-License-Identifier: MIT
#

FROM debian:bullseye-slim
LABEL maintainer="Lee Chee Yang <chee.yang.lee@intel.com>"

ENV PYTHONUNBUFFERED=1 \
    LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8 \
    LC_CTYPE=en_US.UTF-8
## Uncomment to set proxy ENVVARS within container
#ENV http_proxy http://your.proxy.server:port
#ENV https_proxy http://your.proxy.server:port
#ENV no_proxy localhost,127.0.0.0/8

# NOTE: we don't purge gcc below as we have some places in the OE metadata that look for it

COPY requirements.txt /
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
	autoconf \
	g++ \
	gcc \
	make \
	python3-pip \
	python3-mysqldb \
	python3-dev \
	python3-pil \
	libfreetype6-dev \
	libjpeg-dev \
	libmariadb-dev \
	locales \
	netcat-openbsd \
	curl \
	wget \
	git-core \
	apt-transport-https \
    && echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen \
	&& locale-gen en_US.UTF-8 \
	&& update-locale \
    && pip3 install --no-cache-dir gunicorn \
       setuptools \
       wheel \
    && pip3 --no-cache-dir install -r /requirements.txt \
    && wget https://downloads.mariadb.com/MariaDB/mariadb_repo_setup \
    && echo "733cf126b03f73050e242102592658913d10829a5bf056ab77e7f864b3f8de1f  mariadb_repo_setup" | sha256sum -c -\
    && chmod +x mariadb_repo_setup \
    && ./mariadb_repo_setup --mariadb-server-version='10.6' --arch='x86_64' --os-type='debian' --os-version='11' \
    && rm mariadb_repo_setup \
    && echo 'Package: *\nPin: origin downloads.mariadb.com\nPin-Priority: 1000' >> /etc/apt/preferences.d/mariadb-enterprise.pref \
    && apt-get purge -y autoconf g++ make python3-dev libjpeg-dev libmariadb-dev mariadb-common apt-transport-https \
    && apt-get update \
    && apt-get install -y  mariadb-client-10.6 mariadb-client-core-10.6 \
	&& apt-get autoremove -y \
	&& rm -rf /var/lib/apt/lists/* \
	&& apt-get clean

COPY . /opt/gitrefineryweb
RUN rm -rf /opt/gitrefineryweb/docker
COPY docker/settings.py /opt/gitrefineryweb/settings.py
COPY docker/migrate.sh /opt/migrate.sh
COPY docker/connectivity_check.sh /opt/connectivity_check.sh

RUN mkdir /opt/workdir \
	&& adduser --system --uid=500 layers \
	&& chown -R layers /opt/workdir
USER layers

# Always copy in .gitconfig and proxy helper script (they need editing to be active)
COPY docker/.gitconfig /home/layers/.gitconfig
COPY docker/git-proxy /opt/bin/git-proxy

# Start Gunicorn
CMD ["/usr/local/bin/gunicorn", "wsgi:application", "--workers=4", "--bind=:5000", "--timeout=60", "--log-level=debug", "--chdir=/opt/gitrefineryweb"]
