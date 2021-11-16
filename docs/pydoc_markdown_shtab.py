import re

from pydoc_markdown.contrib.processors.pydocmd import PydocmdProcessor


class ShtabProcessor(PydocmdProcessor):
    def _process(self, node):
        if not getattr(node, "docstring", None):
            return super()._process(node)
        # convert parameter lists to markdown list
        node.docstring = re.sub(r"^(\w+)\s{2,}(:.*?)$", r"* __\1__*\2*  ", node.docstring,
                                flags=re.M)
        return super()._process(node)
