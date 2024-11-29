# Convenience methods for running the tools.
# imports are in the methods to avoid circular imports


def run_connection_editor(pths=None):
    from . import cxn_editor

    cxn_editor.run_editor(pths)


def run_class_designer(pth=None):
    from .class_designer import ClassDesigner

    clsDes = ClassDesigner(pth)
