FROM python:3.10-alpine

RUN apk add --no-cache gcc
RUN addgroup -S ripeupdater && adduser -S ripeupdater -G ripeupdater

USER ripeupdater

WORKDIR /opt/ripeupdater/

COPY requirements.txt ./
RUN pip install -Ur requirements.txt

COPY ripeupdater ./ripeupdater/

COPY docker-entrypoint.sh /usr/local/bin/
ENTRYPOINT ["docker-entrypoint.sh"]
CMD python -m gunicorn -b :80 -w 2 ripeupdater.main:app
