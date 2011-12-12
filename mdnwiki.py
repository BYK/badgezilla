'''
@author: BYK
'''

import operator
import re
import urllib
import xml.dom.minidom as minidom


class ActionBase(type):
    def __new__(cls, name, bases, attrs):
        new_class = super(ActionBase, cls).__new__(cls, name, bases, attrs)
        if name != "Action":
            Action.register(new_class)
        return new_class


class Action(object):
    __types = set()
    __metaclass__ = ActionBase
    
    
    @classmethod
    def register(cls, new_class):
        if issubclass(new_class, cls):
            cls.__types.add(new_class)
        else:
            raise ValueError
    
    @classmethod
    def create(cls, url, user, action_log):
        parse_list = action_log.rpartition(';')
        action_str = parse_list[-1]
        comment = parse_list[0]
        details = [url, user, comment]
        
        new_action = None
        for action_type in cls.__types:
            new_action = action_type.create(action_str, *details)
            if new_action:
                break
        
        return new_action
    
    def __init__(self, url, user, comments):
        self.url = url
        self.user = user
        self.comments = comments


class TagAction(Action):
    @classmethod
    def create(cls, s, *details):
        match = re.match(r"(?P<verb>Added|Removed) tags: (?P<tag>\w+)\.", s)
        if match:
            return cls(*details, **match.groupdict())
        else:
            return None

    def __init__(self, *stock, **additional):
        super(self.__class__, self).__init__(*stock)
        self.tag = additional.pop('tag')
        sign = additional.pop('verb')
        self.sign = 1 if sign == "Added" else -1


class EditAction(Action):
    @classmethod
    def create(cls, s, *details):
        matches = re.findall(r"(?P<added>\d+) words (?P<action>added|removed)", s)
        if matches:
            params = dict(map(reversed, matches))
            return cls(*details, **params)
        else:
            return None

    def __init__(self, *stock, **additional):
        super(self.__class__, self).__init__(*stock)
        self.words_added = additional.pop('added', 0)
        self.words_removed = additional.pop('removed', 0)


class FormatAction(Action):
    @classmethod
    def create(cls, s, *details):
        match = re.match(r"one or more formatting changes", s)
        if match:
            return cls(*details)
        else:
            return None

    def __init__(self, *stock):
        super(self.__class__, self).__init__(*stock)


class User(object):
    _urlpattern = "https://developer.mozilla.org/index.php?"
                  "title=Special:Contributions&feed=rss&target=%s"
    __action_count_matcher = re.compile(r"^Edited (\d+(?= times)|once|twice)")
    def __init__(self, user):
        '''
        Constructor
        '''
        self.__user = user
        self.__dom = minidom.parse(urllib.urlopen(
            self._urlpattern % urllib.quote_plus(user)))
        self.__action_groups = self.__dom.getElementsByTagName("entry")
        self.__actions = None

    @classmethod
    def __action_extractor(cls, activity):
        summary = activity.getElementsByTagName("summary")[0].\
                           getElementsByTagName("div")[0]
        p_elems = summary.getElementsByTagName("p")
        summary_text = p_elems[0].firstChild.data
        url = activity.getElementsByTagName("id")[0].firstChild.data
        user = activity.getElementsByTagName("author")[0].\
               getElementsByTagName("name")[0].firstChild.data
        
        edit_count = cls.__action_count_matcher.match(summary_text).group(1)
        edit_count = 1 if edit_count == "once" else \
            2 if edit_count == "twice" else int(edit_count)
        if edit_count == 1:
            return [(url, user, p_elems[1].firstChild.data)]
        else:
            return [(url, user, elm.firstChild.data) for elm in
                       summary.getElementsByTagName("ol")[0].\
                       getElementsByTagName("li")]

    @property
    def actions(self):
        if not self.__actions:
            actions = reduce(operator.add,
                             map(self.__action_extractor, self.__action_groups))
            self.__actions = [Action.create(*x) for x in actions]
        return self.__actions


class Achievement(object):
    pass

