#!/usr/bin/env python3

import os
import json
from typing import Any, ClassVar, Dict, List, Optional
import webbrowser

import requests

from .exceptions import *
from .types import Account, Transaction
from . import utilities


#pylint: disable=too-many-public-methods


class MonzoClient():
    """Monzo API wrapper."""

    client_id: str
    client_secret: str
    access_token: Optional[str]
    account_id: Optional[str]
    state_token: str

    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.redirect_uri = redirect_uri
        self.account_id = None
        self.state_token = utilities.random_string(20)
        super().__init__()

    def authenticate(self) -> bool:

        server = utilities.OAuthServer(3456)

        url = 'https://auth.monzo.com/'
        url += f'?client_id={self.client_id}'
        url += f'&redirect_uri={self.redirect_uri}'
        url += f'&response_type=code'
        url += f'&state={self.state_token}'

        if not webbrowser.open(url):
            print('Here is your link to log in: ' + url)

        parameters = server.wait_for_call()

        if parameters is None:
            raise MonzoAPIError("Failed to authenticate correctly. The response parameters were invalid.")

        authorization_code = parameters["code"]

        if len(parameters["state"]) != 1:
            raise Exception("Invalid return state")

        state_value = parameters["state"][0]

        if self.state_token != state_value:
            raise Exception("State did not match")

        response = requests.post(
            'https://api.monzo.com/oauth2/token',
            data={
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri,
                "code": authorization_code
            }
        )

        data = response.json()

        path = os.path.dirname(__file__)
        with open(path + '/monzo.json', 'w') as fp:
            json.dump(data, fp, sort_keys=True, indent=4)

        self.access_token = data["access_token"]
        return True

    def _handle_response(self, response):
        """Handle API errors."""

        error_map = {
            400: MonzoBadRequestError,
            401: MonzoUnauthorizedError,
            403: MonzoForbiddenError,
            404: MonzoNotFoundError,
            405: MonzoMethodNotAllowedError,
            406: MonzoNotAcceptableError,
            429: MonzoTooManyRequestsError,
            500: MonzoInternalServerError,
            504: MonzoGatewayTimeoutError,
        }

        if response.status_code < 200 or response.status_code >= 300:
            error_class = error_map.get(response.status_code, MonzoAPIError)
            raise error_class(f"Error fetching request: ({response.status_code}): {response.text}")

        return response

    def get(self, path: str):
        """Make a GET request."""
        url = f'https://api.monzo.com/{path}'
        return self._handle_response(requests.get(
            url,
            headers={'Authorization': f'Bearer {self.access_token}'}
        ))

    def accounts(self) -> List[Account]:
        """Return list of accounts."""
        response = self.get('accounts')
        return Account.from_json(response.json())

    def transactions(self, *, account_id: str) -> List[Transaction]:
        """Retrieve a list of transactions."""
        response = self.get(f'transactions?account_id={account_id}&expand[]=merchant')
        return Transaction.from_json(response.json())

    def transaction(self, *, identifier: str) -> Transaction:
        """Get an individual transaction."""
        response = self.get(f'transactions/{identifier}?expand[]=merchant')
        return Transaction.from_json(response.json())[0]

