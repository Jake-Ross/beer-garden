# -*- coding: utf-8 -*-
from base64 import b64decode

import tornado.web

from beer_garden.api.http.authorization import Permissions, authenticated
from beer_garden.api.http.base_handler import BaseHandler
from brewtils.errors import ModelValidationError
from brewtils.models import Operation


class FileAPI(BaseHandler):
    @authenticated(permissions=[Permissions.READ])
    async def get(self):
        """
        ---
        summary: Retrieve a specific file
        parameters:
          - name: file_id
            in: query
            required: true
            description: The ID of the file
            type: string
          - name: chunk
            in: query
            required: false
            description: The chunk number requested
            type: string
          - name: verify
            in: query
            required: false
            description: Flag that will cause verification information to
                         be returned instead of the file data
            type: bool
        responses:
          200:
            description: File with the given ID
            schema:
              $ref: '#/definitions/Request'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Files
        """
        file_id = self.get_argument("file_id", default=None)
        chunk = self.get_argument("chunk", default=None)
        verify = bool(self.get_argument("verify", default=False))

        if file_id is None:
            raise ValueError("Cannot fetch a file or chunk without a file ID.")

        response = await self.client(
            Operation(
                operation_type="FILE_FETCH",
                args=[file_id],
                kwargs={"chunk": chunk, "verify": verify},
            )
        )

        if response == "null":
            self.set_status(404)
        else:
            self.write(response)

    @authenticated(permissions=[Permissions.CREATE])
    async def post(self):
        """
        ---
        summary: Create a new Request
        parameters:
          - name: file_id
            in: query
            required: true
            description: The ID of the file
            type: string
          - name: data
            in: body
            required: true
            description: The Request definition
          - name: offset
            in: body
            required: true
            description: The current offset definition
        responses:
          201:
            description: A new Request has been created
            schema:
              $ref: '#/definitions/Request'
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Files
        """
        file_id = self.get_argument("file_id", default=None)
        upsert = self.get_argument("upsert", default=False)

        args = tornado.escape.json_decode(self.request.body)
        data = args.get("data", None)
        offset = args.get("offset", None)

        if file_id is None:
            raise ModelValidationError("No file id provided.")
        if data is None:
            raise ModelValidationError(f"No data sent to write to file {file_id}")
        if offset is None:
            raise ModelValidationError(
                f"No offset sent with data to write to file {file_id}"
            )

        response = await self.client(
            Operation(
                operation_type="FILE_CHUNK",
                args=[file_id, offset, b64decode(data).decode("utf-8")],
                kwargs={"upsert": upsert},
            )
        )
        self.write(response)

    async def delete(self):
        """
        ---
        summary: Create a new Request
        parameters:
          - name: file_id
            in: query
            required: true
            description: The ID of the file
            type: string
        responses:
          200:
            description: A new Request has been created
            schema:
              $ref: '#/definitions/Request'
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Files
        """
        file_id = self.get_argument("file_id", default=None)
        if file_id is None:
            raise ValueError("Cannot delete a file without an id.")

        response = await self.client(
            Operation(operation_type="FILE_DELETE", args=[file_id])
        )
        self.write(response)


class FileNameAPI(BaseHandler):
    @authenticated(permissions=[Permissions.READ])
    async def get(self):
        """
        ---
        summary: Retrieve a specific file
        parameters:
          - name: file_name
            in: query
            required: true
            description: The name of the file being sent
          - name: chunk_size
            in: query
            required: true
            description: The size of chunks the file is being broken into (in bytes)
          - name: file_size
            in: query
            required: true
            description: The total size of the file (in bytes)
        responses:
          200:
            description: File name to post with
            schema:
              $ref: '#/definitions/Request'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Files
        """
        file_name = self.get_argument("file_name", default="")
        file_size = self.get_argument("file_size", default=None)
        chunk_size = self.get_argument("chunk_size", default=None)
        file_id = self.get_argument("file_id", default=None)
        upsert = self.get_argument("upsert", default=False)
        owner_id = self.get_argument("owner_id", default=None)
        owner_type = self.get_argument("owner_type", default=None)

        if chunk_size is None:
            raise ModelValidationError(f"No chunk_size sent with file {file_name}.")
        if file_size is None:
            raise ModelValidationError(f"No file_size sent with file {file_name}.")

        response = await self.client(
            Operation(
                operation_type="FILE_CREATE",
                args=[file_name, int(file_size), int(chunk_size)],
                kwargs={
                    "file_id": file_id,
                    "upsert": upsert,
                    "owner_id": owner_id,
                    "owner_type": owner_type,
                },
            )
        )
        self.write(response)
