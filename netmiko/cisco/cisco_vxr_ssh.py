from __future__ import print_function
from __future__ import unicode_literals

import re
import time
import logging

from netmiko.cisco.cisco_xr import CiscoXrSSH


class CiscoVxrSSH(CiscoXrSSH):
    """
    CiscoVxrSSH is based of CiscoXrSSH -- CiscoBaseConnection
    """

    def find_prompt(self, delay_factor=1):
        """Finds the current network device prompt, last line only.

        """
        pass

    def send_command(self, command_string, expect_string=None,
                     delay_factor=1, max_loops=500, auto_find_prompt=True,
                     strip_prompt=True, strip_command=True, normalize=True,
                     use_textfsm=False):
        """Execute command_string on the SSH channel using a pattern-based mechanism. Generally
         used for show commands. By default this method will keep waiting to receive data until the
         network device prompt is detected. The current network device prompt will be determined
         automatically.
        """
        pass

    def _read_channel(self):
        """Generic handler that will read all the data from an SSH or telnet channel."""
        pass
