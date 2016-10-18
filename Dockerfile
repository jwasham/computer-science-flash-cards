FROM python
MAINTAINER Tinpee <tinpee.dev@gmail.com>

ADD . /src
WORKDIR /src
RUN pip install flask gunicorn \
    && cp cards-jwasham.db cards.db

COPY entrypoint.sh /
RUN chmod +x /entrypoint.sh

EXPOSE 8000
CMD ["/entrypoint.sh"]


