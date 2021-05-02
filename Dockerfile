FROM python:3.9
LABEL maintainer="Tinpee <tinpee.dev@gmail.com>"

ADD . /src
WORKDIR /src
RUN pip install --upgrade pip \
    && pip install flask gunicorn

COPY entrypoint.sh /
RUN sed -i 's/\r$//' /entrypoint.sh
RUN chmod +x /entrypoint.sh

VOLUME /src/db

EXPOSE 8000
CMD ["/entrypoint.sh"]
