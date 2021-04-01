import functools
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import ileapp.globals as g
import ileapp.report.webicons as webicons
import jinja2
from ileapp import VERSION, __authors__, __contributors__
from ileapp.report.ext import IncludeLogFileExtension

jinja = jinja2.Environment


def init_jinja(log_folder):
    """Sets up Jinja2 templating for HTML report

    Args:
        log_folder (Path): Log folder for the log output]
    """

    global jinja
    template_loader = jinja2.PackageLoader('ileapp.report', 'templates')
    log_file_loader = jinja2.FileSystemLoader(log_folder)

    jinja = jinja2.Environment(
        loader=jinja2.ChoiceLoader([template_loader, log_file_loader]),
        autoescape=jinja2.select_autoescape(['html', 'xml']),
        extensions=[jinja2.ext.do,
                    IncludeLogFileExtension],
        trim_blocks=True,
        lstrip_blocks=True,
    )


class Template:
    """Template decorator for HTML pages

       This is used to decorate a custom class's HTML function to change
       the Jinja2 template being used.

       Example:

           Create a new class extending from HtmlPage base class. Then,
           create a `html()` function which is decorated by this function
           which provides the template name. This function will attached
           the `template` attribute automatically which is used to return the
           HTML of the template page.

           This replaces the default report page with this template.

           class MyCustomPage(HtmlPage):
               @Template('mytemplate')
               def html(self) -> str:
                   return self.template.render(renderingVals)

        Args:
            template(str): Name of Jinja template without extension.
                Must be in template folder.
    """
    def __init__(self, template: str):
        self._template = f'{template}.jinja'

    def __call__(self, func):
        @functools.wraps(func)
        def template_wrapper(cls, *args):
            template_j = jinja.get_template(self._template, None)
            setattr(cls, 'template', template_j)
            return func(cls)
        return template_wrapper


@dataclass
class Contributor:
    """Contributor's information displayed on main index page.

    Attributes:
        name (str): Name of Contributor
        website(str): Website of Contributor
        twitter (str): Twitter handle of the Contributor
        github (str): Github url for Contributor
    """
    name: str
    website: str = ''
    twitter: str = ''
    github: str = ''


@dataclass
class NavigationItem:
    """Navigation item for HTML report

    Attributes:
        name (str): Artifact Name
        href (str): URL of Artifact's report
        web_icon (webicons.Icon): Feather ICON for Artifact in
            the navigation list
    """
    name: str
    href: str
    web_icon: webicons.Icon


def get_contributors(contributors) -> List[Contributor]:
    """Returns a list of Contributors from `ileapp.__contributors__`

    Args:
        contributors (list): List of contributors

    Returns:
        List(Contributor): List of contributors objects for HTML Report
    """
    contrib_list = []

    for row in contributors:
        contrib_list.append(Contributor(*row))
    return contrib_list


def generate_nav(report_folder, selected_artifacts) -> dict:
    """Generates a dictionary containing the navigation of the
       report.

    Args:
        report_folder (Path): Report folder where Artifact HTML Reports
            are saved.
        selected_artifacts (List[AbstractArtifact]): List of selected
            Artifacts for the report

    Returns:
        dict: dictionary of navigation items for HTML Report
    """
    nav = defaultdict(set)

    for _, artifact in selected_artifacts:
        if not artifact.core:
            temp_item = NavigationItem(
                name=artifact.name,
                web_icon=artifact.web_icon.value,
                href=(report_folder
                      / f'{artifact.category} - {artifact.name}.html'))
            nav.update({artifact.category: temp_item})
    return dict(nav)


@dataclass
class _HtmlPageDefaults:
    """HTML page defaults for the HTML page

    Attributes:
        report_folder (Path): Report folder where Artifact HTML Reports
            are saved.
        log_folder (Path): Log folder for the log output
        extraction_type (str): Type of the extraction
        processing_time (float): Float number for time it took to run
            application
        device (Device): Extracted device information object
        project (str): project name
        version (str): project version
        navigation (dict): Navigation of the HTML report
    """
    report_folder: Path = field(default='', init=True)
    log_folder: Path = field(default='', init=True)
    extraction_type: str = field(default='fs', init=True)
    processing_time: float = field(default=0.0, init=True)
    device: g.Device = field(default=g.device, init=False)
    project: str = field(default=VERSION.split(' ')[0], init=False)
    version: str = field(default=VERSION.split(' ')[1], init=False)
    navigation: dict = field(default_factory=lambda: {}, init=False)


@dataclass
class HtmlPage(ABC, _HtmlPageDefaults):

    @abstractmethod
    def html(self):
        raise NotImplementedError(
            'HtmlPage objects must implement \'html()\' method!')


@dataclass
class Index(HtmlPage):
    """Main index page for HTML report

    Attributes:
        authors (list): list of authors
        contributors (list): list of contributors
    """
    authors: list = field(
        init=False, default_factory=lambda: get_contributors(__authors__))
    contributors: list = field(
        init=False, default_factory=lambda: get_contributors(__contributors__))

    @Template('index')
    def html(self) -> str:
        """Generates html for page

        Note:
            A 'empty' artifact object is used here to generate the report.
            Every HTML page is attached to an artifact but this one which is
            the reason the usage of the 'fake' artifact.

        Returns:
            str: HTML of the page
        """
        from ileapp.abstract import AbstractArtifact

        class Artifact(AbstractArtifact):
            def process(self):
                pass

        artifact = Artifact()
        artifact.html_report = self
        log_file = str((self.log_folder / 'ileapp.log').absolute())

        return self.template.render(artifact=artifact,
                                    log_file=log_file,
                                    navigation=self.navigation)