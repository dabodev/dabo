"""samplespec.py

A starting example of a python-based report spec file. Dictionaries are used
to specify elements such as the page or the report, bands such as 
PageHeader, PageFooter, GroupHeader, GroupFooter, and Detail, and objects such
as text boxes, rectangles, and lines.

Most values are expressions to be evaluated at runtime (ie they are dynamic).
"""

Page = {"size": ''' "legal" ''',
        "orientation": ''' "landscape" ''',
        "marginLeft": ''' ".5 in" ''',
        "marginRight": ''' ".5 in" ''',
        "marginTop": ''' ".5 in" ''',
        "marginBottom": ''' ".5 in" ''',
}


PageBackground = {"objects": [{"type": "string",
                           "expr": ''' "Test" ''',
                           "align": ''' "left" ''',
                           "rotation": ''' 55 ''',
                           "x": ''' "4.25 in" ''',
                           "y": ''' "5.5 in" ''',
                           "width": ''' "1 in" ''',
                           "fontName": ''' "Helvetica" ''',
                           "fontSize": ''' 20 ''',
                           "fillColor": ''' (.4, .1, .3) ''',
                           "borderWidth": ''' ".5 pt" ''',
                           "borderColor": ''' (.1,.8,.4) ''',
                          },
                          {"type": "rect",
                           "x": ''' "4.25 in" ''',
                           "y": ''' "5 in" ''',
                           "width": ''' "1 in" ''',
                           "height": ''' ".25 in" ''',
                           "rotation": ''' 45 ''',
                           "strokeWidth": ''' ".25 pt" ''',
                           "fillColor": ''' (.5,1,.5) ''',
                           "strokeColor": ''' (.7,.2,.5) ''',
                           "strokeDashArray": ''' (2,5,1,5) '''}
]}


PageHeader = {"height": ''' "0.5 in" ''',
              "objects": [{"type": "string",
                           "expr": ''' "Dabo's Favorite Artists" ''',
                           "align": ''' "center" ''',
                           "x": ''' "3.75 in" ''',
                           "y": ''' "0.3 in" ''',
                           "width": ''' "6 in" ''',
                           "height": ''' ".25 in" ''',
                           "borderWidth": ''' "0 pt" ''',
                           "fontFace": ''' "Helvetica" ''',
                           "fontSize": ''' 14 ''',
                          }]
}

PageFooter = {"height": ''' "1.25 in" ''',
              "objects": [{"type": "image",
                           "expr": ''' "../icons/dabo_lettering_100x40.png" ''',
                           "x": ''' report["bands"]["PageFooter"]["width"]-1 ''',
                           "y": ''' "1" ''',
                           "hAnchor": ''' "right" ''',
                           "width": ''' "50 pt" ''',
                           "height": ''' "20 pt" ''',
                           "mask": ''' None ''',
                          }]
}


Detail = {"height": ''' ".25 in" ''',
          "objects": [{"type": "string",
                       "expr": ''' record['cArtist'] ''',
                       "align": ''' "left" ''',
                       "fontFace": ''' "Helvetica" ''',
                       "fontSize": ''' 12 ''',
                       "borderWidth": ''' ".25 pt" ''',
                       "x": ''' "1 in" ''',
                       "y": ''' "0 pt" ''',
                       "width": ''' "1.4 in" ''',
                       "height": ''' "0.25 in" '''
                       }]
}

Group1Header = {"height": ''' ".5 in" ''',
                "objects": []}

Group1Footer = {"height": ''' "0 in" ''',
                "objects": []}

Groups = [{"name": "Group1",
           "expr": ''' "record['cartist']" ''',}
         ]
