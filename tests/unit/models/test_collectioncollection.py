# -*- coding: utf-8 -*-
# (c) 2023 Brian Scholer (@briantist)

from itertools import product

from galactory.models import CollectionCollection


def test_collectioncollection_init_add(collection_data_factory):
    ci = collection_data_factory()

    cc = CollectionCollection()
    assert len(cc) == 0
    cc.add(collection_data_factory())
    assert len(cc) == 1
    assert len(cc[ci.fqcn]) == 1
    cc.add(collection_data_factory())
    assert len(cc) == 1 # same name
    assert len(cc[ci.fqcn]) == 1 # same version

    cnewver = collection_data_factory(version='9.8.7', sha256='Z')
    cc.add(cnewver)
    assert len(cc) == 1 # same name
    assert len(cc[ci.fqcn]) == 2
    assert cc[ci.fqcn].latest is cnewver


def test_collectioncollection_from_collections(collection_data_factory):
    namespaces = ['ns1', 'ns2']
    names = ['n1', 'n2']
    versions = ['1.2.3', '1.2.3-dev0', '9.8.7', '0.0.0']

    collections = [
        collection_data_factory(namespace=d[0], name=d[1], version=d[2], sha256=str(i))
        for i, d in enumerate(product(namespaces, names, versions))
    ]

    cc = CollectionCollection.from_collections(collections)

    assert len(cc) == len(namespaces) * len(names)

    for cg in cc.values():
        assert len(cg.versions) == len(versions)
        assert cg.latest.version == '9.8.7'
