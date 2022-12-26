# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

from galactory import constants as C


# can't use trailer fixture here
# for some reason with internal client,
# .get('') gives a 308 redirect, even
# though that doesn't happen with a real
# webserver and request.
def test_root(client):
    response = client.get('/')
    data = response.text

    assert response.status_code == C.HTTP_OK
    assert data == 'Galactory is running'
