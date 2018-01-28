import argparse
import os
import tempfile
from subprocess import Popen, PIPE
import sys
import platform
from distutils.spawn import find_executable


DIR = os.path.dirname(os.path.realpath(__file__))

IS_LINUX = sys.platform == 'linux' or sys.platform == 'linux2'
IS_MAC = sys.platform == 'darwin'
IS_UNIX = IS_LINUX or IS_MAC or 'bsd' in sys.platform.lower()
IS_WINDOWS = sys.platform == 'win32'


def run_command(cmd, cwd=None, env=None, throw=True, verbose=False, print_errors=True):
    def say(*args):
        if verbose:
            print(*args)
    say(cmd)
    if not isinstance(cmd, list):
        cmd = cmd.split()
    process = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, cwd=cwd, env=env)
    result, err = process.communicate()
    if not isinstance(result, str):
        result = ''.join(map(chr, result))
    result = result.strip()
    say(result)
    if process.returncode != 0:
        if not isinstance(err, str):
            err = ''.join(map(chr, err))
        err_msg = ' '.join(cmd) + ' finished with error ' + err.strip()
        if throw:
            raise RuntimeError(err_msg)
        elif print_errors:
            print(err_msg)
    return result, process.returncode


def main():
    print('Checking python version')
    py, _ = run_command('python -u bin/install/check_py_version.py')
    print('Checking if Tensorflow is already installed')
    tf_valid_outside = get_tf_valid(py, verbose=False)  # Could still be in existing pipenv...
    print('Installing pipenv')
    if 'ubuntu' in platform.platform().lower():
        # Install tk for dashboard
        run_command('sudo apt-get install -y python3-tk', throw=False, verbose=True)
    if not find_executable('pipenv'):
        install_pipenv = '%s -m pip install pipenv' % py
        if IS_LINUX:
            run_command('sudo ' + install_pipenv, verbose=True)
        else:
            run_command(install_pipenv)
    os.system('pipenv install')
    tf_valid_inside = get_tf_valid(py='pipenv run python')
    if tf_valid_outside and not tf_valid_inside:
        print('Installing Tensorflow to your virtualenv')
        os.system('pipenv run pip install tensorflow-gpu')
    tf_valid = get_tf_valid(py='pipenv run python', verbose=True, print_errors=True)  # Confirm
    if tf_valid:
        print('Starting baseline agent')
        os.system('pipenv run python main.py --baseline')
    else:
        print('Starting sim in path follower mode')
        os.system('pipenv run python main.py --let-game-drive')


def get_tf_valid(py, verbose=False, print_errors=False):
    _, exit_code = run_command('%s -u bin/install/check_tf_version.py' % py, throw=False, verbose=verbose,
                               print_errors=print_errors)
    tf_valid = exit_code == 0
    return tf_valid


if __name__ == '__main__':
    main()


# Run the tutorial.sh
# Mute with u
# Escape to see menu / controls
# Change cam with 1, 2, 3
# Alt-tab to get back to agent.py
# Change the throttle out in agent.py

# Pause the game, ask them to press j
# Pause the game, ask them to change the camera position
# Pause the game, ask them to change the steering coeff

# To rerun this tutorial, run tutorial.sh
