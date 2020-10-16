from .utils import installed_packages, EditableDistribution
from pip._internal import commands


def refresh():
    for package in installed_packages(editable_only=True):
        EditableDistribution(package, short_description=f'Editable install of {package}')
        print(f'Successfully refreshed entry points of {package}')


commands_dict = {'refresh': refresh}
