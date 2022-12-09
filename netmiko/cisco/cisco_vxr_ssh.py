from __future__ import print_function
from __future__ import unicode_literals

import re
import time
import logging
import os
import paramiko

from netmiko.cisco.cisco_xr import CiscoXrSSH
from netmiko.netmiko_globals import BACKSPACE_CHAR
from netmiko.utilities import get_structured_data

work_dir = os.getenv('CAFYKIT_WORK_DIR')
if work_dir:
    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    paramiko_log_folder = os.path.join(work_dir, 'test_paramiko.log')
    paramiko.util.log_to_file(paramiko_log_folder, level="DEBUG")
    fh = logging.FileHandler(paramiko_log_folder)
    fh.setFormatter(formatter)
    log = logging.getLogger("netmiko")
    log.addHandler(fh)
    log.setLevel(logging.DEBUG)
    log.addHandler(fh)
else:
    from netmiko import log


class CiscoVxrSSH(CiscoXrSSH):
    """
    CiscoVxrSSH is based of CiscoXrSSH -- CiscoBaseConnection
    """

    def __init__(self,
                 **kwargs):
        """Constructor
        """
        # 30 minutes
        self.max_read_timeout = kwargs.get('max_read_timeout', 1800)
        super().__init__(**kwargs)

    def find_prompt(self, delay_factor=1):
        """Finds the current network device prompt, last line only.

        :param delay_factor: See __init__: global_delay_factor
        :type delay_factor: int
        """
        loop_delay = 0.1
        self.clear_buffer()
        self.write_channel(self.RETURN)
        time.sleep(loop_delay)

        prompt = None
        start_time = time.time()
        current_time = time.time()
        while current_time - start_time < self.max_read_timeout and self.is_alive():
            prompt = self.read_channel().strip()
            prompt = prompt.replace("^@", "")
            if prompt:
                log.info("Prompt found. Time Waited: {}".format(current_time - start_time))
                break
            else:
                log.info("Prompt not found. Time Waited: {}".format(current_time - start_time))
                time.sleep(loop_delay)

            current_time = time.time()
        else:
            if not self.is_alive():
                raise IOError("Session went down while finding prompt")
            else:
                raise IOError("Prompt not found after waiting for {} seconds".format(self.max_read_timeout))

        log.info("Prompt Found is: {}.".format(prompt))
        vxr_pattern = "last login"
        if vxr_pattern in prompt.lower():
            time.sleep(loop_delay + 3)
            prompt = self.read_channel()
        autocommand_pattern = "executing autocommand"
        if autocommand_pattern in prompt.lower():
            time.sleep(loop_delay + 5)
            prompt = self.read_channel()
        cxr_pattern = "last switch-over"
        if cxr_pattern in prompt.lower():
            time.sleep(loop_delay + 3)
            prompt = self.read_channel()
        if self.ansi_escape_codes:
            prompt = self.strip_ansi_escape_codes(prompt)

        prompt = self.normalize_linefeeds(prompt)
        prompt = prompt.split(self.RESPONSE_RETURN)[-1]
        prompt = prompt.strip()

        time.sleep(loop_delay)
        self.clear_buffer()
        log.info("Prompt is: {}.".format(prompt))
        return prompt

    def find_prompt2(self, delay_factor=1):
        """Finds the current network device prompt, last line only.

        :param delay_factor: See __init__: global_delay_factor
        :type delay_factor: int
        """
        loop_delay = 0.1
        self.clear_buffer()
        self.write_channel(self.RETURN)
        time.sleep(loop_delay)
        # Initial attempt to get prompt
        prompt = self.read_channel()
        vxr_pattern = "last login"
        if vxr_pattern in prompt.lower():
            time.sleep(loop_delay + 3)
            prompt = self.read_channel()
        autocommand_pattern = "executing autocommand"
        if autocommand_pattern in prompt.lower():
            time.sleep(loop_delay + 5)
            prompt = self.read_channel()
        cxr_pattern = "last switch-over"
        if cxr_pattern in prompt.lower():
            time.sleep(loop_delay + 3)
            prompt = self.read_channel()
        if self.ansi_escape_codes:
            prompt = self.strip_ansi_escape_codes(prompt)

        # Check if the only thing you received was a newline
        prompt = prompt.strip()
        start_time = time.time()
        current_time = time.time()
        while current_time - start_time < self.max_read_timeout and not prompt:
            prompt = self.read_channel().strip()
            if prompt:
                log.info("Prompt found. Time Waited: {}".format(current_time - start_time), 5)
                if self.ansi_escape_codes:
                    prompt = self.strip_ansi_escape_codes(prompt).strip()
            else:
                log.info("Prompt not found. Time Waited: {}".format(current_time - start_time), 5)
                self.write_channel(self.RETURN)
                time.sleep(loop_delay)

            current_time = time.time()

        # If multiple lines in the output take the last line
        prompt = self.normalize_linefeeds(prompt)
        prompt = prompt.split(self.RESPONSE_RETURN)[-1]
        prompt = prompt.strip()
        if not prompt:
            raise ValueError("Unable to find prompt: {}".format(prompt))
        time.sleep(loop_delay)
        self.clear_buffer()
        return prompt

    def send_command(self, command_string, expect_string=None,
                     delay_factor=1, max_loops=500, auto_find_prompt=True,
                     strip_prompt=True, strip_command=True, normalize=True,
                     use_textfsm=False):
        """
        Execute command_string on the SSH channel using a pattern-based mechanism. Generally
        used for show commands. By default this method will keep waiting to receive data until the
        network device prompt is detected. The current network device prompt will be determined
        automatically.

        :param command_string: The command to be executed on the remote device.
        :type command_string: str

        :param expect_string: Regular expression pattern to use for determining end of output.
            If left blank will default to being based on router prompt.
        :type expect_string: str

        :param delay_factor: Multiplying factor used to adjust delays (default: 1).
        :type delay_factor: int

        :param max_loops: max_loops is not used
        :type max_loops: int

        :param strip_prompt: Remove the trailing router prompt from the output (default: True).
        :type strip_prompt: bool

        :param strip_command: Remove the echo of the command from the output (default: True).
        :type strip_command: bool

        :param normalize: Ensure the proper enter is sent at end of command (default: True).
        :type normalize: bool

        :param use_textfsm: Process command output through TextFSM template (default: False).
        :type normalize: bool
        """
        # Time to delay in each read loop
        loop_delay = .2
        delay_factor = 1

        config_large_msg = "This could be a few minutes if your config is large"
        log.info("In send_command, max_read_timeout: {}".format(self.max_read_timeout))

        # Find the current router prompt
        if expect_string is None:
            if auto_find_prompt:
                try:
                    prompt = self.find_prompt(delay_factor=delay_factor)
                except ValueError:
                    raise IOError("Prompt not Found before sending command")
            else:
                prompt = self.base_prompt
            search_pattern = re.escape(prompt.strip())
        else:
            search_pattern = expect_string

        if normalize:
            command_string = self.normalize_cmd(command_string)

        time.sleep(loop_delay)
        self.clear_buffer()
        self.write_channel(command_string)

        output = ''
        start_time = time.time()
        current_time = time.time()
        # Keep reading data until search_pattern is found or session is alive
        while current_time - start_time < self.max_read_timeout and self.is_alive():
            new_data = self.read_channel()
            if new_data:
                if self.ansi_escape_codes:
                    new_data = self.strip_ansi_escape_codes(new_data)
                # Replace Null Characters sent while checking session (alive) status
                new_data = new_data.replace("^@", "")

                output += new_data
                try:
                    lines = output.split(self.RETURN)
                    first_line = lines[0]
                    # First line is the echo line containing the command. In certain situations
                    # it gets repainted and needs filtered
                    if BACKSPACE_CHAR in first_line:
                        pattern = search_pattern + r'.*$'
                        first_line = re.sub(pattern, repl='', string=first_line)
                        lines[0] = first_line
                        output = self.RETURN.join(lines)
                except IndexError:
                    pass
                if re.search(search_pattern, output):
                    break

                if re.search(config_large_msg, output):
                    output = self.send_command(command_string=self.RETURN,
                                               auto_find_prompt=False, strip_prompt=False, strip_command=False, )
                    output += self.read_channel()
                    if re.search(search_pattern, output):
                        break
            else:
                time.sleep(loop_delay)
            log.info("Pattern not found. Time waited: {}".format(current_time - start_time))
            current_time = time.time()

        else:  # nobreak
            if not self.is_alive():
                raise IOError(
                    "Session went down while checking for prompt after sending command.\nSearch pattern: {}".format(search_pattern))
            else:
                if expect_string is None:
                    raise IOError("Prompt not found after sending command and waiting for {} seconds.\nExpected Prompt: {}.\nOutput: {}".format(
                        self.max_read_timeout, search_pattern, output))
                else:
                    raise IOError("Search Pattern not found after sending command and waiting for {} seconds.\nExpected Prompt: {}\nOutput: {}".format(
                        self.max_read_timeout, search_pattern, output))
        if current_time - start_time >= 10:
            log.info("Command took {} seconds".format(current_time - start_time))
        output = self._sanitize_output(output, strip_command=strip_command,
                                       command_string=command_string, strip_prompt=strip_prompt)
        if use_textfsm:
            output = get_structured_data(output, platform=self.device_type,
                                         command=command_string.strip())
        return output

    def send_command_expect(self, command_string, expect_string=None,
                            delay_factor=1, max_loops=500, auto_find_prompt=True,
                            strip_prompt=True, strip_command=True, normalize=True,
                            use_textfsm=False):
        """Support previous name of send_command method.

        :param args: Positional arguments to send to send_command()
        :type args: list

        :param kwargs: Keyword arguments to send to send_command()
        :type kwargs: dict
        """
        # Time to delay in each read loop
        loop_delay = .2
        config_large_msg = "This could be a few minutes if your config is large"
        # Default to making loop time be roughly equivalent to self.timeout (support old max_loops
        # and delay_factor arguments for backwards compatibility).
        delay_factor = self.select_delay_factor(delay_factor)
        if delay_factor == 1 and max_loops == 500:
            # Default arguments are being used; use self.timeout instead
            max_loops = int(self.timeout / loop_delay)
        log.info("In send_command, global_delay:{}, delay_factor:{}, max_loops:{}".format(
            self.global_delay_factor, delay_factor, max_loops))
        # Find the current router prompt
        if expect_string is None:
            if auto_find_prompt:
                try:
                    prompt = self.find_prompt(delay_factor=delay_factor)
                except ValueError:
                    log.info("From send_command: ValueError encountered from find_prompt() is not re-raised")
                    prompt = self.base_prompt
            else:
                prompt = self.base_prompt
            search_pattern = re.escape(prompt.strip())
        else:
            search_pattern = expect_string

        if normalize:
            command_string = self.normalize_cmd(command_string)

        time.sleep(delay_factor * loop_delay)
        self.clear_buffer()
        self.write_channel(command_string)

        i = 1
        output = ''
        # Keep reading data until search_pattern is found or until max_loops is reached.
        while i <= max_loops:
            new_data = self.read_channel()
            if new_data:
                if self.ansi_escape_codes:
                    new_data = self.strip_ansi_escape_codes(new_data)
                output += new_data
                try:
                    lines = output.split(self.RETURN)
                    first_line = lines[0]
                    # First line is the echo line containing the command. In certain situations
                    # it gets repainted and needs filtered
                    if BACKSPACE_CHAR in first_line:
                        pattern = search_pattern + r'.*$'
                        first_line = re.sub(pattern, repl='', string=first_line)
                        lines[0] = first_line
                        output = self.RETURN.join(lines)
                except IndexError:
                    pass
                if re.search(search_pattern, output):
                    break

                if re.search(config_large_msg, output):
                    output = self.send_command(command_string=self.RETURN,
                                               auto_find_prompt=False, strip_prompt=False, strip_command=False,)
                    output += self.read_channel()
                    if re.search(search_pattern, output):
                        break
            else:
                time.sleep(delay_factor * loop_delay)
            i += 1
        else:   # nobreak
            raise IOError("Search pattern never detected in send_command_expect: {},\
                            pattern found was: {}".format(search_pattern, output))

        output = self._sanitize_output(output, strip_command=strip_command,
                                       command_string=command_string, strip_prompt=strip_prompt)
        if use_textfsm:
            output = get_structured_data(output, platform=self.device_type,
                                         command=command_string.strip())
        return output
