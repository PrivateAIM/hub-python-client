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
    def __init__(
        self,
        robot_id: str,
        robot_secret: str,
        base_url=DEFAULT_AUTH_BASE_URL,
        client: httpx.Client = None,
    ):
        self._robot_id = robot_id
        self._robot_secret = robot_secret
        self._current_token = None
        self._current_token_expires_at_nanos = 0
        self._client = client or httpx.Client(base_url=base_url)

    def auth_flow(self, request) -> t.Iterator[httpx.Request]:
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
    def __init__(self, username: str, password: str, base_url=DEFAULT_AUTH_BASE_URL, client: httpx.Client = None):
        self._username = username
        self._password = password
        self._current_token = None
        self._current_token_expires_at_nanos = 0
        self._client = client or httpx.Client(base_url=base_url)

    def _update_token(self, token: RefreshToken, request_nanos: int):
        self._current_token = token
        self._current_token_expires_at_nanos = request_nanos + secs_to_nanos(token.expires_in)

    def auth_flow(self, request) -> t.Iterator[httpx.Request]:
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
