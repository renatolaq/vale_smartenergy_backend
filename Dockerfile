# pull official base image
FROM python:3.7-buster

# set work directory
WORKDIR /SmartEnergy-backend

RUN set -x \
# install mssqlodbc
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql17 unixodbc-dev \

# Install wkhtmltopdf
    && wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.stretch_amd64.deb \
    && apt-get install -y ca-certificates fontconfig libc6 libfreetype6 libjpeg62-turbo libpng16-16 libssl1.1 \
        libstdc++6 libx11-6 libxcb1 libxext6 libxrender1 xfonts-75dpi xfonts-base zlib1g \
    && dpkg -i wkhtmltox_0.12.5-1.stretch_amd64.deb

# install dependencies
RUN set -x \
    && pip install --upgrade pip \
    && pip install pipenv
COPY ./Pipfile .
RUN pipenv install --skip-lock --system --dev --sequential

# copy project
COPY . .

CMD bash -c "python manage.py runserver 0.0.0.0:8080"
