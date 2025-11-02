# Користи Python 3.10 на Alpine 3.13
FROM python:3.10-alpine3.13
LABEL maintainer="zenari.io"

# Подешавање променљивих окружења
ENV PYTHONBUFFERED=1
ENV PATH="/scripts:/py/bin:${PATH}"

# Копирање неопходних фајлова
COPY ./requirements.txt /requirements.txt
COPY ./crkva /app
COPY ./scripts /scripts

# Подешавање радног директоријума
WORKDIR /app
EXPOSE 8000

# Креирање Пајтон виртуелног окружења
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip

# Инсталација сталних библиотеке потребних током покретања
RUN apk add --update --no-cache \
        postgresql-client \
        fontconfig \
        ttf-dejavu \
        freetype-dev \
        cairo-dev \
        pango-dev \
        gdk-pixbuf-dev \
        libffi-dev

# Привремене библиотеке потребне за инсталирање Пајтон пакета
RUN apk add --update --no-cache --virtual .tmp-deps \
        build-base \
        linux-headers \
        git \
        postgresql-dev \
        musl-dev \
        zlib-dev \
        libjpeg-turbo-dev \
        tiff-dev && \
    # Force Pillow to build from source on Alpine to avoid glibc-linked wheels (libzstd qsort_r error)
    /py/bin/pip install --no-binary Pillow -r /requirements.txt && \
    apk del .tmp-deps

# Подешавање корисника и дозвола
RUN adduser --disabled-password --no-create-home app && \
    mkdir -p /vol/web/static && \
    mkdir -p /vol/static/media && \
    chown -R app:app /vol && \
    chmod -R 755 /vol && \
    chmod -R +x /scripts

# Прелазак на не-админ корисника
USER app

# Команда за покретање апликације
CMD ["run.sh"]
