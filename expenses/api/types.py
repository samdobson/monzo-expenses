"""Classes for the various Monzo API response types."""

import abc
import datetime
import time
from typing import Any, Dict, List, Optional, Union

#pylint: disable=too-many-instance-attributes
#pylint: disable=too-many-locals

ACC_TYPE = {
        'uk_retail': 'personal',
        'uk_retail_joint': 'joint',
        'uk_prepaid': 'prepaid'
}

def _get_timestamp(string_value):
    """Gets the timestamp from the string provided by the APIs."""

    if not string_value:
        return None

    try:
        timestamp = time.strptime(string_value, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        timestamp = time.strptime(string_value, "%Y-%m-%dT%H:%M:%SZ")
    return datetime.datetime(*timestamp[:6])


class MonzoType(abc.ABC):
    """Base class for Monzo types."""

    @staticmethod
    def from_json(response: Dict[str, Any]) -> Any:
        """Convert the JSON from the API response into the object."""
        raise NotImplementedError()


class Owner(MonzoType):
    """A Monzo account owner"""

    user_id: str
    preferred_name: str
    preferred_first_name: str

    def __init__(self, *, user_id: str, preferred_name: str, preferred_first_name: str) -> None:
        self.user_id = user_id
        self.preferred_name = preferred_name
        self.preferred_first_name = preferred_first_name

    def __eq__(self, other):
        return self.user_id == other.user_id

    @staticmethod
    def from_json(response: Union[Dict[str, Any], List[Dict[str, Any]]]) -> List['Owner']:

        # Make sure we are always dealing with a list rather than just one
        if isinstance(response, list):
            owners_data = response
        else:
            owners_data = [response]

        results = []

        for owner_data in owners_data:
            results.append(Owner(
                user_id=owner_data["user_id"],
                preferred_name=owner_data["preferred_name"],
                preferred_first_name=owner_data["preferred_first_name"]
            ))

        return results


class Account(MonzoType):
    """A Monzo account"""

    identifier: str
    description: str
    created: datetime.datetime
    is_closed: bool
    account_type: str
    owners: List[Owner]
    account_number: Optional[str]
    sort_code: Optional[str]

    def __init__(
            self,
            *,
            identifier: str,
            description: str,
            created: datetime.datetime,
            is_closed: bool,
            account_type: str,
            owners: List[Owner],
            account_number: Optional[str],
            sort_code: Optional[str]
    ) -> None:
        self.identifier = identifier
        self.description = description
        self.created = created
        self.is_closed = is_closed
        self.account_type = account_type
        self.owners = owners
        self.account_number = account_number
        self.sort_code = sort_code

    def __eq__(self, other):
        return self.identifier == other.identifier

    @staticmethod
    def from_json(response: Dict[str, Any]) -> List['Account']:

        # Make sure we are always dealing with a list rather than just one
        if response.get('accounts') is None:
            accounts = [response]
        else:
            accounts = response['accounts']

        results = []

        for account in accounts:
            created_datetime = _get_timestamp(account["created"])
            results.append(Account(
                identifier=account["id"],
                description=account["description"],
                created=created_datetime,
                is_closed=account["closed"],
                account_type=ACC_TYPE[account["type"]],
                owners=Owner.from_json(account["owners"]),
                account_number=account.get("account_number"),
                sort_code=account.get("sort_code")
            ))

        return results

class Attachment(MonzoType):
    """A Monzo transaction attachment"""

    identifier: Optional[str]
    external_id: str
    file_type: str
    file_url: str
    user_id: str

    def __init__(
            self,
            *,
            identifier: Optional[str],
            external_id: str,
            file_type: str,
            file_url: str,
            user_id: str,
    ) -> None:
        self.identifier = identifier
        self.external_id = external_id
        self.file_type = file_type
        self.file_url = file_url
        self.user_id = user_id

    def __str__(self):
        return str({
            "identifier": self.identifier,
            "external_id": self.external_id,
            "file_type": self.file_type,
            "file_url": self.file_url,
            "user_id": self.user_id
        })

    @staticmethod
    def from_json(response: Dict[str, Any]) -> 'Attachment':
        return Attachment(
            identifier=response.get("id"),
            external_id=response["external_id"],
            file_type=response["file_type"],
            file_url=response["file_url"],
            user_id=response["user_id"]
        )

class Transaction(MonzoType):
    """A Monzo transaction. Only partially parsed."""

    identifier: str
    account_id: str
    user_id: str

    description: str

    amount: int
    currency: str
    category: str
    local_amount: int
    local_currency: str
    account_balance: int

    created: datetime.datetime
    updated: datetime.datetime
    settled: Optional[datetime.datetime]

    attachments: List[Attachment]

    raw_data: Dict[str, Any]

    def __init__(
            self,
            *,
            identifier: str,
            account_id: str,
            user_id: str,
            description: str,
            amount: int,
            currency: str,
            category: str,
            local_amount: int,
            local_currency: str,
            account_balance: int,
            created: datetime.datetime,
            updated: datetime.datetime,
            settled: Optional[datetime.datetime],
            attachments: List[Attachment],
            raw_data: Dict[str, Any]
    ) -> None:
        self.identifier = identifier
        self.account_id = account_id
        self.user_id = user_id
        self.description = description
        self.amount = amount
        self.currency = currency
        self.category = category
        self.local_amount = local_amount
        self.local_currency = local_currency
        self.account_balance = account_balance
        self.created = created
        self.updated = updated
        self.settled = settled
        self.attachments = attachments
        self.raw_data = raw_data

    def __eq__(self, other):
        return self.identifier == other.identifier

    @staticmethod
    def from_json(response: Dict[str, Any]) -> List['Transaction']:
        # Make sure we are always dealing with a list rather than just one
        if response.get('transactions') is not None:
            transactions = response['transactions']
        elif response.get('transaction') is not None:
            transactions = [response['transaction']]
        else:
            transactions = [response]

        results = []

        for transaction in transactions:
            created_datetime = _get_timestamp(transaction["created"])
            updated_datetime = _get_timestamp(transaction["updated"])
            settled_datetime = _get_timestamp(transaction["settled"])

            attachments_data = transaction["attachments"]
            if attachments_data is None:
                attachments_data = []

            attachments = [Attachment.from_json(attachment_data) for attachment_data in attachments_data]

            results.append(Transaction(
                identifier=transaction["id"],
                account_id=transaction["account_id"],
                user_id=transaction["user_id"],
                description=transaction["description"],
                amount=transaction["amount"],
                currency=transaction["currency"],
                category=transaction["category"],
                local_amount=transaction["local_amount"],
                local_currency=transaction["local_currency"],
                account_balance=transaction["account_balance"],
                created=created_datetime,
                updated=updated_datetime,
                settled=settled_datetime,
                attachments=attachments,
                raw_data=transaction
            ))

        return results

