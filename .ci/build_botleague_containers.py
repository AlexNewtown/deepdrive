import os
import sys
from glob import glob
from os.path import join

import docker

DIR = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(DIR)

def main():
    # Get password from botleague_helpers
    # Add GOOGLE_APPLICATION_CREDENTIALS=/root/.gcpcreds/VoyageProject-d33af8724280.json to problem-worker "deepdrive-build" type
    # Add docker creds to environment via the worker (see the sim build for how)

    bot_dirs = glob(f'{join(ROOT, "botleague")}/bots/*')
    problem_dirs = glob(f'{join(ROOT, "botleague")}/problems/*')

    if 'BUILD_ID' in os.environ:
        os.environ['TAG_BUILD_ID'] = f'_{os.environ["BUILD_ID"]}'
    else:
        os.environ['TAG_BUILD_ID'] = 'local_build'


    for pdir in problem_dirs + bot_dirs:
        exit_code = os.system(f'cd {pdir} && make && make push')
        if exit_code != 0:
            raise RuntimeError('Error building problem container, check above')

    # Get names of docker files, build them


if __name__ == '__main__':
    main()
