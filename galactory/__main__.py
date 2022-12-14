# -*- coding: utf-8 -*-
# (c) 2022 Brian Scholer (@briantist)

from . import create_configured_app

if __name__ == '__main__':
    create_configured_app(run=True, parse_known_only=False, parse_allow_abbrev=True)
