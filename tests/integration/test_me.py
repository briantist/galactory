from dohq_artifactory import User
from artifactory import ArtifactoryPath

import inspect

def test(artifactory_generic_repository):
    # a = ArtifactoryPath(artifactory) #, auth=('admin', 'password'))

    raise Exception(inspect.getmembers(artifactory_generic_repository))
