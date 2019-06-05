from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

# TODO: Bootstrap future module to enable Python 2 support of install
#  which depends on this file to do below
# from future.builtins import (ascii, bytes, chr, dict, filter, hex, input,
#                              int, map, next, oct, open, pow, range, round,
#                              str, super, zip)

import random
import os
import sys
from glob import glob

from config.directories import *

import numpy as np

try:
    from gym.utils import seeding
    # Seeded random number generator for reproducibility
    RNG_SEED = 0
    rng = seeding.np_random(RNG_SEED)[0]
except Exception as e:
    import __main__
    if getattr(__main__, '__file__', None) != 'install.py':
        raise e
    else:
        print('Skipping rng seed - not needed for install')


import config.version

# General
CONTROL_NAMES = ['spin', 'direction', 'speed', 'speed_change', 'steering',
                 'throttle']

# Net
NUM_TARGETS = len(CONTROL_NAMES)

# Normalization
SPIN_THRESHOLD = 1.0
SPEED_NORMALIZATION_FACTOR = 2000.
SPIN_NORMALIZATION_FACTOR = 10.
MEAN_PIXEL = np.array([104., 117., 123.], np.float32)

# HDF5
FRAMES_PER_HDF5_FILE = int(os.environ.get('FRAMES_PER_HDF5_FILE', 1000))
NUM_TRAIN_FRAMES_TO_QUEUE = 6000
NUM_TRAIN_FILES_TO_QUEUE = NUM_TRAIN_FRAMES_TO_QUEUE // FRAMES_PER_HDF5_FILE
HDF5_DIR_ZFILL = 7
HDF5_FRAME_ZFILL = 10

# OS 
IS_LINUX = sys.platform == 'linux' or sys.platform == 'linux2'
IS_MAC = sys.platform == 'darwin'
IS_UNIX = IS_LINUX or IS_MAC or 'bsd' in sys.platform.lower()
IS_WINDOWS = sys.platform == 'win32'
if IS_WINDOWS:
    OS_NAME = 'windows'
elif IS_LINUX:
    OS_NAME = 'linux'
else:
    raise RuntimeError('Unexpected OS')

# AGENTS
DAGGER = 'dagger'
DAGGER_MNET2 = 'dagger_mobilenet_v2'
BOOTSTRAPPED_PPO2 = 'bootstrapped_ppo2'


# Weights
ALEXNET_BASELINE_WEIGHTS_DIR = os.path.join(WEIGHTS_DIR,
                                            'baseline_agent_weights')
ALEXNET_BASELINE_WEIGHTS_VERSION = 'model.ckpt-143361'
ALEXNET_PRETRAINED_NAME = 'bvlc_alexnet.ckpt'
ALEXNET_PRETRAINED_PATH = os.path.join(WEIGHTS_DIR, ALEXNET_PRETRAINED_NAME)

MNET2_BASELINE_WEIGHTS_DIR = os.path.join(WEIGHTS_DIR, 'mnet2_baseline_weights')
MNET2_BASELINE_WEIGHTS_VERSION = 'model.ckpt-49147'
MNET2_PRETRAINED_NAME = 'mobilenet_v2_1.0_224_checkpoint'
MNET2_PRETRAINED_PATH = os.path.join(WEIGHTS_DIR, MNET2_PRETRAINED_NAME,
                                     'mobilenet_v2_1.0_224.ckpt')

PPO_BASELINE_WEIGHTS_DIR = os.path.join(WEIGHTS_DIR,
                                        'ppo_baseline_agent_weights')
PPO_BASELINE_WEIGHTS_VERSION = '03125'

# Urls
AWS_BUCKET = 'deepdrive'
BUCKET_URL = 'https://s3-us-west-1.amazonaws.com/' + AWS_BUCKET
BASE_WEIGHTS_URL = BUCKET_URL + '/weights'
ALEXNET_BASELINE_WEIGHTS_URL = BASE_WEIGHTS_URL + '/baseline_agent_weights.zip'
ALEXNET_PRETRAINED_URL = '%s/%s.zip' % (BASE_WEIGHTS_URL, ALEXNET_PRETRAINED_NAME)
MNET2_PRETRAINED_URL = '%s/%s.zip' % (BASE_WEIGHTS_URL, MNET2_PRETRAINED_NAME)
MNET2_BASELINE_WEIGHTS_URL = BASE_WEIGHTS_URL + '/mnet2_baseline_weights.zip'
PPO_BASELINE_WEIGHTS_URL = BASE_WEIGHTS_URL + '/ppo_baseline_agent_weights.zip'
SIM_PREFIX = 'deepdrive-sim-' + OS_NAME
YOU_GET_MY_JIST_URL = BUCKET_URL + '/yougetmyjist.json'


# Sim
if 'DEEPDRIVE_SIM_START_COMMAND' in os.environ:
    # Can do something like
    # `<your-unreal-path>\Engine\Binaries\Win32\UE4Editor.exe <your-deepdrive-sim-path>\DeepDrive.uproject -game ResX=640 ResY=480`
    SIM_START_COMMAND = os.environ['DEEPDRIVE_SIM_START_COMMAND']
else:
    SIM_START_COMMAND = None


REUSE_OPEN_SIM = 'DEEPDRIVE_REUSE_OPEN_SIM' in os.environ

DEFAULT_CAM = dict(
    name='forward cam 227x227 60 FOV',
    field_of_view=60,
    capture_width=227,
    capture_height=227,
    relative_position=[150, 1.0, 200],
    relative_rotation=[0.0, 0.0, 0.0])

DEFAULT_FPS = 8
DEFAULT_SIM_STEP_TIME = 1 / (2 * DEFAULT_FPS)

try:
    import tensorflow
except ImportError:
    TENSORFLOW_AVAILABLE = False
else:
    TENSORFLOW_AVAILABLE = True


# Not passing through main.py args yet, but better for reproducing to put here than in os.environ
SIMPLE_PPO = False
# PPO_RESUME_PATH = '/home/a/baselines_results/openai-2018-06-17-17-48-24-795338/checkpoints/03125'
# PPO_RESUME_PATH = '/home/a/baselines_results/openai-2018-06-22-00-00-21-866205/checkpoints/03125'
PPO_RESUME_PATH = None
# TEST_PPO = False


# API
API_PORT = 5557
API_TIMEOUT_MS = 5000

# Stream
STREAM_PORT = 5558

# Set via main
MAIN_ARGS:dict = {}

# Upload results to github
SESS_RESULTS_CSV_FILENAME_TEMPLATE = '{RESULTS_DIR}{os_path_sep}{DATE_STR}_{prefix}_{name}.csv'

SUMMARY_CSV_FILENAME = SESS_RESULTS_CSV_FILENAME_TEMPLATE.format(
    RESULTS_DIR=RESULTS_DIR, os_path_sep=os.path.sep, prefix='r0',
    name='summary', DATE_STR=DATE_STR)
EPISODES_CSV_FILENAME = SESS_RESULTS_CSV_FILENAME_TEMPLATE.format(
    RESULTS_DIR=RESULTS_DIR, os_path_sep=os.path.sep, prefix='r1',
    name='episodes', DATE_STR=DATE_STR)

BINDINGS_PACKAGE_NAME = 'deepdrive'

PUBLIC = 'DEEPDRIVE_PUBLIC' in os.environ

ALEXNET_NAME = 'AlexNet'
ALEXNET_FC7 = 4096
ALEXNET_IMAGE_SHAPE = (227, 227, 3)
MOBILENET_V2_NAME = 'MobileNetV2'
MOBILENET_V2_SLIM_NAME = 'mobilenet_v2_deepdrive'
MOBILENET_V2_IMAGE_SHAPE = (224, 224, 3)
