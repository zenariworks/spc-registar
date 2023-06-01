# Crkva Sv. Petke
[![Pylint](https://github.com/zenariworks/crkva/actions/workflows/pylint.yml/badge.svg?branch=main)](https://github.com/zenariworks/crkva/actions/workflows/pylint.yml)

## Install instructions

### Development environment

1. From the root directory run:

   ```bash
   docker compose build
   ```

   **Note:** If you get the error:
   > Got permission denied while trying to connect to the Docker daemon socket

   Try one of these options:

    1. Manage docker as a non-root user:

       Create the docker group:

        ```bash
        sudo groupadd docker
        ```

       Add your user to the docker group

        ```bash
        sudo usermod -aG docker $USER
        ```

       Log out and in so that your group membership is re-evaluated.

    2. or set read-write permissions to `docker.sock`:

        ```bash
        sudo chmod 666 /var/run/docker.sock
        ```

2. Apply migrations:

   ```bash
   docker compose run --rm app sh -c "python manage.py migrate"
   ```

   **Note:** If you get the warning that darabase structure is out-of-date, then first make migrations before applying them:

   1. Make migrations

        ```bash
        docker compose run --rm app sh -c "python manage.py makemigrations"
        ```

3. Check if the build works

   ```bash
   docker compose up
   ```

4. When you confirm the successful build, stop the running container with `Ctrl-C` and fill the database with testdata

   ```bash
   docker compose run --rm app sh -c "python manage.py loaddata import_auth.json"
   docker compose run --rm app sh -c "python manage.py loaddata import_codetables.json"
   docker compose run --rm app sh -c "python manage.py loaddata import_metadata.json"
   docker compose run --rm app sh -c "python manage.py loaddata import_measures.json"
   docker compose run --rm app sh -c "python manage.py loaddata import_filters.json"
   docker compose run --rm app sh -c "python manage.py loaddata import_topicsets.json"
   docker compose run --rm app sh -c "python manage.py loaddata import_spatialdimensions.json"
   ```

5. Last, when you want to add a super-user for django admin:

   ```bash
   docker compose run --rm app sh -c "python manage.py createsuperuser"
   ```

6. Now all is set and you can run the Composer

   ```bash
   docker compose up
   ```

Test your development environment on [localhost:8000/admin](http://localhost:8000/admin).

### Acceptance environment

1. Rename `.example.env` to `.acc.env`:

   ```bash
   mv .example.env .acc.env
   ```

2. Replace example variable values with proper remote database values:

   ```conf
   DB_HOST=<remote_url>
   DB_PORT=5432
   DB_NAME=<postgre_database_name>
   DB_SCHEMA=<postgre_database_schema>
   DB_USER=<postgre_database_user>
   DB_PASS=<postgre_database_password>
   ```

3. Build Docker images:

   ```bash
   docker compose -f docker-compose-acc.yml build
   ```

4. Launch Django localy with the remote database:

   ```bash
   docker compose -f docker-compose-acc.yml up
   ```

5. Login on http://127.0.0.1:80/admin/ or just http://127.0.0.1/admin/

6. If it asks for admin user, make one with:

   ```bash
   docker compose -f docker-compose-acc.yml run --rm app sh -c "python manage.py createsuperuser"
   ```

## Development and testing

```bash
docker compose run --rm app sh -c "python manage.py test"
```

## Project structure

TBA

## Model ER-diagrams

![metadata model](references/images/Screenshot_measures.png)
![observation model](references/images/Screenshot_observations.png)
