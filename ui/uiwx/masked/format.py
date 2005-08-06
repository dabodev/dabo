import re, string, copy, itertools, datetime
import wx.lib.masked as masked
from wx.lib.masked import controlTypes
import wx

_xchars =  string.letters+string.punctuation+string.digits
_abrmonths = [datetime.date(2000, m, 01).strftime("%b") for m in
              [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]]

def _isX(c): c in _xchars
def _isPunctuation(c): c in string.punctuation
def _isAnsi(c): c in masked.ansichars

class _TokMatch(object):
    __tests = {
        '#': str.isdigit,
        'N': str.isalnum,
        'A': str.isupper,
        'a': str.islower,
        'C': str.isalpha,
        'X': _isX,
        '&': _isPunctuation,
        '*': _isAnsi,
        }

    def __init__(self, v):
        self.__test = _TokMatch.__tests[v]
    def __call__(self, i, o):
        return self.__test(i[0]) and (i[1:], o+i[0])

class _TokQmatch(object):
    def __init__(self, v):
        self.__qval = v
    def __call__(self, i, o):
        return i[0] == self.__qval and (i[1:], o+i[0]) or (i, o+self.__qval)

def _tok_repeat(subnode, strCnt):
    cnt = int(strCnt)
    return subnode*cnt

_grammar_ = map(lambda e: (re.compile(e[0]), e[1]),
                [('#', _TokMatch),
                 ('N', _TokMatch),
                 ('A', _TokMatch),
                 ('a', _TokMatch),
                 ('C', _TokMatch),
                 ('X', _TokMatch),
                 ('&', _TokMatch),
                 (r'\*'       , _TokMatch ),
                 (r'\\(.)'    , _TokQmatch),
                 (r'\{(\d+)\}', _tok_repeat),
                 (r'([^#NAaCX&*{}])', _TokQmatch),
                 ])

_time_mask_ = r'(##):(##)(:(##))?( (AM|PM))?'
_date_masks_ = tuple(reduce(lambda l1, l2: l1 + l2,
                            [[re.escape(delim).join(parts) for delim in '-/.']
                             for parts in (('(##)','(##)', '(####)'),
                                           ('(####)', '(##)','(##)'),
                                           ('(##)','(##)', '(####)'),
                                           ('(CCC)','(##)', '(####)'),
                                           ('(####)', '(CCC)','(##)'),
                                           ('(##)','(##)', '(##)'),
                                           )]
                            ))
_datetime_masks_ = map(lambda e: e + " " + _time_mask_, _date_masks_)

_datetime_parts_ = {
    ('Y', '##'):   '%y',
    ('Y', '####'): '%Y',
    ('M', '##'):   '%m',
    ('M', 'CCC'):  '%b',
    ('D', '##'):   '%d',
    }

_datetime_format_regexps_ = \
                          [('%y', r'(?P<year>\d{2})'),
                           ('%Y', r'(?P<year>\d{4})'),
                           ('%m', r'(?P<month>\d{2})'),
                           ('%b', r'(?P<month>[\wA-Za-z]{3})'),
                           ('%d', r'(?P<day>\d{2})'),
                           ('%I', r'(?P<hour>\d{2})'),
                           ('%H', r'(?P<hour>\d{2})'),
                           ('%M', r'(?P<minute>\d{2})'),
                           ('%S', r'(?P<second>\d{2})'),
                           ('%p', r'(?P<p>AM|PM)')
                           ]
 
def _num_mask_parse(val):
    if isinstance(val,  str):
        intp, fractp = val, ""
    else:
        intp, fractp = val
    return (len(intp), len(fractp))

def _time_mask_parse(val):
    # ('##', '##', _, '##', _, CC)
    h, m, s, p = val[0], val[1], val[3], val[5]
    hFmt = p and '%I' or '%H'
    
    outFmt = hFmt + ':%M'
    outFmt += s and ':%S' or ''
    outFmt += p and ' %p' or ''
    return outFmt

def _date_mask_parse(val, mask, dateStyle):
    sep = (('/' in mask) * '/') + (('-' in mask) * '-') + (('.' in mask) * '.')
    outFmt = sep.join([_datetime_parts_[(v, val[dateStyle.index(v)])] for v in dateStyle])
    return outFmt

def _datetime_mask_parse(val, mask, dateStyle):
    dateFmt = _date_mask_parse(val[:3], mask, dateStyle)
    timeFmt = _time_mask_parse(val[3:])
    return dateFmt + " " + timeFmt

_datetime_rules_ = \
                 map(lambda e: (re.compile(e[0]), e[1]),
                     map(lambda e: (e, _datetime_mask_parse),
                         _datetime_masks_) + \
                     map(lambda e: (e, _date_mask_parse),
                         _date_masks_) + \
                     [(_time_mask_, _time_mask_parse)])
_num_rules = \
      map(lambda e: (re.compile(e[0]), e[1]),     
          [(r'([#]+)\.([#]+)', _num_mask_parse),
           (r'[#]+', _num_mask_parse),])

def _match_rule(rule, text):
    regexp, tag = rule
    res = regexp.match(text)
    if res:
        groups = res.groups()
        if not groups:
            val = res.group(0)
        elif len(groups) == 1:
            val, = groups
        else:
            val = groups
        rest_text = text[res.end():]
        return (tag, val), rest_text
    else:
        return False

def _map_rules(rules, text):
    for rule in rules:
        res = _match_rule(rule, text)
        if res: return res
    return False

def _tokenizer(rules, text):
    rest_text = text
    while rest_text:
        res = _map_rules(rules, rest_text)
        if res:
            val, rest_text = res
            yield val
        else: raise ValueError, 'Invalid mask format'
    return

def kwval(key, kwargs):
    return kwargs.has_key(key) and kwargs[key]

def Ctrl(controlType=controlTypes.TEXT, **kwargs):
    return {
        controlTypes.NUMBER: NumFormat,
        controlTypes.TEXT: TextFormat,
        controlTypes.TIME: TimeFormat,
        controlTypes.COMBO: TextFormat,
        }[controlType](**kwargs)

def _add_properties(param_names):
    ret = []
    for param in param_names:
        propname = param[0].upper() + param[1:]
        getter_name = '_get%s' % propname
        setter_name = '_set%s' % propname
        getter = 'def %s(self): return self._%s' % (getter_name, param)
        setter = 'def %s(self, val): self.SetParameters(%s=val)' % (setter_name, param)
        prop = '%s = property(%s, %s, None,"Generated.")' % (propname, getter_name, setter_name)
        ret.extend([getter, setter, prop])
    return tuple(ret)


class TextFormat(object):
    valid_params = {
        'name':         "text",
        'formatcodes':  "",
        'groupChar':    ',',
        'decimalChar':  '.',
        'autoformat':   "",
        'mask':         'XXXXXXXXXXXXX',
        'datestyle':    'MDY',
        'useParensForNegatives': False
        }

    for d in  _add_properties(valid_params): exec(d)
    
    def __init__(self, **kwargs):
        self._mytype = None
        self._format = None
        self._scaner = None
        for key, value in TextFormat.valid_params.items():
           setattr(self, '_' + key, copy.copy(value))
        self.SetParameters(**kwargs)

    def format(self, val):
        fmt = {
            'string': self._mask_format,
            'date':   self._time_format,
            'time':   self._time_format,
            'int':    self._num_format,
            'float':  self._num_format,
            }[self._mytype]
        return fmt(val)

    def fromstr(self, strv, dataType=str):
        try:
            if dataType == str or dataType == unicode: return strv
        
            v =  self._scaner(self, strv)
            if v is None: return v

            if self._mytype in ('date', 'time'):
                if dataType == datetime.datetime:
                    return datetime.datetime(*v)
                elif dataType == datetime.date:
                    return datetime.date(*v[0:3])
                elif str(dataType) == "<type 'DateTime'>":
                    try:
                        import mx.DateTime
                        return mx.DateTime.DateTime(*v)
                    except ImportError:
                        return None
            elif dataType == bool:
                return v == 'True' or False
            else:
                return dataType(strv)
        except (ValueError, TypeError):
            return None
            
    def SetParameters(self, **kwargs):
        if kwargs.has_key('autoformat'):
            autoformat = kwargs['autoformat']
            try:
                kws = masked.maskededit.masktags[autoformat]
                for key, value in kws.items():
                    kwargs[key] = value
            except KeyError:
                raise(AttributeError,
                      'invalid autoformat value %s' % repr(autoformat))

        for key in TextFormat.valid_params.keys():
            if kwargs.has_key(key):
                setattr(self, '_' + key, kwargs[key])

        self._groupdigits = ',' in self._formatcodes
        self._padZero = '0' in self._formatcodes
        self._guess_type()
        self._choose_scanner()
        if self._mytype in ('date', 'time'):
             # autoformat masks could get 'AM' at the end
             self._mask = self._mask.replace('AM', 'CC')
        self._cmask = self._parse(self._mask)

        return

    def _guess_type(self):
        self._format = None
        self._mytype = 'string'
        # try date/time
        is_date = 'D' in self._formatcodes and 'date'
        is_time = 'T' in self._formatcodes and 'time'
        if is_date or is_time:
            self._mytype =  is_date or is_time
            for kv in (('MDDY', 'MDY'), ('YMMD', 'YMD'), ('YMMMD', 'YMD'),
                       ('DMMY', 'DMY'), ('DMMMY', 'DMY'),):
                pat, style = kv
                if self._autoformat.find(pat) != -1:
                    self._datestyle = style
                    break

        type_rules = (is_date or is_time) and _datetime_rules_ \
                     or _num_rules
        res = _map_rules(type_rules, self._mask.strip())

        if not res: self._mytype = 'string'; return
        rule_res, rest_text = res
        if rest_text: self._mytype = 'string'; return
        tag, tag_val = rule_res

        if tag == _num_mask_parse:
            self._integerWidth, self._fractionWidth = tag(tag_val)
            self._mytype = self._fractionWidth and 'float' or 'int'
            fmtInt = self._padZero and '%%0%dd' % self._integerWidth or '%d'
            fmtFrac = self._fractionWidth and self._decimalChar + '%d' or None
            self._format = (fmtInt, fmtFrac) 
        elif tag in (_date_mask_parse, _datetime_mask_parse):
            self._format = tag(tag_val, self._mask, self._datestyle)
            self._mytype = 'date'
        elif tag == _time_mask_parse:
            self._format = tag(tag_val)
            self._mytype = 'time'
        else:
            self._format = None
            self._mytype = 'string'

        return

    def _choose_scanner(self):
        if self._mytype in ('date', 'time'):
            format = self._format
            for pat, reg in _datetime_format_regexps_:
                format = format.replace(pat, reg)
            def scan(self, v):
                m = re.match(format, v)
                if m is None:
                    return None
                else:
                    gd = m.groupdict()
                    year, day, hour, minute, second = \
                          [int(gd.get(k, v)) for (k, v) in
                           [('year', '1970'), ('day', '1'),
                            ('hour', '0'), ('minute', '0'), ('second', '0')]]
                    [sp, smonth] = [gd.get(k, v) for (k,v) in
                                    [('p',''), ('month', '1')]]
                    p = sp == 'PM' and 12 or 0
                    month = len(smonth) == 3 and _abrmonths.index(smonth)+1 \
                            or int(smonth)
                return (year, month, day, hour, minute, second)
        elif self._mytype in ('int', 'float'):
            def scan(self, v):
                sign = v[0] == '(' and -1 or 1
                v = v.replace('(', '').replace(')', '').replace(',', '')
                ret = (self._mytype == 'int' and int(v) or float(v))*sign
                return ret
        else:
            scan = lambda self, v: v

        self._scaner = scan
                    
    def _mask_format(self, text):
        if not isinstance(text, basestring):
            text = text is None and "" or str(text)
        out = ""
        for f in self._cmask:
            if not text: return out
            res = f(text, out)
            if not res: return out+text
            text, out = res
        return out+text

    def _num_format(self, val):
        try:
            if self._mytype == 'int': v = int(val)
            else: v = float(val)
        except:
            try: v = float(val)
            except:
                return self._mask_format(val)
        is_neg = v < 0
        v = abs(v)
        vi, vf = divmod(v, 1)
        vf *= 10**self._fractionWidth
        vf = round(vf, 0)
        fmtInt, fmtFrac = self._format
        intStr = fmtInt % vi
        if fmtFrac:
            fracStr = self._decimalChar + \
                      (vf and '%d' % vf or '0'*self._fractionWidth)
        else:
            fracStr = ''
        if self._groupdigits:
            groups = []; rest = intStr
            while rest:
                groups.append(rest[-3:])
                rest = rest[0:-3]
            groups.reverse()
            intStr = self._groupChar.join(groups)
        retStr = intStr + fracStr
        if is_neg:
            if self._useParensForNegatives:
                retStr = '(' + retStr + ')'
            else:
                retStr = '-'+retStr
        return retStr

    def _time_format(self, val):
        dataType = type(val)
        if dataType == wx.DateTime:
            val.Format(self._format)
        try:
            return val.strftime(self._format)
        except:
            return self._mask_format(val)
    
    def _parse(self, mask):
        # we use one token for look ahead, so add [None] to the end
        tokens = itertools.chain(_tokenizer(_grammar_, mask), [None])
        nodes = []
        def parse_next(cur, next):
            if not cur: return None
            
            cur_type, cur_val = cur
            next_type, next_val = next or (None, None)
            if cur_type == _tok_repeat:
                raise ValueError, 'Invalid mask format'  
            if next_type == _tok_repeat:
                add_nodes = next_type(cur_type(cur_val), next_val)
                next = tokens.next()
            else:
                add_nodes = [cur_type(cur_val)]
            nodes.extend(add_nodes)
            return next
        reduce(parse_next, tokens)
        return nodes

    def _getFormatType(self):
        return self._mytype

    FormatType = property(_getFormatType, None, None,"FormatType.")
    
class TimeFormat(TextFormat):
    valid_params = {
        'format' : 'HHMMSS',
        'displaySeconds' : True,
        }
    valid_time_formats = (
        'HHMMSS', 'TIMEHHMMSS', 'HHMM', 'TIMEHHMM',
        '24HHMMSS', '24HRTIMEHHMMSS', '24HHMM', '24HRTIMEHHMM',
        )
    
    __need24hr = False

    for d in  _add_properties(valid_params): exec(d)

    def __init__(self, name='time', **kwargs):

        if not TimeFormat.__need24hr:
            wxdt = wx.DateTimeFromDMY(1, 0, 1970)
            if wxdt.Format('%p') not in  ('AM', 'PM'):
                TimeFormat.valid_params['format'] = '24HHMMSS'
                TimeFormat.__need24hr = True
            else:
                TimeFormat.__need24hr = False
        for key, value in TimeFormat.valid_params.items():
            setattr(self, "_TimeFormat__" + key, value)
        TextFormat.__init__(self,  name = name, **kwargs)

    def SetParameters(self, **kwargs):
        TextFormat.SetParameters(self, **self._SetParameters(**kwargs))
        
    def _SetParameters(self, format=None, fmt24hr=False, displaySeconds=True,
                       **kwargs):
        if format and format not in valid_time_formats:
            raise AttributeError, 'invalid format %s' % format

        if TimeFormat.__need24hr:
            self.__fmt24hr = TimeFormat.__need24hr
        elif format:
            self.__fmt24hr = format.startswith('24') 
        else:
            self.__fmt24hr = fmt24hr

        if format:
            self.__displaySeconds = format.endswith('SS')
        else:
            self.__displaySeconds = displaySeconds
            
        self.__format = (self.__fmt24hr and '24HR' or '') + \
                        'TIME' + \
                        (self.__displaySeconds and 'HHMMSS' or 'HHMM')

        retargs = {}
        retargs['autoformat'] = self.__format
        retargs['formatcodes'] = 'T'
        return retargs
    
class NumFormat(TextFormat):
    valid_params = {
        'integerWidth': 10,
        'fractionWidth': 0,
        'decimalChar': '.',
        'useParensForNegatives': False,
        'groupDigits': True,
        'groupChar': ',',
        }

    for d in  _add_properties(valid_params): exec(d)

    def __init__(self, name='num', **kwargs):
        for key, value in NumFormat.valid_params.items():
           setattr(self, '_' + key, copy.copy(value))
        TextFormat.__init__(self,  name=name, **kwargs)

    def SetParameters(self, **kwargs):
        TextFormat.SetParameters(self, **self._SetParameters(**kwargs))

    def _SetParameters(self, **kwargs):
        for key in NumFormat.valid_params.keys():
            if kwargs.has_key(key):
                setattr(self, '_' + key, kwargs[key])
                
        mask = '#'*self._integerWidth
        if self._fractionWidth:
            mask += '.'+ '#'*self._fractionWidth

        formatcodes = kwval('formatcodes', kwargs) or ""
        if self._groupDigits: formatcodes += ','
            
        retargs = {
            'mask': mask,
            'formatcodes': formatcodes,
            }
        
        for key in  ('decimalChar',  'groupChar', 'useParensForNegatives',):
            if kwargs.has_key(key):
                retargs[key] = kwargs[key]
        return retargs

if __name__ == '__main__':
    import datetime, time
    fm = TimeFormat(fmt24hr=True, displaySeconds=False)
    print fm.format(datetime.datetime(1970, 1, 1).today())
    print fm.format("2337")
    print fm.format(None)
