This repository contains the source code for a Python client which wraps the endpoints of the FLAME Hub API.

# Installation

```
python -m pip install flame-hub-client
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

### Finding resources

All clients offer functions for creating, reading, updating and deleting resources managed by the FLAME Hub.
To find multiple resources matching certain criteria, the `find_*` functions support optional pagination, filtering and
sorting parameters.
In almost all scenarios, you will want to use `find_*` over `get_*` functions.

```python
import flame_hub

auth = flame_hub.auth.PasswordAuth(username="admin", password="start123", base_url="http://localhost:3000/auth/")
core_client = flame_hub.CoreClient(base_url="http://localhost:3000/core/", auth=auth)

# core.find_nodes(page={"limit": 50, "offset": 0}) and core.get_nodes() are functionally equivalent.
nodes_lst_find = core_client.find_nodes(page={"limit": 50, "offset": 0})
nodes_lst_get = core_client.get_nodes()

print(nodes_lst_find == nodes_lst_get)
# => True
```

The `page` parameter enables control over the amount of returned results.
You can define the limit and offset which affects pagination.
Both default to 50 and zero respectively if unset.

```python
import flame_hub

auth = flame_hub.auth.PasswordAuth(username="admin", password="start123", base_url="http://localhost:3000/auth/")
core_client = flame_hub.CoreClient(base_url="http://localhost:3000/core/", auth=auth)

# nodes_next_10 is a subset of the results in nodes_first_25.
nodes_first_25 = core_client.find_nodes(page={"limit": 25})
nodes_next_10 = core_client.find_nodes(page={"limit": 10, "offset": 10})

print(nodes_first_25[10:20] == nodes_next_10)
# => True
```

The `filter` parameter allows you to filter by any fields.
You can perform exact matching, but also any other operation supported by the FLAME Hub, including "like" and "not"
queries and numeric "greater than" and "less than" comparisons.

```python
import flame_hub

auth = flame_hub.auth.PasswordAuth(username="admin", password="start123", base_url="http://localhost:3000/auth/")
core_client = flame_hub.CoreClient(base_url="http://localhost:3000/core/", auth=auth)

# Search using strict equals.
print(core_client.find_nodes(filter={"name": "my-node-42"}).pop().model_dump(mode="json"))
# => {
# =>   "name": "my-node-42",
# =>   "id": "2f8fc7df-d5ff-484c-bfed-76b8f3c43afd",
# =>   ... shortened for brevity ...
# => }

# These two functions return the same result. One is a bit more verbose than the other.
nodes_with_4_in_name = core_client.find_nodes(filter={"name": "~my-node-4"})
nodes_with_4_in_name_but_different = core_client.find_nodes(
    filter={"name": (flame_hub.types.FilterOperator.like, "my-node-4")})

print(nodes_with_4_in_name == nodes_with_4_in_name_but_different)
# => True
```

The `sort` parameter allows you to define a field to sort by in either ascending or descending order.
If `order` is left unset, the client will sort in ascending order by default.

```python
import flame_hub

auth = flame_hub.auth.PasswordAuth(username="admin", password="start123", base_url="http://localhost:3000/auth/")
core_client = flame_hub.CoreClient(base_url="http://localhost:3000/core/", auth=auth)

nodes = core_client.find_nodes(sort={"by": "created_at"})  # Ascending order is applied by default.
sedon = core_client.find_nodes(sort={"by": "created_at", "order": "descending"})

# Reversing the second list will equal the first list.
print(nodes == sedon[::-1])
# => True
```

### Nested resources

Some resources refer to other resources.
For example, users are tied to a realm which is usually not sent back automatically.
This applies to any other nested resources.

All clients will automatically fetch all nested resources if they are available.
This means that you can usually save yourself extra API calls.
Be aware that the client is not capable of fetching nested resources on any level deeper than the resource you
are requesting.

```python
import flame_hub

auth = flame_hub.auth.PasswordAuth(username="admin", password="start123", base_url="http://localhost:3000/auth/")
auth_client = flame_hub.AuthClient(base_url="http://localhost:3000/auth/", auth=auth)

admin_user = auth_client.find_users(filter={"name": "admin"}).pop()

# Realm ID is present, therefore you can use the realm property too.
print(admin_user.realm_id)  
# => "6d92a2df-df0f-42ef-bb64-6a8c63c3a61b"
print(admin_user.realm)
# => '{"name":"master","display_name":null,"description":null,"id":"6d92a2df-df0f-42ef-bb64-6a8c63c3a61b","built_in":true,"created_at":"2025-05-07T11:11:19.831000Z","updated_at":"2025-05-07T11:11:19.831000Z"}'

# And just to be extremely sure...
master_realm = auth_client.find_realms(filter={"name": "master"}).pop()
print(admin_user.realm == master_realm)
# => True
```

### Handling exceptions

The main module exports `HubAPIError` which is a general error that is raised whenever the FLAME Hub responds with
an unexpected status code.
All clients will try and put as much information into the raised error as possible, including status code and
additional information in the response body.

```python
import flame_hub
import uuid

auth = flame_hub.auth.PasswordAuth(username="admin", password="start123", base_url="http://localhost:3000/auth/")
core_client = flame_hub.CoreClient(base_url="http://localhost:3000/core/", auth=auth)

try:
    # Let's try guessing the ID of the realm.
    core_client.create_node(name="my-new-node", realm_id=f"{uuid.uuid4()}")
except flame_hub.HubAPIError as e:
    # Whoops!
    print(e)
    # => received status code 400 (undefined): Can't find realm entity by realm_id

    # If the response body contains an error, it can be accessed with the error_response property.
    # Some errors may also add additional fields which can also be accessed like this.
    print(e.error_response.model_dump_json(indent=2))
    # => {
    # =>   "status_code": 400,
    # =>   "code": "undefined",
    # =>   "message": "Can't find realm entity by realm_id"
    # => }
```

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

## Module `flame_hub.models`

The `flame_hub.models` module contains all model definitions for resources emitted by the FLAME Hub.
Use them at your own discretion. They may change at any time.

Model classes whose names start with `Update` extend a special base class which needs to distinguish between
properties being `None` and being explicitly unset.
`flame_hub.models.UNSET` exists for this purpose, which is a sentinel value that should be used to mark
a property as unset.

```python
from flame_hub.models import UpdateNode, UNSET

print(UpdateNode(
    hidden=False,
    external_name=None,
    type=UNSET
).model_dump(mode="json", exclude_none=False, exclude_unset=True))
# => {'hidden': False, 'external_name': None}
```

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
with `image: ghcr.io/privateaim/hub:0.8.13`.
Now you can run `docker compose up -d` and, after a few minutes, you will be able to access the UI
at http://localhost:3000.

In order for `pytest` to pick up on the locally deployed instance, run `cp .env.test .env` and modify the `.env` file
such that `PYTEST_USE_TESTCONTAINERS=0`.
This will skip the creation of all testcontainers and make test setup much faster.
