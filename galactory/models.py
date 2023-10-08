# -*- coding: utf-8 -*-
# (c) 2023 Brian Scholer (@briantist)

import json

import typing as t
from typing import ValuesView

from semver import VersionInfo
from collections import UserDict
from dataclasses import dataclass
from functools import total_ordering, cached_property
from datetime import datetime

from artifactory import ArtifactoryPath


@total_ordering
@dataclass(eq=False, order=False)
class CollectionData:
    collection_info: dict
    created_datetime: datetime
    modified_datetime: datetime
    namespace: str
    name: str
    filename: str
    sha256: str
    size: int
    mime_type: str
    version: str

    @classmethod
    def from_artifactory_path(cls, *, path: ArtifactoryPath, properties: dict, stat: dict):
        collection_info = json.loads(properties['collection_info'][0])

        return cls(
            collection_info=collection_info,
            created_datetime=stat.ctime,
            modified_datetime=stat.mtime,
            namespace=properties['namespace'][0],
            name=properties['name'][0],
            filename=path.name,
            sha256=stat.sha256,
            size=stat.size,
            mime_type=stat.mime_type,
            version=properties['version'][0],
        )

    def __eq__(self, other) -> bool:
        # All of the comparable information is in the collection
        # tarball itself, so this should be a nice fast way of
        # comparing equality, without computing the cached_properties.
        try:
            return self.sha256 == other.sha256
        except AttributeError:
            # Allow for comparing directly with VersionInfo objects.
            if isinstance(other, VersionInfo):
                return self.semver == other
            return NotImplemented

    def __lt__(self, other) -> bool:
        this_is_prerelease = self.is_prerelease
        this_version = self.semver

        if isinstance(other, VersionInfo):
            other_is_prerelease = other.prerelease is not None
            other_version = other
        elif isinstance(other, CollectionData):
            other_is_prerelease = other.is_prerelease
            other_version = other.semver
            if self.name != other.name or self.namespace != other.namespace:
                return False
        else:
            return NotImplemented

        # Both objects are prerelease versions, or both are not, so compare normally.
        if this_is_prerelease == other_is_prerelease:
            return this_version < other_version

        # One of the objects is not a prerelease and the other is.
        # If self is a prerelease, then it is necessarily < the other.
        return this_is_prerelease

    @cached_property
    def fqcn(self) -> str:
        return f"{self.namespace}.{self.name}"

    @cached_property
    def created(self) -> str:
        return self.created_datetime.isoformat()

    @cached_property
    def modified(self) -> str:
        return self.modified_datetime.isoformat()

    @cached_property
    def semver(self) -> VersionInfo:
        return VersionInfo.parse(self.version)

    @cached_property
    def is_prerelease(self) -> bool:
        return self.semver.prerelease is not None


class CollectionGroup(UserDict):
    """
    A dict-like object that represents one or more
    versions of a single collection. The keys are
    VersionInfo objects and the values are
    CollectionData objects.
    """
    latest: CollectionData = None

    def __init__(self, *, namespace: str, name: str):
        self.namespace = namespace
        self.name = name
        super().__init__()

    @classmethod
    def from_collection(cls, collection: CollectionData):
        instance = cls(namespace=collection.namespace, name=collection.name)
        instance.add(collection)
        return instance

    @property
    def versions(self) -> t.Dict[VersionInfo, CollectionData]:
        return self.data

    @cached_property
    def fqcn(self) -> str:
        return f"{self.namespace}.{self.name}"

    def add(self, collection: CollectionData) -> None:
        self[collection.semver] = collection

    @staticmethod
    def _get_key(key: t.Union[str, VersionInfo], *, raises: bool = True) -> VersionInfo:
        if isinstance(key, VersionInfo):
            return key
        elif isinstance(key, str):
            return VersionInfo.parse(key)
        else:
            if raises:
                raise TypeError("Only valid semantic versions can be used as keys.")
            else:
                return key

    def __getitem__(self, key: t.Union[str, VersionInfo]) -> CollectionData:
        return super().__getitem__(self._get_key(key))

    def __setitem__(self, key: t.Union[str, VersionInfo], item: CollectionData) -> None:
        if not isinstance(item, CollectionData):
            raise TypeError("Values must be of type CollectionData.")

        if self.name != item.name or self.namespace != item.namespace:
            raise ValueError(f"Attempted to add collection '{item.namespace}.{item.name}' to group for '{self.namespace}.{self.name}'.")

        if self.latest is None or item > self.latest:
            self.latest = item

        return super().__setitem__(self._get_key(key), item)

    def __delitem__(self, key: t.Union[str, VersionInfo]) -> None:
        dkey = self._get_key(key)
        super().__delitem__(dkey)

        if self.latest == dkey:
            self.latest = max(self.values(), default=None)

    def __contains__(self, key: t.Union[str, VersionInfo]) -> bool:
        return super().__contains__(self._get_key(key, raises=False))

    # re-define for the type hints
    def values(self) -> ValuesView[CollectionData]:
        return super().values()


class CollectionCollection(UserDict):
    """
    A Dict[str, CollectionGroup] object where the keys are FQCNs.
    """
    @classmethod
    def from_collections(cls, collections: t.Iterable[CollectionData]):
        instance = cls()
        for collection in collections:
            instance.add(collection)
        return instance

    def add(self, collection: CollectionData) -> None:
        if collection.fqcn in self.data:
            self.data[collection.fqcn].add(collection)
        else:
            self.data[collection.fqcn] = CollectionGroup.from_collection(collection)

    # re-define for the type hints
    def values(self) -> ValuesView[CollectionGroup]:
        return super().values()
