#! /usr/bin/env systest

from systest import conf


def script():
    conf.logger.info(conf.handler_configuration)
