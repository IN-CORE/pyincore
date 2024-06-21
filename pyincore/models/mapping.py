# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


class Mapping:
    """ mapping class that contains the rules and keys of dfr3 curves.

    Args:
        entry (dict): mapping entry.
        rules (list): mapping match rules

    """

    def __init__(self, entry: dict, rules: list):
        self.entry = entry
        self.rules = rules
