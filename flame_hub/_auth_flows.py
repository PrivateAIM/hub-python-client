import time
import typing as t

import httpx
from pydantic import BaseModel

from flame_hub._defaults import DEFAULT_AUTH_BASE_URL
from flame_hub._exceptions import new_hub_api_error_from_response


def secs_to_nanos(seconds: int) -> int:
    return seconds * (10**9)


class AccessToken(BaseModel):
    access_token: str
    expires_in: int
    token_type: str
    scope: str


class RefreshToken(AccessToken):
    refresh_token: str


class RobotAuth(httpx.Auth):
    """Robot authentication for the FLAME Hub.

    This class implements a robot authentication flow which is one possible flow that is recognized by the FLAME Hub. It
    is derived from the ``httpx`` base class for all authentication flows ``httpx.Auth``. For more information about
    this base class, click
    `here <https://www.python-httpx.org/advanced/authentication/#custom-authentication-schemes>`_. Note that
    ``base_url`` is ignored if you pass your own client via the ``client`` keyword argument. An instance of this class
    could be used for authentication to access the Hub endpoints via the clients.

    Parameters
    ----------
    robot_id : :py:class:`str`
        The ID of the robot which is used to execute the authentication flow.
    robot_secret : :py:class:`str`
        The secret which corresponds to the robot with ID ``robot_id``.
    base_url : :py:class:`str`, default=\\ :py:const:`~flame_hub._defaults.DEFAULT_AUTH_BASE_URL`
        The base URL for the authentication flow.
    client : :py:class:`httpx.Client`
        Pass your own client to avoid the instantiation of a client while initializing an instance of this class.

    See Also
    --------
    :py:class:`.AuthClient`, :py:class:`.CoreClient`, :py:class:`.StorageClient`
    """

    def __init__(
        self,
        robot_id: str,
        robot_secret: str,
        base_url: str = DEFAULT_AUTH_BASE_URL,
        client: httpx.Client = None,
    ):
        self._robot_id = robot_id
        self._robot_secret = robot_secret
        self._current_token = None
        self._current_token_expires_at_nanos = 0
        self._client = client or httpx.Client(base_url=base_url)

    def auth_flow(self, request) -> t.Iterator[httpx.Request]:
        """Executes the robot authentication flow.

        This method checks if the current access token is not set or expired and, if so, requests a new one from the Hub
        instance. It then yields the authentication request. Click
        `here <https://www.python-httpx.org/advanced/authentication/#custom-authentication-schemes>`_ for further
        information on this method.

        See Also
        --------
        :py:class:`.AccessToken`
        """

        # check if token is not set or current token is expired
        if self._current_token is None or time.monotonic_ns() > self._current_token_expires_at_nanos:
            request_nanos = time.monotonic_ns()

            r = self._client.post(
                "token",
                json={
                    "grant_type": "robot_credentials",
                    "id": self._robot_id,
                    "secret": self._robot_secret,
                },
            )

            if r.status_code != httpx.codes.OK.value:
                raise new_hub_api_error_from_response(r)

            at = AccessToken(**r.json())

            self._current_token = at
            self._current_token_expires_at_nanos = request_nanos + secs_to_nanos(at.expires_in)

        request.headers["Authorization"] = f"Bearer {self._current_token.access_token}"
        yield request


class PasswordAuth(httpx.Auth):
    """Password authentication for the FLAME Hub.

    This class implements a password authentication flow which is one possible flow that is recognized by the FLAME Hub.
    It is derived from the ``httpx`` base class for all authentication flows ``httpx.Auth``. For more information about
    this base class, click
    `here <https://www.python-httpx.org/advanced/authentication/#custom-authentication-schemes>`_. Note that
    ``base_url`` is ignored if you pass your own client via the ``client`` keyword argument. An instance of this class
    could be used for authentication to access the Hub endpoints via the clients.

    Parameters
    ----------
    username : :py:class:`str`
        The user's name which is used to execute the authentication flow.
    password : :py:class:`str`
        The password which corresponds to ``username``.
    base_url : :py:class:`str`, default=\\ :py:const:`~flame_hub._defaults.DEFAULT_AUTH_BASE_URL`
        The base URL for the authentication flow.
    client : :py:class:`httpx.Client`
        Pass your own client to avoid the instantiation of a client while initializing an instance of this class.

    See Also
    --------
    :py:class:`.AuthClient`, :py:class:`.CoreClient`, :py:class:`.StorageClient`
    """

    def __init__(
        self,
        username: str,
        password: str,
        base_url: str = DEFAULT_AUTH_BASE_URL,
        client: httpx.Client = None,
    ):
        self._username = username
        self._password = password
        self._current_token = None
        self._current_token_expires_at_nanos = 0
        self._client = client or httpx.Client(base_url=base_url)

    def _update_token(self, token: RefreshToken, request_nanos: int):
        """Overwrites the current token and calculates the expiring point in time for the new token.

        Parameters
        ----------
        token : :py:class:`.RefreshToken`
            A new refresh token which replaces the current token.
        request_nanos : :py:class:`int`
            The point in time where the request was sent that had ``token`` as a response. The unit of this argument
            needs to be nanoseconds.

        See Also
        --------
        :py:class:`.RefreshToken`
        """
        self._current_token = token
        self._current_token_expires_at_nanos = request_nanos + secs_to_nanos(token.expires_in)

    def auth_flow(self, request) -> t.Iterator[httpx.Request]:
        """Executes the password authentication flow.

        If there is no token set, this method requests a new refresh token by using ``username`` and ``password``. If
        the token is just expired, the current token is used to request a new one so that the old one can be replaced by
        the new refresh token. It then yields the authentication request. Click
        `here <https://www.python-httpx.org/advanced/authentication/#custom-authentication-schemes>`_ for further
        information on this method.

        See Also
        --------
        :py:class:`.RefreshToken`
        """
        if self._current_token is None:
            request_nanos = time.monotonic_ns()

            r = self._client.post(
                "token",
                json={
                    "grant_type": "password",
                    "username": self._username,
                    "password": self._password,
                },
            )

            if r.status_code != httpx.codes.OK.value:
                raise new_hub_api_error_from_response(r)

            self._update_token(RefreshToken(**r.json()), request_nanos)

        # flow is handled using refresh token if a token was already issued
        if time.monotonic_ns() > self._current_token_expires_at_nanos:
            request_nanos = time.monotonic_ns()

            r = self._client.post(
                "token",
                json={
                    "grant_type": "refresh_token",
                    "refresh_token": self._current_token.refresh_token,
                },
            )

            if r.status_code != httpx.codes.OK.value:
                raise new_hub_api_error_from_response(r)

            self._update_token(RefreshToken(**r.json()), request_nanos)

        request.headers["Authorization"] = f"Bearer {self._current_token.access_token}"
        yield request
