"""
Simple Logging Utilities for Streamy
"""
import sys
import logging

#** Variables **#
__all__ = ['basic_logger']

#** Functions **#

def basic_logger(name: str, loglevel: int) -> logging.Logger:
    """
    spawn logging instance w/ the given loglevel

    :param name:     name of the logging instance
    :param loglevel: level of verbosity on logging instance
    :return:         new logging instance
    """
    log = logging.getLogger(name)
    log.setLevel(loglevel)
    # spawn handler
    fmt     = logging.Formatter('[%(process)d] [%(name)s] [%(levelname)s] %(message)s')
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(fmt)
    handler.setLevel(loglevel)
    log.handlers.append(handler)
    return log
