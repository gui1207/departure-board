"""
PI-DEPARTURE-BOARD
A Python-based departure board system that displays real-time UK transport information.
"""

__version__ = '2.10.0'
__author__ = 'Jonathan Foot'

from .common import *
from .services import *

__all__ = (
    common.__all__ +
    services.__all__
)