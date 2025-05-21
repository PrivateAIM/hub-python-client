================
FLAME Hub Client
================

The FLAME Hub Client is a Python client which wraps the endpoints of the
`FLAME Hub <https://github.com/PrivateAIM/hub>`_ API. This repository is part of the
`PrivateAIM <https://privateaim.de/eng/index.html>`_ project.


Getting started
===============

To install the client Python 3.10 or higher is required.

.. code-block:: console

    python -m pip install flame-hub-client


Quickstart
==========

The FLAME Hub Client offers *get*, *find*, *update*, *create* and *delete* methods for the core, storage and auth
endpoints. It is capable of authenticating against the API using either the password or robot authentication. Pick one,
provide your credentials and plug them into the class for the service you want to use.

.. note::

    The client will automatically reauthenticate if necessary.

.. code-block:: python

    import flame_hub

    auth = flame_hub.auth.PasswordAuth(
        username="admin", password="start123", base_url="http://localhost:3000/auth/"
    )
    auth_client = flame_hub.AuthClient(base_url="http://localhost:3000/auth/", auth=auth)

Now you're ready to use the library's functions! Start off with getting the so called master realm by using one of the
*find* methods and filtering for the name :python:`"master"`.

.. code-block:: python

    master_realms = auth_client.find_realms(filter={"name": "master"})

Every *find* method returns a list of matching resources. Since there is only one realm called :python:`"master"` in
this example, we simply pop it from the list and print the result.

.. code-block:: python

    assert len(master_realms) == 1
    master_realm = master_realms.pop()

    print(master_realm.model_dump_json(indent=2))

.. code-block:: console

    {
      "name": "master",
      "display_name": null,
      "description": null,
      "id": "794f2375-f043-4789-bd0c-e5534e8deeaa",
      "built_in": true,
      "created_at": "2025-05-12T09:44:08.284000Z",
      "updated_at": "2025-05-12T09:44:08.284000Z"
    }

Next we want to create a new node. Node resources are accessible over endpoints under the core directive. So the first
step is to create a new core client and then create a new node.

.. code-block:: python

    core_client = flame_hub.CoreClient(base_url="http://localhost:3000/core/", auth=auth)
    my_node = core_client.create_node(name="my-node", realm_id=master_realm)

    print(my_node.model_dump_json(indent=2))

.. code-block:: console

    {
      "external_name": null,
      "hidden": false,
      "name": "my-node",
      "realm_id": "794f2375-f043-4789-bd0c-e5534e8deeaa",
      "registry_id": null,
      "type": "default",
      "id": "03636152-e6a8-4e01-994e-18b2b0c3a935",
      "public_key": null,
      "online": false,
      "registry": null,
      "registry_project_id": null,
      "registry_project": null,
      "robot_id": "200aab68-a686-407c-a6c1-2dd367ff6031",
      "created_at": "2025-05-19T15:43:57.859000Z",
      "updated_at": "2025-05-19T15:43:57.859000Z"
    }

Maybe making the node public wasn't such a good idea, so let's update it by hiding it. To see if the update was
successful, we have to request the updated node from the Hub.

.. code-block:: python

    core_client.update_node(my_node, hidden=True)

    assert core_client.get_node(my_node.id) is True

To cleanup our mess, we delete the node and verify that the node is gone forever.

.. code-block:: python

    core_client.delete_node(my_node)

    assert core_client.get_node(my_node.id) is None

.. note::

    Creation, update and deletion isn't available for all resources. Check the :doc:`API Reference <api>` which methods
    are available for each resource.



.. toctree::
    :maxdepth: 2
    :caption: Contents

    user_guide
    testing
    api
