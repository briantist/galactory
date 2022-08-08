from threading import Thread

import pytest
from dohq_artifactory import User
from artifactory import ArtifactoryPath

import ansible_runner

import inspect


@pytest.fixture
def running_app(app):
    running = Thread(target=lambda: app.run('0.0.0.0', 54321, threaded=True), daemon=True)
    running.start()
    yield 'http://localhost:54321'
    running.

def test(test_collections, app):
    assert len(test_collections) == 4, f"{test_collections}"
    # a = ArtifactoryPath(artifactory) #, auth=('admin', 'password'))
    repository = ArtifactoryPath()



    for c in test_collections:
        out, err, rc = ansible_runner.run_command(
            executable_cmd='ansible-galaxy',
            cmdline_args=['collection', '-s',  'publish']
        )
        # response = client.post('/api/v2/collections/', )
        # data = response.json

    # raise Exception(inspect.getmembers(artifactory_generic_repository))
