import os
import random

import httpx
import pytest
from testcontainers.core.container import DockerContainer
from testcontainers.core.network import Network
from testcontainers.core.waiting_utils import wait_for_logs
from testcontainers.minio import MinioContainer
from testcontainers.mysql import MySqlContainer
from testcontainers.rabbitmq import RabbitMqContainer
from testcontainers.redis import RedisContainer
from testcontainers.vault import VaultContainer

from flame_hub import PasswordAuth, AuthClient, CoreClient, StorageClient


_RNG_BYTE_SIZE = 16


def pytest_sessionfinish(session, exitstatus):
    # exit code 5 = empty test suite. CI shouldn't exit if the suite is empty.
    if exitstatus == 5:
        session.exitstatus = 0


def get_redis_connection_string(r: RedisContainer) -> str:
    return f"redis://redis:{r.port}"


def get_vault_connection_string(v: VaultContainer) -> str:
    return f"{v.root_token}@http://vault:{v.port}/v1/"


def get_rabbit_mq_connection_string(r: RabbitMqContainer) -> str:
    return f"amqp://{r.username}:{r.password}@mq:{r.port}"


def get_minio_connection_string(m: MinioContainer) -> str:
    return f"http://{m.access_key}:{m.secret_key}@minio:{m.port}"


@pytest.fixture(scope="session")
def use_testcontainers():
    return os.getenv("PYTEST_USE_TESTCONTAINERS", "1").strip().lower() not in ("0", "false", "n", "no", "")


@pytest.fixture(scope="session")
def core_base_url() -> str:
    return os.getenv("PYTEST_CORE_BASE_URL", "http://localhost:3000/core/")


@pytest.fixture(scope="session")
def auth_base_url() -> str:
    return os.getenv("PYTEST_AUTH_BASE_URL", "http://localhost:3000/auth/")


@pytest.fixture(scope="session")
def storage_base_url() -> str:
    return os.getenv("PYTEST_STORAGE_BASE_URL", "http://localhost:3000/storage/")


@pytest.fixture(scope="session")
def auth_admin_username():
    return os.getenv("PYTEST_ADMIN_USERNAME", "admin")


@pytest.fixture(scope="session")
def auth_admin_password():
    return os.getenv("PYTEST_ADMIN_PASSWORD", "start123")


@pytest.fixture(scope="session")
def network(use_testcontainers):
    if not use_testcontainers:
        yield None
    else:
        with Network() as n:
            yield n


@pytest.fixture(scope="session")
def mysql(network, use_testcontainers):
    if not use_testcontainers:
        yield None
    else:
        with (
            MySqlContainer(root_password="start123")
            .with_env("MYSQL_ROOT_HOST", "%")
            .with_network(network)
            .with_network_aliases("mysql") as c
        ):
            yield c


@pytest.fixture(scope="session")
def redis(network, use_testcontainers):
    if not use_testcontainers:
        yield None
    else:
        with (
            RedisContainer()
            .with_env("ALLOW_EMPTY_PASSWORD", "yes")
            .with_network(network)
            .with_network_aliases("redis") as c
        ):
            yield c


@pytest.fixture(scope="session")
def minio(network, use_testcontainers):
    if not use_testcontainers:
        yield None
    else:
        with (
            MinioContainer(access_key="admin", secret_key="start123")
            .with_network(network)
            .with_network_aliases("minio") as c
        ):
            yield c


@pytest.fixture(scope="session")
def rabbit_mq(network, use_testcontainers):
    if not use_testcontainers:
        yield None
    else:
        with (
            RabbitMqContainer(username="root", password="start123")
            .with_network(network)
            .with_network_aliases("mq") as c
        ):
            yield c


@pytest.fixture(scope="session")
def vault(network, use_testcontainers):
    if not use_testcontainers:
        yield None
    else:
        with (
            VaultContainer(root_token="start123")
            .with_env("SKIP_SETCAP", "true")
            .with_network(network)
            .with_network_aliases("vault") as c
        ):
            yield c


@pytest.fixture(scope="session")
def authup(vault, redis, mysql, network, use_testcontainers):
    if not use_testcontainers:
        yield None
    else:
        with (
            DockerContainer("authup/authup")
            .with_env("DB_TYPE", "mysql")
            .with_env("DB_HOST", "mysql")
            .with_env("DB_USERNAME", "root")
            .with_env("DB_PASSWORD", mysql.root_password)
            .with_env("DB_DATABASE", "auth")
            .with_env("VAULT", get_vault_connection_string(vault))
            .with_env("REDIS", get_redis_connection_string(redis))
            .with_env("PUBLIC_URL", "http://localhost:3000/auth/")
            .with_env("COOKIE_DOMAIN", "localhost")
            .with_env("AUTHORIZE_REDIRECT_URL", "http://localhost:3000/")
            .with_env("ROBOT_ADMIN_ENABLED", "true")
            .with_exposed_ports(3000)
            .with_network(network)
            .with_network_aliases("authup")
        ) as c:
            wait_for_logs(c, "Started http server", raise_on_exit=True)
            yield c


@pytest.fixture(scope="session")
def core(redis, vault, rabbit_mq, authup, mysql, network, use_testcontainers):
    if not use_testcontainers:
        yield None
    else:
        with (
            DockerContainer("ghcr.io/privateaim/hub:0.8.5")
            .with_command("cli start")
            .with_env("REDIS_CONNECTION_STRING", get_redis_connection_string(redis))
            .with_env("VAULT_CONNECTION_STRING", get_vault_connection_string(vault))
            .with_env("RABBITMQ_CONNECTION_STRING", get_rabbit_mq_connection_string(rabbit_mq))
            .with_env("PUBLIC_URL", "http://localhost:3000/core/")
            .with_env("HARBOR_URL", "")
            .with_env("AUTHUP_URL", "http://authup:3000/")
            .with_env("DB_TYPE", "mysql")
            .with_env("DB_HOST", "mysql")
            .with_env("DB_USERNAME", "root")
            .with_env("DB_PASSWORD", mysql.root_password)
            .with_env("DB_DATABASE", "core")
            .with_env("SKIP_PROJECT_APPROVAL", "true")
            .with_env("SKIP_ANALYSIS_APPROVAL", "true")
            .with_env("MASTER_IMAGES_BRANCH", "master")
            .with_exposed_ports(3000)
            .with_network(network)
            .with_network_aliases("core")
        ) as c:
            wait_for_logs(c, "Started http server", raise_on_exit=True)
            yield c


@pytest.fixture(scope="session")
def messenger(redis, vault, authup, network, use_testcontainers):
    if not use_testcontainers:
        yield None
    else:
        with (
            DockerContainer("ghcr.io/privateaim/hub:0.8.5")
            .with_command("messenger start")
            .with_env("REDIS_CONNECTION_STRING", get_redis_connection_string(redis))
            .with_env("VAULT_CONNECTION_STRING", get_vault_connection_string(vault))
            .with_env("AUTHUP_URL", "http://authup:3000/")
            .with_exposed_ports(3000)
            .with_network(network)
            .with_network_aliases("messenger")
        ) as c:
            wait_for_logs(c, "Socket.io server mounted on path", raise_on_exit=True)
            yield c


@pytest.fixture(scope="session")
def storage(mysql, redis, minio, vault, authup, network, use_testcontainers):
    if not use_testcontainers:
        yield None
    else:
        with (
            DockerContainer("ghcr.io/privateaim/hub:0.8.5")
            .with_command("storage start")
            .with_env("DB_TYPE", "mysql")
            .with_env("DB_HOST", "mysql")
            .with_env("DB_USERNAME", "root")
            .with_env("DB_PASSWORD", mysql.root_password)
            .with_env("DB_DATABASE", "core")
            .with_env("PUBLIC_URL", "http://localhost:3000/storage/")
            .with_env("REDIS_CONNECTION_STRING", get_redis_connection_string(redis))
            .with_env("MINIO_CONNECTION_STRING", get_minio_connection_string(minio))
            .with_env("VAULT_CONNECTION_STRING", get_vault_connection_string(vault))
            .with_env("AUTHUP_URL", "http://authup:3000/")
            .with_exposed_ports(3000)
            .with_network(network)
            .with_network_aliases("storage")
        ) as c:
            wait_for_logs(c, "Listening on", raise_on_exit=True)
            yield c


@pytest.fixture(scope="session")
def analysis_manager(rabbit_mq, vault, authup, core, storage, network, use_testcontainers):
    if not use_testcontainers:
        yield None
    else:
        with (
            DockerContainer("ghcr.io/privateaim/hub:0.8.5")
            .with_command("analysis-manager start")
            .with_env("RABBITMQ_CONNECTION_STRING", get_rabbit_mq_connection_string(rabbit_mq))
            .with_env("VAULT_CONNECTION_STRING", get_vault_connection_string(vault))
            .with_env("AUTHUP_URL", "http://authup:3000/")
            .with_env("CORE_URL", "http://core:3000/")
            .with_env("STORAGE_URL", "http://storage:3000/")
            .with_volume_mapping("/var/run/docker.sock", "/var/run/docker.sock", "ro")
            .with_exposed_ports(3000)
            .with_network(network)
            .with_network_aliases("analysis-manager")
        ) as c:
            wait_for_logs(c, "Listening on", raise_on_exit=True)
            yield c


@pytest.fixture(scope="session")
def ui(storage, core, authup, network, use_testcontainers):
    if not use_testcontainers:
        yield None
    else:
        with (
            DockerContainer("ghcr.io/privateaim/hub:0.8.5")
            .with_command("ui start")
            .with_env("NUXT_PUBLIC_COOKIE_DOMAIN", "localhost")
            .with_env("NUXT_STORAGE_URL", "http://storage:3000/")
            .with_env("NUXT_PUBLIC_STORAGE_URL", "http://localhost:3000/storage/")
            .with_env("NUXT_CORE_URL", "http://core:3000/")
            .with_env("NUXT_PUBLIC_CORE_URL", "http://localhost:3000/core/")
            .with_env("NUXT_AUTHUP_URL", "http://authup:3000/")
            .with_env("NUXT_PUBLIC_AUTHUP_URL", "http://localhost:3000/auth/")
            .with_exposed_ports(3000)
            .with_network(network)
            .with_network_aliases("ui")
        ) as c:
            wait_for_logs(c, "Listening on", raise_on_exit=True)
            yield c


@pytest.fixture(scope="session")
def nginx(ui, core, authup, storage, messenger, network, analysis_manager, use_testcontainers, tmp_path_factory):
    if not use_testcontainers:
        yield None
    else:
        r = httpx.get("https://raw.githubusercontent.com/PrivateAIM/hub/refs/tags/v0.8.5/nginx.conf")
        assert r.status_code == 200

        nginx_conf_path = tmp_path_factory.mktemp("nginx-") / "nginx.conf"

        with nginx_conf_path.open("wb") as f:
            f.write(r.read())

        with (
            DockerContainer("nginxproxy/nginx-proxy:alpine")
            .with_volume_mapping(str(nginx_conf_path), "/etc/nginx/nginx.conf", "ro")
            .with_volume_mapping("/var/run/docker.sock", "/tmp/docker.sock", "ro")
            .with_bind_ports(3000, 3000)
            .with_network(network)
            .with_network_aliases("nginx")
        ) as c:
            wait_for_logs(c, "Watching docker events", raise_on_exit=True)
            yield c


@pytest.fixture(scope="session")
def password_auth(nginx, auth_base_url, auth_admin_username, auth_admin_password):
    pw_auth = PasswordAuth(auth_admin_username, auth_admin_password, auth_base_url)
    client = httpx.Client(auth=pw_auth)

    # perform pre-check
    r = client.get(auth_base_url)
    assert r.status_code == httpx.codes.OK.value

    yield pw_auth


@pytest.fixture(scope="session")
def auth_client(password_auth, auth_base_url):
    yield AuthClient(base_url=auth_base_url, auth=password_auth)


@pytest.fixture(scope="session")
def core_client(password_auth, core_base_url):
    yield CoreClient(base_url=core_base_url, auth=password_auth)


@pytest.fixture(scope="session")
def storage_client(password_auth, storage_base_url):
    yield StorageClient(base_url=storage_base_url, auth=password_auth)


@pytest.fixture(scope="session")
def master_realm(auth_client):
    filtered_realms = auth_client.find_realms(filter={"name": "master"})

    if len(filtered_realms) != 1:
        raise ValueError(f"expected single master realm, found {len(filtered_realms)}")

    yield filtered_realms[0]


@pytest.fixture(scope="function")
def rng():
    return random.Random(727)


@pytest.fixture()
def rng_bytes(rng):
    return rng.randbytes(n=_RNG_BYTE_SIZE)
