#! /usr/bin/env systest

from systest_manager import conf


def script():
    conf.logger.info(conf.handler_configuration)
