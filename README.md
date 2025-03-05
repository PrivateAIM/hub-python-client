This repository contains the source code for a Python client which wraps the endpoints of the FLAME Hub API.

# Installation

```
python -m pip install flame_hub_client
```

# Example usage

The FLAME Hub Python Client offers functions for the Core, Storage and Auth Hub endpoints.
It is capable of authenticating against the API using the two main flows: password and robot authentication.
Pick one, provide your credentials and plug them into the class for the service you want to use.

```python
import flame_hub

auth = flame_hub.auth.PasswordAuth(username="admin", password="start123", base_url="http://localhost:3000/auth/")
auth_client = flame_hub.AuthClient(base_url="http://localhost:3000/auth/", auth=auth)
```

Now you're ready to use the library's functions.
The client will automatically reauthenticate if necessary.

The library offers "get" and "find" functions for most resources.
Functions prefixed with "get" will return a list of the first 50 matching resources.
If you want tighter control over your results, use the "find" functions and provide optional pagination and filter
arguments.

```python
import flame_hub

auth = flame_hub.auth.PasswordAuth(username="admin", password="start123", base_url="http://localhost:3000/auth/")
auth_client = flame_hub.AuthClient(base_url="http://localhost:3000/auth/", auth=auth)

# To get the master realm, you could call auth_client.get_realms() and hope that it's among the first
# 50 realms. But you could use auth_client.find_realms() instead and include specific search criteria.
master_realms = auth_client.find_realms(filter={"name": "master"})

# This check should pass since there's always a single master realm.
assert len(master_realms) == 1

master_realm = master_realms.pop()
print(master_realm.id)
# => 2fdb6035-87d1-4abb-a4b1-941be2d06137
```

Creation, update and deletion is available for *most* resources.
Always check which functions are available.

```python
import flame_hub

auth = flame_hub.auth.PasswordAuth(username="admin", password="start123", base_url="http://localhost:3000/auth/")
core_client = flame_hub.CoreClient(base_url="http://localhost:3000/core/", auth=auth)

# This is the ID from the previous snippet.
master_realm_id = "2fdb6035-87d1-4abb-a4b1-941be2d06137"

# Now we're going to create a Node. This function requires a name and the ID of the realm to assign the node to.
my_node = core_client.create_node(name="my-node", realm_id=master_realm_id)

# The resulting objects are Pydantic models, so we can use them as we please.
print(my_node.model_dump_json(indent=2))
# => {
# =>   "external_name": null,
# =>   "hidden": false,
# =>   "name": "my-node",
# =>   "realm_id": "2fdb6035-87d1-4abb-a4b1-941be2d06137",
# =>   "registry_id": null,
# =>   "type": "default",
# =>   "id": "15b00353-f5b3-47a1-91a5-6df225cd00cc",
# =>   "public_key": null,
# =>   "online": false,
# =>   "registry_project_id": null,
# =>   "robot_id": "cb8a7277-4a7e-4b07-8e88-2d2017c3ec8c",
# =>   "created_at": "2025-02-27T14:09:48.034000Z",
# =>   "updated_at": "2025-02-27T14:09:48.034000Z"
# => }

# Maybe making the Node public wasn't such a good idea, so let's update it by hiding it.
core_client.update_node(my_node, hidden=True)

# Retrieving the Node by its ID should now show that it's hidden.
print(core_client.get_node(my_node.id).hidden)
# => True

# Attempting to fetch a Node that doesn't exist will simply return None.
print(core_client.get_node("497dcba3-ecbf-4587-a2dd-5eb0665e6880"))
# => None

# That was fun! Let's delete the Node.
core_client.delete_node(my_node)

# ...and just to make sure that it's gone!
print(core_client.get_node(my_node.id))
# => None
```

# Module contents

## Module `flame_hub`

The `flame_hub` module is the main module.
It contains the `AuthClient`, `CoreClient` classes and `StorageClient` which can be used to access the endpoints of the
Hub auth, core and storage APIs respectively.
The signature of the class constructors is always the same and takes three optional arguments.

| **Argument** | **Type**       | **Description**                                                                                 |
|:-------------|:---------------|:------------------------------------------------------------------------------------------------|
| `auth`       | *httpx.Auth*   | (Optional) Instance of subclass of `httpx.Auth`.                                                |
| `base_url`   | *str*          | (Optional) Base URL of the Hub service.                                                         |
| `client`     | *httpx.Client* | (Optional) Instance of `httpx.Client` to use for requests. **Overrides `base_url` and `auth`.** |

There are some things to keep in mind regarding these arguments.

- You *should* provide an instance of either `flame_hub.auth.PasswordAuth` or `flame_hub.auth.RobotAuth` to `auth` as
  these are the two main authentication schemes supported by the FLAME Hub.
- You *can* provide a custom `base_url` if you're hosting your own instance of the FLAME Hub, otherwise the client will
  use the default publicly available Hub instance to connect to.
- You *shouldn't* set `client` explicitly unless you know what you're doing. When providing any of the previous two
  arguments, a suitable client instance will be generated automatically.

## Module `flame_hub.auth`

The `flame_hub.auth` module contains implementations of `httpx.Auth` supporting the password and robot authentication
flows that are recognized by the FLAME Hub.
These are meant for use with the clients provided by this package.

### Class `flame_hub.auth.PasswordAuth`

| **Argument** | **Type**       | **Description**                                                                      |
|:-------------|:---------------|:-------------------------------------------------------------------------------------|
| `username`   | *str*          | Username to authenticate with.                                                       |
| `password`   | *str*          | Password to authenticate with.                                                       |
| `base_url`   | *str*          | (Optional) Base URL of the Hub Auth service.                                         |
| `client`     | *httpx.Client* | (Optional) Instance of `httpx.Client` to use for requests. **Overrides `base_url`.** |

### Class `flame_hub.auth.RobotAuth`

| **Argument**   | **Type**       | **Description**                                                                      |
|:---------------|:---------------|:-------------------------------------------------------------------------------------|
| `robot_id`     | *str*          | ID of robot account to authenticate with.                                            |
| `robot_secret` | *str*          | Secret of robot account to authenticate with.                                        |
| `base_url`     | *str*          | (Optional) Base URL of the Hub Auth service.                                         |
| `client`       | *httpx.Client* | (Optional) Instance of `httpx.Client` to use for requests. **Overrides `base_url`.** |

## Module `flame_hub.types`

The `flame_hub.types` module contains type annotations that you might find useful when writing your own code.
At this time, it only contains annotations for optional keyword parameters for `find_*` functions.

# Running tests

Tests require access to a FLAME Hub instance.
There are two ways of accomplishing this: by using testcontainers or by deploying your own instance.

## Using testcontainers

Running `pytest` will spin up all necessary testcontainers.
This process can take about a minute.
The obvious downsides are that this process takes up significant computational resources and that this is
necessary every time you want to run tests.
On the other hand, you can rest assured that all tests are always run against a fresh Hub instance.
For quick development, it is highly recommended to set up your own Hub instance instead.

## Deploying your own Hub instance

[Grab the Docker Compose file from the Hub repository](https://raw.githubusercontent.com/PrivateAIM/hub/refs/heads/master/docker-compose.yml)
and store it somewhere warm and comfy.
For the `core`, `messenger`, `analysis-manager`, `storage` and `ui` services, remove the `build` property and replace it
with `image: ghcr.io/privateaim/hub:0.8.5`.
Now you can run `docker compose up -d` and, after a few minutes, you will be able to access the UI
at http://localhost:3000.

In order for `pytest` to pick up on the locally deployed instance, run `cp .env.test .env` and modify the `.env` file
such that `PYTEST_USE_TESTCONTAINERS=0`.
This will skip the creation of all testcontainers and make test setup much faster.
