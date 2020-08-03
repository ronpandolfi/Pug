from pip._internal.commands import InstallCommand
import subprocess
import sys
import os
from functools import lru_cache
import click
from git import Repo


# TODO: add context
@lru_cache()
def _installed_packages():
    return [r.decode().split()[0].lower() for r in
            subprocess.check_output([sys.executable, '-m', 'pip', 'list']).split(b'\n')[2:-1]]


def package_is_installed(name):
    return name in _installed_packages()


class Package(object):
    def __init__(self, name, distributions=None):
        self.name = name
        self.distributions = distributions or []


class Distribution(object):
    def __init__(self, name, mechanism, short_description, orgname=None):
        self.name = name
        self.mechanism = mechanism
        self.orgname = orgname
        self.short_description = short_description

    def as_record(self):
        return f"{self.mechanism}:{self.orgname + '/' if self.orgname else ''}{self.name} {'(Installed)' if self.installed else ''}\n    {self.short_description or ''}"

    @property
    def installed(self):
        return package_is_installed(self.name)

    def install(self, args):
        raise NotImplementedError


class PyPIDistribution(Distribution):

    def install(self, args):
        InstallCommand().main([self.name, *args])


class GitDistribution(Distribution):

    def __init__(self, *args, url, **kwargs):
        super(GitDistribution, self).__init__(*args, **kwargs)

        self.url = url

    def install(self, args):
        providers = ['editable clone', 'install to site-packages']

        print(f'There are {len(providers)} providers available for {self.name}:')
        for i, provider in enumerate(providers):
            print(f"{[i+1]} {provider}")

        provider_index = click.prompt(f'Select a provider:', type=int, default=1)-1

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
