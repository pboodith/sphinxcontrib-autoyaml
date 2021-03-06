import os

from docutils.statemachine import ViewList
from docutils.parsers.rst import Directive
from docutils import nodes
from sphinx.util import logging
from sphinx.util.nodes import nested_parse_with_titles
from sphinx.ext.autodoc import AutodocReporter
from sphinx.errors import ExtensionError


logger = logging.getLogger(__name__)


class AutoYAMLException(ExtensionError):

    category = 'AutoYAML error'


class AutoYAMLDirective(Directive):

    required_arguments = 1

    def run(self):
        self.config = self.state.document.settings.env.config
        self.env = self.state.document.settings.env
        self.record_dependencies = \
            self.state.document.settings.record_dependencies
        location = os.path.normpath(
            os.path.join(self.env.srcdir,
                         self.config.autoyaml_root
                         + '/' + self.arguments[0]))
        self.result = ViewList()
        if os.path.isfile(location):
            logger.debug('[autoyaml] parsing file: %s', location)
            self.parse_file(location)
        else:
            raise AutoYAMLException('%s:%s: location "%s" is not a file.' % (
                                    self.env.doc2path(self.env.docname, None),
                                    self.content_offset - 1,
                                    location))
        self.record_dependencies.add(location)
        print(self.result)
        node = nodes.paragraph()
        # parse comment internals as reST
        old_reporter = self.state.memo.reporter
        self.state.memo.reporter = AutodocReporter(
            self.result, self.state.memo.reporter)
        nested_parse_with_titles(self.state, self.result, node)
        self.state.memo.reporter = old_reporter
        return [node]

    def parse_file(self, source):
        with open(source, 'r') as src:
            lines = src.read().splitlines()
        in_docstring = False
        in_parameter = False
        for linenum, line in enumerate(lines, start=1):
            if line.startswith(self.config.autoyaml_doc_delimiter):
                in_docstring = True
                # self._parse_line('', source, linenum)
                self._parse_line(line, source, linenum, True)
            elif line.startswith(self.config.autoyaml_doc_parameter) \
                    and in_parameter:
                in_parameter = True
                self._parse_line('', source, linenum)
                self._parse_parameter(line, source, linenum, True)
            elif line.startswith(self.config.autoyaml_doc_parameter) \
                    and in_docstring:
                in_parameter = True
                self._parse_line('', source, linenum)
                self._parse_parameter(line, source, linenum)
            elif line.startswith(self.config.autoyaml_comment) \
                    and in_docstring:
                self._parse_line('', source, linenum)
                self._parse_line(line, source, linenum)
            else:
                in_docstring = False
                in_parameter = False
                # add terminating newline
                self._parse_line('', source, linenum)

    def _parse_line(self, line, source, linenum, starting=False):
        if starting:
            docstring = line[len(self.config.autoyaml_doc_delimiter):]
        else:
            docstring = line[len(self.config.autoyaml_comment):]
        # strip preceding whitespace
        if docstring and docstring[0] == ' ':
            docstring = docstring[1:]
        self.result.append(docstring, source, linenum)

    def _parse_parameter(self, line, source, linenum, continuation=False):
        if continuation:
            docstring = line[2:]
        else:
            docstring = line[2:]
        # strip preceding whitespace
        # if docstring and docstring[0] == ' ':
        #     docstring = docstring[1:]
        self.result.append(docstring, source, linenum)

def setup(app):
    app.add_directive('autoyaml', AutoYAMLDirective)
    app.add_config_value('autoyaml_root', '..', 'env')
    app.add_config_value('autoyaml_doc_delimiter', '###', 'env')
    app.add_config_value('autoyaml_doc_parameter', '##', 'html')
    app.add_config_value('autoyaml_comment', '#', 'env')