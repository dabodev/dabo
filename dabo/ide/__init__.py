# Convenience methods for running the tools.
# imports are in the methods to avoid circular imports

def run_connection_editor(filepaths=None):
    from . import cxn_editor
    cxn_editor.run_editor(filepaths)


def run_class_designer(filepath=None):
    from .class_designer import ClassDesigner
    clsDes = ClassDesigner(filepath)
