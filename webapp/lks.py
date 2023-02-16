import json
from dataclasses import dataclass
from urllib import parse, request

from authlib.integrations.flask_client import OAuth

from flask import Flask


@dataclass
class LksUserModel:
    id: int
    login: str  # "edu.mirea.ru" email
    email: str  # personal email
    name: str
    last_name: str | None
    second_name: str
    is_active: str
    personal_number: str
    academic_group: str


class LksOAuthHelper:
    def __init__(self):
        self.name = "lks"
        self.oauth = OAuth()
        self.lks_base_url: str | None = None

    def register(
        self,
        app: Flask,
        client_id: str,
        client_secret: str,
        lks_base_url: str,
    ):
        """Register the OAuth client with the Flask app. This must be called before any other methods."""

        self.oauth.register(
            name=self.name,
            client_id=client_id,
            client_secret=client_secret,
            access_token_url=f"{lks_base_url}/oauth/token",
            authorize_url=f"{lks_base_url}/oauth/authorize",
            api_base_url=f"{lks_base_url}/api",
            client_kwargs={"scope": "profile"},
        )

        self.lks_base_url = lks_base_url
        self.oauth.init_app(app)

    def request(
        self,
        method: str,
        url: str,
        token,
        data: dict = None,
        headers: dict = None,
        params: dict = None,
    ):
        """Send an authenticated request to the LKS API.

        `auth` is created using the access token from the JWT. For example:

        ```python
        token = {'token_type': 'bearer', 'access_token': '....', ...}
        auth = OAuth2Auth(token)
        ```
        """
        if headers is None:
            headers = {}
        headers |= {"Authorization": f"{token['token_type']} {token['access_token']}"}

        if params is not None:
            url = f"{url}?{parse.urlencode(params)}"

        if data is not None:
            data = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = request.Request(url, data=data, headers=headers, method=method)

        return request.urlopen(req)

    def get_me(self, token) -> "LksUserModel":
        """Get information about the current user."""

        if not self.lks_base_url:
            raise ValueError("LKS base URL not set. Call register() first.")

        res = self.request(
            "GET",
            f"{self.lks_base_url}/api/?action=getData&url=https://lk.mirea.ru/profile/",
            token=token,
        )

        json_res = json.loads(res.read())

        student = next(
            (
                element
                for element in json_res["STUDENTS"].values()
                if "Д" not in element["PROPERTIES"]["PERSONAL_NUMBER"]["VALUE"]
                and "Ж" not in element["PROPERTIES"]["PERSONAL_NUMBER"]["VALUE"]
            ),
            None,
        )

        try:
            return LksUserModel(
                id=json_res["ID"],
                login=json_res["arUser"]["LOGIN"],
                email=json_res["arUser"]["EMAIL"],
                name=json_res["arUser"]["NAME"],
                last_name=json_res["arUser"]["LAST_NAME"],
                second_name=json_res["arUser"]["SECOND_NAME"],
                is_active=student["ACTIVE"] == "Y",
                personal_number=student["PROPERTIES"]["PERSONAL_NUMBER"]["VALUE"],
                academic_group=student["PROPERTIES"]["ACADEMIC_GROUP"]["VALUE_TEXT"],
            )
        except KeyError as e:
            raise ValueError(f"Missing key in LKS response: {e}") from e


lks_oauth_helper = LksOAuthHelper()
