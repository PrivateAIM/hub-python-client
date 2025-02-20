__all__ = ["RobotAuth", "PasswordAuth"]

import httpx
from pydantic import BaseModel

import urllib.parse

from flame_hub import common


class AccessToken(BaseModel):
    access_token: str
    expires_in: int
    token_type: str
    scope: str


class RefreshToken(AccessToken):
    refresh_token: str


class RobotAuth(httpx.Auth):
    def __init__(
        self, robot_id: str, robot_secret: str, base_url=common.DEFAULT_AUTH_BASE_URL, client: httpx.Client = None
    ):
        self._robot_id = robot_id
        self._robot_secret = robot_secret
        self._base_url = urllib.parse.urlsplit(base_url)
        self._current_token = None
        self._current_token_expires_at = 0
        self._client = client or httpx.Client()

    def auth_flow(self, request):
        # check if token is not set or current token is expired
        if self._current_token is None or common.now() > self._current_token_expires_at:
            r = self._client.post(
                common.merge_parse_result(self._base_url, path=common.join_url_path(self._base_url.path, "token")),
                json={
                    "grant_type": "robot_credentials",
                    "id": self._robot_id,
                    "secret": self._robot_secret,
                },
            )

            r.raise_for_status()
            at = AccessToken(**r.json())

            self._current_token = at
            self._current_token_expires_at = common.now() + at.expires_in

        request.headers["Authorization"] = f"Bearer {self._current_token.access_token}"
        yield request


class PasswordAuth(httpx.Auth):
    def __init__(
        self, username: str, password: str, base_url=common.DEFAULT_AUTH_BASE_URL, client: httpx.Client = None
    ):
        self._username = username
        self._password = password
        self._base_url = urllib.parse.urlsplit(base_url)
        self._current_token = None
        self._current_token_expires_at = 0
        self._client = client or httpx.Client()

    def _update_token(self, token: RefreshToken):
        self._current_token = token
        self._current_token_expires_at = common.now() + token.expires_in

    def auth_flow(self, request):
        if self._current_token is None:
            r = self._client.post(
                common.merge_parse_result(self._base_url, path=common.join_url_path(self._base_url.path, "token")),
                json={
                    "grant_type": "password",
                    "username": self._username,
                    "password": self._password,
                },
            )

            r.raise_for_status()
            self._update_token(RefreshToken(**r.json()))

        # flow is handled using refresh token if a token was already issues
        if common.now() > self._current_token_expires_at:
            r = self._client.post(
                common.merge_parse_result(self._base_url, path=common.join_url_path(self._base_url.path, "token")),
                json={
                    "grant_type": "refresh_token",
                    "refresh_token": self._current_token.refresh_token,
                },
            )

            r.raise_for_status()
            self._update_token(RefreshToken(**r.json()))

        request.headers["Authorization"] = f"Bearer {self._current_token.access_token}"
        yield request
