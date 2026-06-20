import re
import sys
from agency.install import _DISPATCH_HOOK_SCRIPT

def test_hint_function_outputs_to_stderr(capsys):
    # Extract the hint function code from the bash script.
    # We look for the exact definition in the python block.
    match = re.search(r'def hint\(msg\):.*?print\([^)]+\)', _DISPATCH_HOOK_SCRIPT, re.DOTALL)
    assert match is not None, "hint function not found in _DISPATCH_HOOK_SCRIPT"

    hint_code = match.group(0)

    # Create an environment for exec
    env = {'sys': sys}

    # Execute the hint function definition
    exec(hint_code, env)

    # The function is now in the environment, call it
    hint_fn = env['hint']
    hint_fn("this is a test hint message")

    # Capture the output
    captured = capsys.readouterr()

    # The hint function should print to stderr with the prefix "agency hook | "
    assert captured.out == ""
    assert "agency hook | this is a test hint message\n" in captured.err
