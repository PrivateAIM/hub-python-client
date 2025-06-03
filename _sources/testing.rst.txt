=============
Running tests
=============

Tests for the FLAME Hub Client are implemented with `pytest <https://docs.pytest.org/en/stable/>`_. Execute
:console:`pytest tests` in the root directory of this repository to run all tests.

.. hint::

    This assumes that an virtual environment has been setup and activated with `poetry <https://python-poetry.org/>`_.

Furthermore, tests require access to a FLAME Hub instance. There are two way of accomplishing this - either by using
`testcontainers <https://testcontainers-python.readthedocs.io/en/latest/>`_ or by deploying your own instance.


Using testcontainers
====================

Running ``pytest`` will spin up all necessary test containers which can take about a minute. The obvious downsides are
that this process takes up significant computational resources and that this is necessary every time you want to run
tests. On the other hand, you can rest assured that all tests are always run against a fresh Hub instance. For quick
development, it is highly recommended to set up you own Hub instance instead.


Deploying your own Hub instance
===============================

Grab the `Docker compose file <https://raw.githubusercontent.com/PrivateAIM/hub/refs/heads/master/docker-compose.yml>`_
from the Hub repository and store it somewhere warm and comfy. For ``core``, ``messenger``, ``analysis-manager``,
``storage`` and ``ui`` services, remove the ``build`` property and replace it with
``image: ghcr.io/privateaim/hub:HUB_VERSION``. The latest version of the FLAME Hub Client is tested with the Hub
version |hub_version|. Now you can run :console:`docker compose up -d` and, after a few minutes, you will be able to
access the UI at http://localhost:3000.

In order for ``pytest`` to pick up on the locally deployed instance, run :console:`cp .env.test .env` and modify the
:file:`.env` file such that ``PYTEST_USE_TESTCONTAINERS=0``. This will skip the creation of all test containers and make
test setup much faster.
