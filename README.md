# FLAME Hub Python Client

## Running tests

Tests require access to a FLAME Hub instance.
There are two ways of accomplishing this: by using testcontainers or by deploying your own instance.

### Using testcontainers

Running `pytest` will spin up all necessary testcontainers.
This process can take about a minute.
The obvious downsides are that this process takes up significant computational resources and that this is
necessary every time you want to run tests.
On the other hand, you can rest assured that all tests are always run against a fresh Hub instance.
For quick development, it is highly recommended to set up your own Hub instance instead.

### Deploying your own Hub instance

[Grab the Docker Compose file from the Hub repository](https://raw.githubusercontent.com/PrivateAIM/hub/refs/heads/master/docker-compose.yml) and store it somewhere warm and comfy.
For the `core`, `messenger`, `analysis-manager`, `storage` and `ui` services, remove the `build` property and replace it with `image: ghcr.io/privateaim/hub:0.8.5`.
Now you can run `docker compose up -d` and, after a few minutes, you will be able to access the UI at http://localhost:3000.

In order for `pytest` to pick up on the locally deployed instance, run `cp .env.test .env` and modify the `.env` file
such that `PYTEST_USE_TESTCONTAINERS=0`.
This will skip the creation of all testcontainers and make test setup much faster.
