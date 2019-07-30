import json
from abc import abstractmethod
from typing import Dict, Optional, Tuple

import requests

from samples_validator.conf import conf
from samples_validator.reporter import debug

API_URL = f'https://{conf.api_url}'


def _create_resource(
        url: str,
        payload: Optional[dict] = None,
        access_token: Optional[str] = None,
        headers: Optional[dict] = None) -> Tuple[int, Optional[dict]]:
    if access_token:
        headers = headers or {}
        headers['Authorization'] = f'Bearer {access_token}'
    response = requests.post(url, json=payload, headers=headers)
    code = response.status_code
    if not response.ok:
        return code, None
    try:
        return code, response.json()
    except json.JSONDecodeError:
        return code, None


def _delete_resource(
        url: str,
        access_token: Optional[str] = None,
        headers: Optional[dict] = None) -> int:
    if access_token:
        headers = headers or {}
        headers['Authorization'] = f'Bearer {access_token}'
    response = requests.delete(url, headers=headers)
    return response.status_code


class Resource:

    def __init__(self, base_url: str):
        self.base_url = base_url
        self._created = False
        self._deleted = False

    def create(
            self,
            payload: Optional[dict] = None) -> Tuple[int, Optional[dict]]:
        debug(f'Creating {self.__class__.__name__}')
        code, response = self._create(payload)
        debug(f'Status code: {code}')
        self._created = True
        return code, response

    def delete(self) -> int:
        debug(f'Removing {self.__class__.__name__} <{self.id_field}>')
        response = self._delete()
        self._deleted = True
        return response

    @property
    def deleted(self):
        return self._deleted

    @abstractmethod
    def _create(
            self,
            payload: Optional[dict] = None) -> Tuple[int, Optional[dict]]:
        """Send a request to create a resource"""

    @abstractmethod
    def _delete(self) -> int:
        """Send a request to delete the resource"""

    @property
    @abstractmethod
    def id_field(self):
        """Identifier value within an API"""

    @abstractmethod
    def generate_payload(self):
        """Generate payload needed to create a resource"""


class ResourceRegistry:
    def __init__(self):
        self.resources = []

    def create(
            self,
            name: str,
            substitutions: Dict[str, str]) -> dict:

        from samples_validator.prerequisites import resources
        filtered_body = {}
        resource = getattr(resources, name)()
        status_code, body = resource.create()
        body = body or {}
        self.resources.append(resource)
        for key_from, key_to in substitutions.items():
            if key_from in body:
                filtered_body[key_to] = body[key_from]
        return filtered_body

    def cleanup(self):
        for resource in self.resources:
            if not resource.deleted:
                resource.delete()
