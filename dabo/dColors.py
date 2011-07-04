# -*- coding: utf-8 -*-
import re
import random

class HexError(Exception): pass
class InvalidCharError(HexError): pass
class TypeError(HexError): pass

class ColorTupleError(Exception): pass
class RgbValueError(ColorTupleError): pass
class LengthError(ColorTupleError): pass
class IntegerTypeError(ColorTupleError): pass

colorDict = {"aliceblue" : (240, 248, 255),
		"antiquewhite" : (250, 235, 215),
		"aqua" : (0, 255, 255),
		"aquamarine" : (127, 255, 212),
		"azure" : (240, 255, 255),
		"beige" : (245, 245, 220),
		"bisque" : (255, 228, 196),
		"black" : (0, 0, 0),
		"blanchedalmond" : (255, 235, 205),
		"blue" : (0, 0, 255),
		"blueviolet" : (138, 43, 226),
		"brown" : (165, 42, 42),
		"burlywood" : (222, 184, 135),
		"cadetblue" : (95, 158, 160),
		"chartreuse" : (127, 255, 0),
		"chocolate" : (210, 105, 30),
		"coral" : (255, 127, 80),
		"cornflowerblue" : (100, 149, 237),
		"cornsilk" : (255, 248, 220),
		"crimson" : (220, 20, 60),
		"cyan" : (0, 255, 255),
		"darkblue" : (0, 0, 139),
		"darkcyan" : (0, 139, 139),
		"darkgoldenrod" : (184, 134, 11),
		"darkgray" : (169, 169, 169),
		"darkgrey" : (169, 169, 169),
		"darkgreen" : (0, 100, 0),
		"darkkhaki" : (189, 183, 107),
		"darkmagenta" : (139, 0, 139),
		"darkolivegreen" : (85, 107, 47),
		"darkorange" : (255, 140, 0),
		"darkorchid" : (153, 50, 204),
		"darkred" : (139, 0, 0),
		"darksalmon" : (233, 150, 122),
		"darkseagreen" : (143, 188, 143),
		"darkslateblue" : (72, 61, 139),
		"darkslategray" : (47, 79, 79),
		"darkslategrey" : (47, 79, 79),
		"darkturquoise" : (0, 206, 209),
		"darkviolet" : (148, 0, 211),
		"deeppink" : (255, 20, 147),
		"deepskyblue" : (0, 191, 255),
		"dimgray" : (105, 105, 105),
		"dimgrey" : (105, 105, 105),
		"dodgerblue" : (30, 144, 255),
		"feldspar" : (209, 146, 117),
		"firebrick" : (178, 34, 34),
		"floralwhite" : (255, 250, 240),
		"forestgreen" : (34, 139, 34),
		"fuchsia" : (255, 0, 255),
		"gainsboro" : (220, 220, 220),
		"ghostwhite" : (248, 248, 255),
		"gold" : (255, 215, 0),
		"goldenrod" : (218, 165, 32),
		"gray" : (128, 128, 128),
		"grey" : (128, 128, 128),
		"green" : (0, 128, 0),
		"greenyellow" : (173, 255, 47),
		"honeydew" : (240, 255, 240),
		"hotpink" : (255, 105, 180),
		"indianred" : (205, 92, 92),
		"indigo" : (75, 0, 130),
		"ivory" : (255, 255, 240),
		"khaki" : (240, 230, 140),
		"lavender" : (230, 230, 250),
		"lavenderblush" : (255, 240, 245),
		"lawngreen" : (124, 252, 0),
		"lemonchiffon" : (255, 250, 205),
		"lightblue" : (173, 216, 230),
		"lightcoral" : (240, 128, 128),
		"lightcyan" : (224, 255, 255),
		"lightgoldenrodyellow" : (250, 250, 210),
		"lightgray" : (211, 211, 211),
		"lightgrey" : (211, 211, 211),
		"lightgreen" : (144, 238, 144),
		"lightpink" : (255, 182, 193),
		"lightsalmon" : (255, 160, 122),
		"lightseagreen" : (32, 178, 170),
		"lightskyblue" : (135, 206, 250),
		"lightslateblue" : (132, 112, 255),
		"lightslategray" : (119, 136, 153),
		"lightslategrey" : (119, 136, 153),
		"lightsteelblue" : (176, 196, 222),
		"lightyellow" : (255, 255, 224),
		"lime" : (0, 255, 0),
		"limegreen" : (50, 205, 50),
		"linen" : (250, 240, 230),
		"magenta" : (255, 0, 255),
		"maroon" : (128, 0, 0),
		"mediumaquamarine" : (102, 205, 170),
		"mediumblue" : (0, 0, 205),
		"mediumorchid" : (186, 85, 211),
		"mediumpurple" : (147, 112, 216),
		"mediumseagreen" : (60, 179, 113),
		"mediumslateblue" : (123, 104, 238),
		"mediumspringgreen" : (0, 250, 154),
		"mediumturquoise" : (72, 209, 204),
		"mediumvioletred" : (199, 21, 133),
		"midnightblue" : (25, 25, 112),
		"mintcream" : (245, 255, 250),
		"mistyrose" : (255, 228, 225),
		"moccasin" : (255, 228, 181),
		"navajowhite" : (255, 222, 173),
		"navy" : (0, 0, 128),
		"oldlace" : (253, 245, 230),
		"olive" : (128, 128, 0),
		"olivedrab" : (107, 142, 35),
		"orange" : (255, 165, 0),
		"orangered" : (255, 69, 0),
		"orchid" : (218, 112, 214),
		"palegoldenrod" : (238, 232, 170),
		"palegreen" : (152, 251, 152),
		"paleturquoise" : (175, 238, 238),
		"palevioletred" : (216, 112, 147),
		"papayawhip" : (255, 239, 213),
		"peachpuff" : (255, 218, 185),
		"peru" : (205, 133, 63),
		"pink" : (255, 192, 203),
		"plum" : (221, 160, 221),
		"powderblue" : (176, 224, 230),
		"purple" : (128, 0, 128),
		"red" : (255, 0, 0),
		"rosybrown" : (188, 143, 143),
		"royalblue" : (65, 105, 225),
		"saddlebrown" : (139, 69, 19),
		"salmon" : (250, 128, 114),
		"sandybrown" : (244, 164, 96),
		"seagreen" : (46, 139, 87),
		"seashell" : (255, 245, 238),
		"sienna" : (160, 82, 45),
		"silver" : (192, 192, 192),
		"skyblue" : (135, 206, 235),
		"slateblue" : (106, 90, 205),
		"slategray" : (112, 128, 144),
		"slategrey" : (112, 128, 144),
		"snow" : (255, 250, 250),
		"springgreen" : (0, 255, 127),
		"steelblue" : (70, 130, 180),
		"tan" : (210, 180, 140),
		"teal" : (0, 128, 128),
		"thistle" : (216, 191, 216),
		"tomato" : (255, 99, 71),
		"turquoise" : (64, 224, 208),
		"violet" : (238, 130, 238),
		"violetred" : (208, 32, 144),
		"wheat" : (245, 222, 179),
		"white" : (255, 255, 255),
		"whitesmoke" : (245, 245, 245),
		"yellow" : (255, 255, 0),
		"yellowgreen" : (154, 205, 50)
		}

colors = colorDict.keys()
colors.sort()


def hexToDec(hx):
	if not isinstance(hx, basestring):
		raise TypeError("Input must be a string")
	# Define a dict of char-value pairs
	hex = {"0": 0, "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8,
			"9": 9, "A": 10, "B": 11, "C": 12, "D": 13, "E": 14, "F": 15}
	# Reverse it, and force upper case
	rev = hx[::-1].upper()
	ret = 0
	pos = 1
	for c in rev:
		if hex.get(c) == None:
			raise InvalidCharError("%s is an invalid hex character" % (c, ))
		ret += (hex[c] * pos)
		pos = pos * 16
	return ret


def tupleToHex(t, includeHash=True):
	"""Convert a color tuple into an HTML hex format."""
	if not len(t) == 3:
		raise LengthError("Color tuple needs to contain 3 elements")
	for rgb in t:
		if not isinstance(rgb, int):
			raise IntegerTypeError("Tuple elements should be all integers.")
		if not 0 <= rgb <= 255:
			raise RgbValueError("Rgb Value must be in the range 0-255")
	rx, gx, bx = hex(t[0]), hex(t[1]), hex(t[2])
	# Each is in the format '0x00'.
	r = rx[2:].upper()
	g = gx[2:].upper()
	b= bx[2:].upper()
	if len(r) == 1: r = '0' + r
	if len(g) == 1: g = '0' + g
	if len(b) == 1: b = '0' + b
	ret = ""
	if includeHash:
		ret = "#"
	ret += r + g + b
	return ret


def colorTupleFromHex(hx):
	# Strip the pound sign, if any
	hx = hx.replace("#", "")
	hx = hx.lstrip('0')
	if len(hx) < 6: hx = '0'*(6-len(hx)) + hx
	red = hexToDec(hx[:2])
	green = hexToDec(hx[2:4])
	blue = hexToDec(hx[4:])
	return (red, green, blue)


def colorTupleFromName(color):
	"""Given a color name, such as "Blue" or "Aquamarine", return a color tuple.

	This is used internally in the ForeColor and BackColor property setters. The
	color name is not case-sensitive. If the color name doesn't exist, an exception
	is raised.
	"""
	ret = None
	try:
		ret = colorDict[color.lower().strip()]
	except KeyError:
		try:
			ret = colorTupleFromHex(color)
		except InvalidCharError:
			ret = colorTupleFromString(color)
	return ret


def colorTupleFromString(color):
	ret = None
	colorTuplePat = "\((\d+), *(\d+), *(\d+)\)"
	mtch = re.match(colorTuplePat, color)
	if mtch:
		grps = mtch.groups()
		ret = (int(grps[0]), int(grps[1]), int(grps[2]))
		for val in ret:
			if not 0 <= val <= 255:
				raise KeyError("Color tuple integer must range from 0-255")
	else:
		raise KeyError("Color '%s' is not defined." % color)
	return ret


def randomColor():
	"""Returns a random color tuple"""
	return colorDict[random.choice(colorDict.keys())]


def randomColorName():
	"""Returns a random color name"""
	return random.choice(colorDict.keys())


def colorNameFromTuple(colorTuple, firstOnly=False):
	"""Returns a list of color names, if any, whose RGB tuple matches
	the specified tuple. If 'firstOnly' is True, then a single color name
	will be returned as a string, not a list; the string will be empty
	if there is no match.
	"""
	ret = [nm for nm, tup in colorDict.items()
			if tup == colorTuple]
	if firstOnly:
		try:
			ret = ret[0]
		except IndexError:
			ret = ""
	return ret
