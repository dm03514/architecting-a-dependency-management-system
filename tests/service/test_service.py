import filecmp
import logging
import unittest

import os

import sys

import copy
import uuid

from depmgmtsystem.repos import packages
from depmgmtsystem.repos.deps import Repo
from depmgmtsystem.dependencies import Dep
from depmgmtsystem.decoders import DepsDecoder
from depmgmtsystem.trees.dep_tree import DepTree
from depmgmtsystem.trees.pkg_tree import FileSystemPackageTree

root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)


def _fixture_path_by_file_name(f_name):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'fixtures',
        f_name,
    )


class StubDecoder(DepsDecoder):

    def __init__(self, deps):
        self.deps = deps

    def decode(self):
        return self.deps


class StubDepsRepo(Repo):

    def __init__(self, dep_versions):
        self.dep_version = dep_versions

    def deps(self, package_name):
        return copy.deepcopy(self.dep_version.get(package_name, []))


class StubPackageRepo(packages.Repo):

    def download(self, name, version):
        return open(
            _fixture_path_by_file_name('stub-package.tar.gz'),
            'rb'
        ).read()


class ServiceTestCase(unittest.TestCase):
    def test_parse_file_build_tree(self):

        stub_decoder = StubDecoder(
            deps=[
                Dep(name='package-1', version=None),
                Dep(name='package-2-cli', version='==1.0.0'),
                Dep(name='another-package', version='>=0.9.7'),
            ]
        )

        deps_repo = StubDepsRepo(dep_versions={
            'another-package': [
                Dep('another-package', version='0.9.7'),
            ],
            'package-1': [
                Dep('package-1', version='0.0.1'),
            ],
            'package-2-deps-1-pkg': [
                Dep('package-2-deps-1-pkg', version='0.0.1'),
            ],
            'package-2-deps-2-pkg': [
                Dep('package-2-deps-2-pkg', version='0.0.1'),
            ],
            'package-2-cli': [
                Dep(name='package-2-cli', version='1.0.0', deps=[
                    Dep(name='package-2-deps-1-pkg', version='0.0.1'),
                    Dep(name='package-2-deps-2-pkg', version='0.0.1')
                ])
            ],
            'package-2-deps-1-pkg': [
                Dep(
                    name='package-2-depmgmtsystem-1-pkg',
                    version='0.0.1',
                    deps=[
                        Dep(name='recursive-deps', version='0.0.1'),
                    ]
                )
            ],
            'recursive-deps': [
                Dep('recursive-deps', version='0.0.1'),
            ],
        })

        fs_path = ['/', 'tmp', str(uuid.uuid1())]

        FileSystemPackageTree(
            dep_tree=DepTree(
                stub_decoder.decode(),
                deps_repo,
            ).tree(),
            root_dir_path=fs_path,
            pkg_repo=StubPackageRepo(),
        ).tree()

        comp = filecmp.dircmp(
            os.path.join(*(fs_path + ['deps'])),
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                'fixtures',
                'parse_file_build_tree_oracle',
                'deps',
            )
        )
        self.assertEqual(comp.diff_files, [])
