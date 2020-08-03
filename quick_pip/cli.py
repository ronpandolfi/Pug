"""Console script for quick_pip."""
import argparse
from difflib import SequenceMatcher
import sys
import subprocess
from pip._internal import parse_command, commands_dict, commands
from github import Github
from .utils import PyPIDistribution, GithubDistribution, print_distributions, parse_selection, package_is_installed

g = Github()

MAX_DISTRIBUTION_CHOICES = {"pypi": 50,  # PyPi's search capabilites are lacking; results are presorted by some metric
                            "github": 10,
                            "total": 20}

# TODO: use pip-api

# TODO::: Implement Providers with first search just returning name matches, providers next

def main():
    """Console script for quick_pip."""
    parser = argparse.ArgumentParser()
    parser.add_argument('_', nargs='*')
    args = parser.parse_args()

    cmd_args = []
    cmd_name = None

    if len(args._) == 0:
        cmd_name = 'list'

    else:
        if package_is_installed(sys.argv[1]):
            commands.UninstallCommand().main(sys.argv[1:])

        else:
            distros = []

            # check if package is on pypi
            search_cmd = commands.SearchCommand()
            options, args = search_cmd.parse_args(sys.argv[1:])
            results = search_cmd.search(args, options)
            for result in results[:MAX_DISTRIBUTION_CHOICES['pypi']]:

                distros.append(PyPIDistribution(result['name'], mechanism='pypi', short_description=result['summary']))

            # check for packages on github
            repos = g.search_repositories(sys.argv[1]+" language:python")
            for repo in repos[:MAX_DISTRIBUTION_CHOICES['github']]:
                distros.append(GithubDistribution(repo.name, mechanism='git', short_description=repo.description, orgname=repo.owner.login, url=repo.clone_url))

            distros = sorted(distros, key=lambda distro: -SequenceMatcher(None, distro.name, sys.argv[1]).ratio())[:MAX_DISTRIBUTION_CHOICES['total']]

            print_distributions(distros)

            selected_indexes = parse_selection(input("==> Packages to install (eg: 1 2 3, 1-3 or ^4)\n==> "), len(distros))

            if selected_indexes:
                for i in selected_indexes:
                    distros[i-1].install(sys.argv[2:])
            else:
                print('There is nothing to do.')
                return 0






    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
