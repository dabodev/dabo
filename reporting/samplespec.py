"""samplespec.py

A starting example of a python-based report spec file. Dictionaries are used
to specify elements such as the page or the report, bands such as 
PageHeader, PageFooter, GroupHeader, GroupFooter, and Detail, and objects such
as text boxes, rectangles, and lines.
"""

Page = {"unit": "inch",
        "size": "letter",
        "orientation": "portrait",
        "margin": {"left": .5,
                   "right": .5,
                   "top": .5,
                   "bottom": .5}
}


PageHeader = {"height": 0.5,
              "objects": [{"name": "TestRectangle",
                           "type": "rectangle",
                           "lineWidth": 0.25,
                           "geometry": {"x": 1.5,
                                        "y": .5,
                                        "width": .1,
                                        "height": .1},
                          }]
}

PageFooter = {"height": 1.25,
              "objects": [{"name": "TestRectangle1",
                           "type": "rectangle",
                           "lineWidth": 0.25,
                           "geometry": {"x": 4.5,
                                        "y": .25,
                                        "width": 1,
                                        "height": .4},
                          }]
}


Detail = {"height": .75,
              "objects": [{"name": "TestRectangle1",
                           "type": "rectangle",
                           "lineWidth": 0.25,
                           "geometry": {"x": 4.5,
                                        "y": .25,
                                        "width": 5,
                                        "height": .3},
                          }]
}

