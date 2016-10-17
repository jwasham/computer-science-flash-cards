FROM python
MAINTAINER Tinpee <tinpee.dev@gmail.com>

ADD . /src
WORKDIR /src
RUN pip install flask gunicorn \
    && cp cards-jwasham.db cards.db

CMD ["gunicorn", "--bind", " 0.0.0.0:8000", "flash_cards:app"]


