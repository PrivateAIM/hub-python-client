==========
User guide
==========


The ``flame_hub`` module contains three different clients that are meant to be imported by a user:

* :py:class:`.AuthClient`
* :py:class:`.CoreClient`
* :py:class:`.StorageClient`.

With these clients it is possible to access the endpoints of the Hub ``auth``, ``core`` and ``storage`` APIs
respectively. The signature of the clients is always the same since they inherit from the :py:class:`.BaseClient` class.

When initializing a client, there are some things to keep in mind.

* You *should* provide an instance of either :py:class:`.PasswordAuth` or :py:class:`.RobotAuth` to the ``auth``
  argument as these are the two main authentication schemes supported by the FLAME Hub.
* You *can* provide a custom ``base_url`` if you're hosting your own instance of the FLAME Hub, otherwise the client
  will use the default publicly available Hub instance https://privateaim.dev to connect to.
* You *should'nt* set ``client`` explicitly unless you know what you're doing. When providing any of the previous two
  arguments, a suitable client instance will be generated automatically.

Authentication functionalities are implemented in the ``flame_hub.auth`` module. For further information, check out the
documentation about the :doc:`authentication flows <authentication_api>`.


Handling resources
==================

Among other things, each client implements six methods for each of its resources. Below you can find a description and
the naming pattern for each of the methods. ``RESOURCE_NAME`` and ``RESOURCE_NAME_PLURAL`` have to be replaced by either
the singular or plural form of a specific resource name following the
`naming conventions of Python <https://peps.python.org/pep-0008/#function-and-variable-names>`_.

.. py:method:: get_RESOURCE_NAME(self, id: str | uuid.UUID | ResourceT, **params: typing.Unpack[GetKwargs]) -> ResourceT | None
    :no-index:

    Takes an ``id`` and returns the corresponding resource or :py:obj:`None` if there is no resource with that ``id``.
    ``id`` can either be a :py:class:`str`, an :py:class:`~uuid.UUID` or a resource of the exact type you are searching
    for. The last option is basically irrelevant unless the resource was updated in the meanwhile and you want to get
    the updated resource.

.. py:method:: get_RESOURCE_NAME_PLURAL(self, **params: typing.Unpack[GetKwargs]) -> list[ResourceT]
    :no-index:

    Returns a list of the first :python:`DEFAULT_PAGE_PARAMS["limit"]` resources. See
    :py:const:`~flame_hub._base_client.DEFAULT_PAGE_PARAMS` for the default setting.

.. py:method:: find_RESOURCE_NAME_PLURAL(self, **params: typing.Unpack[FindAllKwargs]) -> list[ResourceT]
    :no-index:

    Filters, sorts and pages resources and returns matching resources as a list. See :py:class:`.FindAllKwargs` for all
    possible keyword arguments and :ref:`finding-resources` for examples on how to find resources.

.. py:method:: create_RESOURCE_NAME(self, **params) -> ResourceT
    :no-index:

    Creates a new resource and returns it. ``params`` are keyword arguments that can be send to the Hub when creating a
    new resource of a specific type. To see what parameters can be specified on creation, have a look at the concrete
    *create* method or at the corresponding :doc:`create model <models_api>`.

.. py:method:: update_RESOURCE_NAME(self, id: str | uuid.UUID | ResourceT, **params) -> ResourceT
    :no-index:

    Updates the resource that matches a given ``id``. ``id`` can either be a :py:class:`str`, an :py:class:`~uuid.UUID`
    or a resource of the same type. ``params`` are keyword arguments that can be send to the Hub when updating an
    already existing resource of a specific type. To see what parameters can be specified on update, have a look at the
    concrete *update* method or at the corresponding :doc:`update model <models_api>`. Raises a :py:exc:`.HubAPIError`
    if there is no resource with this ``id``.

.. py:method:: delete_RESOURCE_NAME(self, id: str | uuid.UUID | ResourceT)
    :no-index:

    Deletes the resource that matches a given ``id``. ``id`` can either be a :py:class:`str`, an :py:class:`~uuid.UUID`
    or a resource of the same type. Raises a :py:exc:`.HubAPIError` if there is no resource with this ``id``.

.. hint::

    See :py:type:`~flame_hub._base_client.ResourceT` for further information on the base resource type.

.. note::

    Every resource model has an ``id`` attribute. If you commit a resource instance as an ``id`` to either a *get*,
    *update* or *delete* method, the client will automatically use the ``id`` attribute of the given resource.

.. warning::

    Creation, deletion or update methods are not implemented for all resources since there is no endpoint on the Hub in
    some cases. Please check the :doc:`API of the clients <clients_api>` to see which methods exist.


Overview of implemented resources
=================================

* :py:class:`.AuthClient`
    * realms
    * users
    * robots
    * permissions
    * roles
    * role permissions
    * user permissions
    * user roles
    * robot permissions
    * robot roles
* :py:class:`.CoreClient`
    * registries
    * registry projects
    * nodes
    * master image groups
    * master images
    * master image event logs
    * projects
    * project nodes
    * analyses
    * analysis logs
    * analysis nodes
    * analysis node logs
    * analysis buckets
    * analysis bucket files
* :py:class:`.StorageClient`
    * buckets
    * bucket files


.. _finding-resources:

Finding resources
=================

In almost all scenarios, you will want to use :py:meth:`find_RESOURCE_NAME_PLURAL` over
:py:meth:`get_RESOURCE_NAME_PLURAL` methods because they offer to find multiple resources that match
certain criteria. To start off with an example, we create a core client and authorize it.

.. code-block:: python

    import flame_hub

    auth = flame_hub.auth.PasswordAuth(
        username="admin", password="start123", base_url="http://localhost:3000/auth/"
    )
    core_client = flame_hub.CoreClient(base_url="http://localhost:3000/core/", auth=auth)

The ``page`` parameter enables control over the amount of returned results. You can define the limit and offset which
affects pagination. They default to :python:`limit=50` and :python:`offset=0`.

.. code-block:: python

    nodes_first_25 = core_client.find_nodes(page={"limit": 25})
    nodes_next_10 = core_client.find_nodes(page={"limit": 10, "offset": 10})

    assert nodes_first_25[10:20] == nodes_next_10

.. note::

    :python:`core_client.find_nodes(page=DEFAULT_PAGE_PARAMS)` is functionally equivalent to
    :python:`core_client.get_nodes()`. See :py:const:`~flame_hub._base_client.DEFAULT_PAGE_PARAMS` for the default
    setting.

The ``filter`` parameter allows you to filter by any fields. You can perform exact matching, but also any other
operation supported by the FLAME Hub, including *like* and *not* queries and numeric *greater than* and *less than*
comparisons.

.. code-block:: python

    print(core_client.find_nodes(filter={"name": "my-node-42"}).pop().model_dump_json(indent=2))

.. code-block:: console

    {
      "name": "my-node-42",
      "id": "2f8fc7df-d5ff-484c-bfed-76b8f3c43afd",
      ...
    }

You can also use the :py:class:`.FilterOperator` enum class which contains all possible operators.

.. code-block:: python

    from flame_hub.types import FilterOperator

    nodes_with_4_in_name = core_client.find_nodes(filter={"name": "~my-node-4"})
    nodes_with_4_in_name_but_different = core_client.find_nodes(
        filter={"name": (FilterOperator.like, "my-node-4")}
    )

    assert nodes_with_4_in_name == nodes_with_4_in_name_but_different

The ``sort`` parameter allows you to define a field to sort by in either ascending or descending order. If ``order`` is
left unset, the client will sort in ascending order by default.

.. code-block:: python

    nodes = core_client.find_nodes(sort={"by": "created_at"})
    sedon = core_client.find_nodes(sort={"by": "created_at", "order": "descending"})

    assert nodes == sedon[::-1]

See :py:class:`.FindAllKwargs` for the API documentation of all possible parameters.


Optional fields
===============

Some fields are not provided by default, such as the secret tied to a robot. You can explicitly request these fields
with the `fields` keyword argument.

.. code-block:: python

    import flame_hub

    auth = flame_hub.auth.PasswordAuth(
        username="admin", password="start123", base_url="http://localhost:3000/auth/"
    )
    auth_client = flame_hub.AuthClient(base_url="http://localhost:3000/auth/", auth=auth)

    system_robot = auth_client.find_robots(filter={"name": "system"}).pop()
    assert system_robot.secret is None

You have to request ``secret`` explicitly in order to get it.

.. code-block:: python

    system_robot = auth_client.find_robots(filter={"name": "system"}, fields="secret").pop()
    print(system_robot.secret)

.. code-block::

    $2y$10$KUOKEwbbnaUDo41e7XBKGek4hggD6z6R95I69Cv3mTeBcx0hifBAC

If you are ever unsure which fields can be requested this way on a specific resource, use :py:func:`.get_field_names`
function.

.. code-block:: python

    from flame_hub import get_field_names
    from flame_hub.models import Robot

    assert get_field_names(Robot) == ("secret",)


Meta information
================

Furthermore, it is possible to retrieve meta information for *find* and *get* methods via the ``meta`` keyword argument.
When set to :python:`True`, methods return a model containing all received meta data as a second value.

.. code-block:: python

    import flame_hub

    auth = flame_hub.auth.PasswordAuth(
        username="admin", password="start123", base_url="http://localhost:3000/auth/"
    )
    auth_client = flame_hub.AuthClient(base_url="http://localhost:3000/auth/", auth=auth)

    _, meta = auth_client.get_permissions(meta=True)
    print(meta.model_dump_json(indent=2))

.. code-block:: console

    {
        "total": 106,
        "limit": 50,
        "offset": 0
    }


Nested resources
================

Some resources refer to other resources. For example, users are tied to a realm which is usually not sent back
automatically. This applies to any other nested resource.

All clients will automatically fetch all nested resources if they are available. This means that you can usually save
yourself extra API calls. Be aware that the client is not capable of fetching nested resources on any level deeper than
the resource you are requesting.

.. code-block:: python

    import flame_hub

    auth = flame_hub.auth.PasswordAuth(
        username="admin", password="start123", base_url="http://localhost:3000/auth/"
    )
    auth_client = flame_hub.AuthClient(base_url="http://localhost:3000/auth/", auth=auth)

    admin_user = auth_client.find_users(filter={"name": "admin"}).pop()

    print(admin_user.id)
    print(admin_user.realm.model_dump_json(indent=2))

.. code-block:: console

    794f2375-f043-4789-bd0c-e5534e8deeaa
    {
      "name": "master",
      "display_name": null,
      "description": null,
      "id": "794f2375-f043-4789-bd0c-e5534e8deeaa",
      "built_in": true,
      "created_at": "2025-05-12T09:44:08.284000Z",
      "updated_at": "2025-05-12T09:44:08.284000Z"
    }

Since the realm ID is present, we can use the ``realm`` property too. And just to be extremely sure, we verify that the
admin's realm is the master realm.

.. code-block:: python

    master_realm = auth_client.find_realms(filter={"name": "master"}).pop()

    assert admin_user.realm == master_realm


Handling exceptions
===================

The ``flame_hub`` module exports :py:exc:`.HubAPIError` which is a general error that is raised whenever the FLAME Hub
responds with an unexpected status code. All clients will try and put as much information into the raised error as
possible, including status code and additional information in the response body.

.. code-block:: python

    import flame_hub
    from uuid import uuid4

    auth = flame_hub.auth.PasswordAuth(
        username="admin", password="start123", base_url="http://localhost:3000/auth/"
    )
    core_client = flame_hub.CoreClient(base_url="http://localhost:3000/core/", auth=auth)

    try:
        core_client.create_node(name="my-new-node", realm_id=str(uuid4()))
    except flame_hub.HubAPIError as e:
        print(e)
        print(e.error_response.model_dump_json(indent=2))

.. code-block:: console

    received status code 400 (undefined): Can't find realm entity by realm_id
    {
      "status_code": 400,
      "code": "undefined",
      "message": "Can't find realm entity by realm_id"
    }

In this example a :py:exc:`.HubAPIError` is raised because there is no realm with an ID that matches the dynamically
created ID. If the response body contains an error, it can be accessed with the ``error_response`` property. Some errors
may also add additional fields which can also be accessed like this.


Models
======

The ``flame_hub.models`` module contains all model definitions for resources emitted by the FLAME Hub. Use them at you
own discretion. They may change at any time.

Model classes whose names start with *Update* extend the special base class :py:class:`.UpdateModel` which needs to
distinguish between properties being :py:obj:`None` and being explicitly unset. :py:class:`~flame_hub.models.UNSET`
exists for this purpose, which is a sentinel value that should be used to mark a property as unset.

.. code-block:: python

    from flame_hub.models import UpdateNode, UNSET

    update_node = UpdateNode(hidden=False, external_name=None, type=UNSET)
    print(update_node.model_dump_json(indent=2, exclude_none=False, exclude_unset=True))

.. code-block:: console

    {
      "hidden": false,
      "external_name": null
    }

Check out all implemented models :doc:`here <models_api>`.


Types
=====

The ``flame_hub.types`` module contains type annotations that you might find useful when writing your own code. Check
out all implemented types :doc:`here <types_api>`.
