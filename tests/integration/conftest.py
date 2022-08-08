import pytest
import requests
from urllib.parse import urljoin
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

from pathlib import Path
from artifactory import ArtifactoryPath, RepositoryLocal
from dohq_artifactory import User

import ansible_runner

from galactory import create_app

# @pytest.fixture(autouse=True, scope='session')
# def broken():
#     pytest.skip('Integration tests are incomplete and disabled.')

@pytest.fixture
def app(repository, artifactory_user):
    app = create_app()
    app.config.update({
        'ARTIFACTORY_PATH': repository,
        'ARTIFACTORY_API_KEY': artifactory_user.api_key.get(),
    })
    yield app


@pytest.fixture
def app_request_context(app):
    with app.app_context(), app.test_request_context():
        yield


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(scope="session")
def test_collections(collection_finder, data_finder):
    collections = Path(collection_finder())
    runtime = Path(data_finder('runtime'))
    for collection in collections.iterdir():
        for version in collection.iterdir():
            out, err, rc = ansible_runner.run_command(
                executable_cmd='ansible-galaxy',
                cmdline_args=['collection', 'build', '--force', '--output-path', str(runtime.absolute()), str(version.absolute())]
            )
            assert rc == 0 , f"stdout: {out}\nstderr: {err}"

    return [d for d in runtime.rglob('*.tar.gz')]


@pytest.fixture(scope='session')
def artifactory(session_scoped_container_getter):
    request_session = requests.Session()
    retries = Retry(
        total=30,
        backoff_factor=0.1,
        status_forcelist=[500, 502, 503, 504],
    )
    request_session.mount('http://', HTTPAdapter(max_retries=retries))

    service = session_scoped_container_getter.get("artifactory").network_info[0]
    artifactory_url = "http://%s:%s/artifactory" % (service.hostname, service.host_port)
    readiness_url = "%s/api/v1/system/readiness" % (artifactory_url,)
    request_session.get(readiness_url)
    return ArtifactoryPath(artifactory_url)
    # return request_session, api_url


@pytest.fixture(scope='session')
def artifactory_user(artifactory):
    user = User(artifactory, name='admin', password='password')
    apikey = user.api_key.get()
    if not apikey:
        user.api_key.create()

    return user


@pytest.fixture(scope='session')
def artifactory_authed(artifactory, artifactory_user):
    return ArtifactoryPath(artifactory, apikey=artifactory_user.api_key.get())


@pytest.fixture(scope='session')
def artifactory_generic_repository(artifactory_authed):
    name = 'example-repo-local'
    # repo = artifactory_authed.find_repository_local(name)
    # ^ can't use this, requires pro license 🙄

    for repo in artifactory_authed.get_repositories():
        if repo.name == name:
            if repo.package_type == RepositoryLocal.GENERIC:
                return repo
            else:
                raise ValueError("existing repository is the wrong type.")

    # this is going to fail without a pro license
    repo = RepositoryLocal(artifactory_authed, name=name, package_type=RepositoryLocal.GENERIC)
    repo.create()

    return repo


@pytest.fixture
def repository(artifactory_generic_repository):
    return artifactory_generic_repository.path / 'repo' / 'subpath'
