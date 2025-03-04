# FLAME Hub Python Client

## Example usage

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
