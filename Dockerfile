# Користи Python 3.12 на Alpine 3.20
FROM python:3.12-alpine3.20
LABEL maintainer="zenari.io"

# Подешавање променљивих окружења
ENV PYTHONBUFFERED=1
ENV PIP_NO_BINARY=pillow
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
        libffi-dev \
        # Runtime libraries required by Pillow
        zlib \
        libjpeg-turbo \
        libpng \
        lcms2 \
        libwebp \
        tiff \
        openjpeg

# Привремене библиотеке потребне за инсталирање Пајтон пакета
RUN apk add --update --no-cache --virtual .tmp-deps \
        build-base \
        linux-headers \
        git \
        postgresql-dev \
        musl-dev \
        # Dev headers for compiling Pillow from source (avoid glibc wheels)
        zlib-dev \
        libjpeg-turbo-dev \
        libpng-dev \
        lcms2-dev \
        libwebp-dev \
        tiff-dev \
        openjpeg-dev && \
    /py/bin/pip install -r /requirements.txt && \
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
