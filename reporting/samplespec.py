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
                   "bottom": .5},
}


PageBackground = {"objects": [{"type": "string",
                           "expression": '''"Test"''',
                           "alignment": "center",
                           "rotation": 30,
                           "x": 4.25,
                           "y": 5.5,
                           "fontFace": "Helvetica",
                           "fontSize": 12,
                          }]}


PageHeader = {"height": 0.5,
              "objects": [{"type": "string",
                           "expression": '''"Dabo's Favorite Artists"''',
                           "alignment": "center",
                           "x": 3.75,
                           "y": 0.3,
                           "width": 6,
                           "height": .25,
                           "borderWidth": 0,
                           "fontFace": "Helvetica",
                           "fontSize": 14,
                          }]
}

PageFooter = {"height": 1.25,
              "objects": [{"type": "image",
                           "expression": '''"../icons/dabo_lettering_100x40.png"''',
                           "x": 6.1,
                           "y": .01,
                           "width": None,
                           "height": None,
                           "mask": None,
                          }]
}


Detail = {"height": .25,
          "objects": [{"type": "string",
                       "expression": "record['cArtist']",
                       "alignment": "left",
                       "fontFace": "Helvetica",
                       "fontSize": 12,
                       "borderWidth": .25,
                       "x": 1,
                       "y": .01,
                       "width": 1.4,
                       "height": 0.25
                       }]
}

Group1Header = {"height": .5,
                "objects": []}

Group1Footer = {"height": 0,
                "objects": []}

Groups = [{"name": "Group1",
           "expression": "record['cartist']",}
         ]
