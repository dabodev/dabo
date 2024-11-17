from .ClassDesigner import ClassDesigner
from . import CxnEditor


def run_connection_editor(filepaths=None):
    CxnEditor.run_editor(filepaths)


def run_class_designer(filepath=None):
    clsDes = ClassDesigner(filepath)
