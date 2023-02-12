from dataclasses import dataclass

import requests
from authlib.integrations.flask_client import OAuth
from authlib.integrations.requests_client import OAuth2Auth

from flask import Flask


oauth = OAuth()


def init_app(
    app: Flask,
    client_id: str,
    client_secret: str,
    lks_base_url: str,
):
    """Register the OAuth client with the Flask app. This must be called before any other methods."""

    oauth.register(
        name="lks",
        client_id=client_id,
        client_secret=client_secret,
        access_token_url=f"{lks_base_url}/oauth/token",
        authorize_url=f"{lks_base_url}/oauth/authorize",
        api_base_url=f"{lks_base_url}/api",
        client_kwargs={"scope": "profile"},
    )

    oauth.init_app(app)


def request(
    method: str,
    url: str,
    auth: OAuth2Auth,
    data: dict = None,
    json: dict = None,
    headers: dict = None,
    params: dict = None,
    **kwargs,
) -> requests.Response:
    """Send an authenticated request to the LKS API.

    `auth` is created using the access token from the JWT. For example:

    ```python
    token = {'token_type': 'bearer', 'access_token': '....', ...}
    auth = OAuth2Auth(token)
    ```
    """

    return requests.request(
        method,
        url,
        data=data,
        json=json,
        headers=headers,
        params=params,
        auth=auth,
        **kwargs,
    )


def get_me(auth: OAuth2Auth) -> "LksUserModel":
    """Get information about the current user."""

    res = request(
        "GET",
        "https://auth-app.mirea.ru/api/?action=getData&url=https://lk.mirea.ru/profile/",
        auth=auth,
    )

    res.raise_for_status()

    json = res.json()

    student = next(
        (
            element
            for element in json["STUDENTS"].values()
            if "Д" not in element["PROPERTIES"]["PERSONAL_NUMBER"]["VALUE"]
            and "Ж" not in element["PROPERTIES"]["PERSONAL_NUMBER"]["VALUE"]
        ),
        None,
    )

    try:
        return LksUserModel(
            id=json["ID"],
            login=json["arUser"]["LOGIN"],
            email=json["arUser"]["EMAIL"],
            name=json["arUser"]["NAME"],
            last_name=json["arUser"]["LAST_NAME"],
            second_name=json["arUser"]["SECOND_NAME"],
            is_active=student["ACTIVE"] == "Y",
            personal_number=student["PROPERTIES"]["PERSONAL_NUMBER"]["VALUE"],
            academic_group=student["PROPERTIES"]["ACADEMIC_GROUP"]["VALUE_TEXT"],
        )
    except KeyError as e:
        raise ValueError(f"Missing key in LKS response: {e}") from e


@dataclass
class LksUserModel:
    id: int
    login: str
    email: str
    name: str
    last_name: str | None
    second_name: str
    is_active: str
    personal_number: str
    academic_group: str
