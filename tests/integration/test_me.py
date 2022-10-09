from threading import Thread

import pytest
from dohq_artifactory import User
from artifactory import ArtifactoryPath

from base64io import Base64IO

from flask import request
import requests

import ansible_runner

import inspect


# @pytest.fixture
# def running_app(app):
#     @app.route('/_shutdown', methods=['DELETE'])
#     def _shutdown():
#         f_shutdown = request.environ.get('werkzeug.server.shutdown')
#         f_shutdown()
#         return 'Exiting...'

#     listen = '0.0.0.0'
#     port = 54321
#     host = 'localhost'
#     url = f"http://{host}:{port}"
#     shutdown = f"{url}/_shutdown"

#     running = Thread(target=lambda: app.run(listen, port, threaded=True), daemon=True)
#     running.start()
#     yield url
#     requests.delete(shutdown)


def test(test_collections, app, client):
    assert len(test_collections) == 4, f"{test_collections}"
    # a = ArtifactoryPath(artifactory) #, auth=('admin', 'password'))
    repository = ArtifactoryPath()



    for c in test_collections:
        # out, err, rc = ansible_runner.run_command(
        #     executable_cmd='ansible-galaxy',
        #     cmdline_args=['collection', '-s', running_app, 'publish', c]
        # )
        import hashlib

        sha256sum = hashlib.sha256()
        chunk_size = sha256sum.block_size

        from io import BytesIO
        with c.open('rb') as h, BytesIO() as b:
            with Base64IO(b) as b64:
                for data in iter(lambda: h.read(chunk_size), b''):
                    sha256sum.update(data)
                    b64.write(data)

            b.seek(0)
            response = client.post(
                '/api/v2/collections/',
                data=dict(sha256=sha256sum.hexdigest(), file=(b, c.name)),
            )

        assert response.status_code == 200, response.text
        # data = response.json

    # raise Exception(inspect.getmembers(artifactory_generic_repository))
