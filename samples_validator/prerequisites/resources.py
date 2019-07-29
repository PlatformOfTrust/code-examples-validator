from typing import Optional, Tuple

from samples_validator.conf import conf
from samples_validator.prerequisites.base import (
    _create_resource, _delete_resource, API_URL, Resource,
)


class Identity(Resource):

    def __init__(self, base_url: str = f'{API_URL}/identities/v1'):
        super().__init__(base_url)
        self._id_field = None

    def _create(
            self,
            payload: Optional[dict] = None) -> Tuple[int, Optional[dict]]:
        code, body = _create_resource(
            self.base_url, self.generate_payload(), conf.access_token,
        )
        if body:
            self._id_field = body.get('@id')
        return code, body

    def _delete(self) -> int:
        return _delete_resource(
            f'{self.base_url}/{self.id_field}',
            conf.access_token,
        )

    @property
    def id_field(self):
        return self._id_field

    def generate_payload(self):
        return {
            'name': 'code-examples-validator',
            'context': 'context',
            'type': 'Owner',
        }


class DeleteProduct(Resource):

    def __init__(self, base_url: str = f'{API_URL}/products/v1'):
        super().__init__(base_url)

    def _create(
            self,
            payload: Optional[dict] = None) -> Tuple[int, Optional[dict]]:
        code = _delete_resource(
            f'{self.base_url}/{self.id_field}',
            conf.access_token,
        )
        return code, None

    def _delete(self) -> int:
        return 200

    @property
    def id_field(self):
        return 'product-1'

    def generate_payload(self):
        return {}
