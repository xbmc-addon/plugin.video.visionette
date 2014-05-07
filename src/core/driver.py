# -*- coding: utf-8 -*-


"""
Возможные значения data в драйверах:
title (обязательно), label, info, property, icon, cover, fanart, color1, color2, color3
"""

from drivers import finamfm
from drivers import rbc
from drivers import rain


DRIVERS = {
    1: finamfm,
    2: rbc,
    3: rain
}
