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

    def send_command_expect(self, *args, **kwargs):
        """Support previous name of send_command method.

        """
        pass

    def send_command_timing(self, command_string, delay_factor=1, max_loops=150,
                            strip_prompt=True, strip_command=True, normalize=True,
                            use_textfsm=False):
        """Execute command_string on the SSH channel using a delay-based mechanism. Generally
        used for show commands.
        """
        pass

    def send_config_set(self, config_commands=None, exit_config_mode=True, delay_factor=1,
                        max_loops=150, strip_prompt=False, strip_command=False,
                        config_mode_command=None):
        """
        Send configuration commands down the SSH channel.

        config_commands is an iterable containing all of the configuration commands.
        The commands will be executed one after the other.

        Automatically exits/enters configuration mode.
        """
        pass

    def _read_channel(self):
        """Generic handler that will read all the data from an SSH or telnet channel."""
        pass

    def _read_channel_timing(self, delay_factor=1, max_loops=150):
        """Read data on the channel based on timing delays.

        Attempt to read channel max_loops number of times. If no data this will cause a 15 second
        delay.

        Once data is encountered read channel for another two seconds (2 * delay_factor) to make
        sure reading of channel is complete.
        """
        pass

    def _read_channel_expect(self, pattern='', re_flags=0, max_loops=150):
        """Function that reads channel until pattern is detected.

        pattern takes a regular expression.

        By default pattern will be self.base_prompt

        Note: this currently reads beyond pattern. In the case of SSH it reads MAX_BUFFER.
        In the case of telnet it reads all non-blocking data.

        There are dependencies here like determining whether in config_mode that are actually
        depending on reading beyond pattern.

        """
        pass
