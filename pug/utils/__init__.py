from pip._internal.commands import InstallCommand
import subprocess
import sys
import os
from functools import lru_cache
import click
from git import Repo
from collections import defaultdict


class keydefaultdict(defaultdict):
    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError( key )
        else:
            ret = self[key] = self.default_factory(key)
            return ret


# TODO: add context
@lru_cache()
def installed_packages(editable_only=False):
    command = [sys.executable, '-m', 'pip', 'list']
    if editable_only:
        command.append('-e')
    return [r.decode().split()[0].lower() for r in
            subprocess.check_output(command).split(b'\n')[2:-1]]


def package_is_installed(name):
    return name in installed_packages()


class Package(object):
    def __init__(self, name, distributions=None):
        self.name = name
        self.distributions = distributions or []

    def as_record(self):
        return f"{self.name} {'(Installed)' if self.installed else ''}\n    {self.short_description or ''}"

    @property
    def installed(self):
        return package_is_installed(self.name)

    @property
    def short_description(self):
        for distribution in self.distributions:
            if distribution.short_description:
                return distribution.short_description


class Distribution(object):
    distributor_name = ''

    def __init__(self, name, short_description, orgname=None):
        self.name = name
        self.orgname = orgname
        self.short_description = short_description

    def as_record(self):
        return f"{self.distributor_name}:{self.orgname + '/' if self.orgname else ''}{self.name} {'(Installed)' if self.installed else ''}\n    {self.short_description or ''}"

    @property
    def installed(self):
        return package_is_installed(self.name)

    def install(self, args):
        raise NotImplementedError


class PyPIDistribution(Distribution):
    distributor_name = 'pypi'

    def install(self, args):
        InstallCommand().main([self.name, *args])


class EditableDistribution(PyPIDistribution):
    distributor_name = 'editable'


class GitDistribution(Distribution):
    distributor_name = 'git'

    def __init__(self, *args, url, **kwargs):
        super(GitDistribution, self).__init__(*args, **kwargs)

        self.url = url

    def install(self, args):
        providers = ['editable clone', 'install to site-packages']

        print(f'There are {len(providers)} providers available for {self.name}:')
        for i, provider in reversed(list(enumerate(providers))):
            print(f"{[i+1]} {provider}")

        provider_index = int(input(f'Select a provider (default=1): ').strip() or 1)-1

        if not click.confirm('Do you want to continue?', default=True):
            return

        if provider_index == 0:  # editable clone
            clone_path = os.path.join(os.getcwd(), f'{self.name}/')
            Repo.clone_from(self.url, clone_path)
            InstallCommand().main(['-e', clone_path, *args])

        elif provider_index == 1:  # install to site-packages
            InstallCommand().main([f'git+{self.url}', *args])


class GithubDistribution(GitDistribution):
    ...


def print_distributions(distributions):
    for i, distro in reversed(list(enumerate(distributions))):
        print(f"[{i + 1}] {distro.as_record()}")


def print_packages(packages):
    for i, package in reversed(list(enumerate(packages.values()))):
        print(f"[{i + 1}] {package.as_record()}")


def parse_selection(selection, count):
    selected_indexes = set()

    for chunk in selection.split():
        if "-" in chunk:
            bounds = list(map(int, chunk.split("-")))
            selected_indexes.union(list(range(bounds[0], bounds[1] + 1)))

        elif "^" in chunk:
            exclusion = int(chunk[1:])
            selected_indexes.union(set(range(count)))
            selected_indexes.remove(exclusion)

        else:
            selected_indexes.add(int(chunk))

    return selected_indexes
