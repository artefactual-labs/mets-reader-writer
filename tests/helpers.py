# -*- coding: utf-8 -*-
from lxml import etree


def print_element(element):
    print(etree.tostring(element, pretty_print=True).decode("utf8"))
