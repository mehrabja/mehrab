"""Intentionally unsafe fixture for the RepoSentinel demo.

This file exists only so the scanner can demonstrate RS010 and RS011.
Never copy these patterns into application code.
"""

import subprocess


def evaluate_user_expression(user_input: str):
    # RS010: dynamic evaluation of untrusted input.
    return eval(user_input)


def run_user_command(user_command: str) -> None:
    # RS011: shell=True can turn untrusted input into command execution.
    subprocess.run(user_command, shell=True, check=False)
