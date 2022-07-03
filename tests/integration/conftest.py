import pytest
import requests
from urllib.parse import urljoin
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

from artifactory import ArtifactoryPath, RepositoryLocal
from dohq_artifactory import User


@pytest.fixture(autouse=True, scope='session')
def broken():
    pytest.skip('Integration tests are incomplete and disabled.')


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
def repository(artifactory):
    return ArtifactoryPath(f"{artifactory}/repo/subpath")
