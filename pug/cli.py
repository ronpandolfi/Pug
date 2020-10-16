"""Console script for pug."""
import argparse
from difflib import SequenceMatcher
import sys
from pip._internal import parse_command, commands_dict, commands
from .commands import refresh
from github import Github
from .utils import PyPIDistribution, GithubDistribution, print_distributions, print_packages, parse_selection, \
    package_is_installed, Package, keydefaultdict

g = Github()

MAX_DISTRIBUTION_CHOICES = {"pypi": 50,  # PyPi's search capabilites are lacking; results can only be sorted one way
                            "github": 10,
                            "total": 20}


# TODO: use pip-api


def main():
    """Console script for pug."""
    parser = argparse.ArgumentParser()
    parser.add_argument('_', nargs='*')
    args = parser.parse_args()

    if len(args._) == 0:
        commands.ListCommand().main(sys.argv[1:])

    elif args._[0] == 'refresh':
        refresh()

    else:

        packages = keydefaultdict(Package)

        # check if package is on pypi
        search_cmd = commands.SearchCommand()
        options, args = search_cmd.parse_args(sys.argv[1:])
        results = search_cmd.search(args, options)

        for result in results[:MAX_DISTRIBUTION_CHOICES['pypi']]:
            packages[result['name']].distributions.append(
                PyPIDistribution(result['name'], short_description=result['summary']))

        # check for packages on github
        repos = g.search_repositories(sys.argv[1] + " language:python")
        for repo in repos[:MAX_DISTRIBUTION_CHOICES['github']]:
            packages[repo.name].distributions.append(GithubDistribution(repo.name,
                                                                        short_description=repo.description,
                                                                        orgname=repo.owner.login,
                                                                        url=repo.clone_url))

        # sort by similarity to query name
        sorted_package_names = sorted(packages, key=lambda name: -SequenceMatcher(None, name, sys.argv[1]).ratio())[
                               :MAX_DISTRIBUTION_CHOICES['total']]
        packages = {name: packages[name] for name in sorted_package_names}

        print_packages(packages)

        selection = input("==> Packages to install (eg: 1 2 3, 1-3 or ^4)\n==> ")
        if not selection.strip():
            return 0

        selected_package_indexes = parse_selection(selection, len(packages))

        _package_names = list(packages.keys())
        selected_packages = {_package_names[i - 1]: packages[_package_names[i - 1]] for i in selected_package_indexes}
        if selected_packages:
            for package in selected_packages.values():
                if package.installed:
                    commands.UninstallCommand().main(sys.argv[1:])

                else:
                    distros = package.distributions

                    if len(distros) > 1:
                        print_distributions(distros)
                        selected_distribution_index = int(
                            input("==> Distribution to install (default=1)\n==> ").strip() or 1)

                    else:
                        selected_distribution_index = 1

                    distros[selected_distribution_index - 1].install(sys.argv[2:])
        else:
            print('There is nothing to do.')
            return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
