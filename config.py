import random
import os
import sys

from datetime import datetime
import numpy as np

# Net
NUM_TARGETS = 6
IMAGE_SHAPE = (227, 227, 3)

# Normalization
SPIN_THRESHOLD = 1.0
SPEED_NORMALIZATION_FACTOR = 2000.
SPIN_NORMALIZATION_FACTOR = 10.
MEAN_PIXEL = np.array([104., 117., 123.], np.float32)

# HDF5
FRAMES_PER_HDF5_FILE = 1000
MAX_RECORDED_OBSERVATIONS = FRAMES_PER_HDF5_FILE * 250
NUM_TRAIN_FILES_TO_QUEUE = 2000 // FRAMES_PER_HDF5_FILE

# OS 
IS_LINUX = sys.platform == 'linux' or sys.platform == 'linux2'
IS_MAC = sys.platform == 'darwin'
IS_UNIX = IS_LINUX or IS_MAC or 'bsd' in sys.platform.lower()
IS_WINDOWS = sys.platform == 'win32'

# Set DEEPDRIVE_DIR
DEEPDRIVE_DIR = os.environ.get('DEEPDRIVE_DIR')
if DEEPDRIVE_DIR is None:
    config_dir = os.path.expanduser('~') + '/.deepdrive'
    os.makedirs(config_dir, exist_ok=True)
    deepdrive_dir_config = os.path.join(config_dir, 'deepdrive_dir')
    if os.path.exists(deepdrive_dir_config):
        with open(deepdrive_dir_config) as f:
            DEEPDRIVE_DIR = f.read()
    else:
        default_dir = os.path.join(os.path.expanduser('~'), 'DeepDrive')
        DEEPDRIVE_DIR = input('Where would you like to store DeepDrive files '
                              '(i.e. sim binaries, checkpoints, recordings, and logs)? [Default - %s] ' % default_dir)
        deepdrive_dir_set = False
        while not deepdrive_dir_set:
            DEEPDRIVE_DIR = DEEPDRIVE_DIR or default_dir
            if 'deepdrive' not in DEEPDRIVE_DIR.lower():
                DEEPDRIVE_DIR = os.path.join(DEEPDRIVE_DIR, 'DeepDrive')
            if not os.path.isabs(DEEPDRIVE_DIR):
                DEEPDRIVE_DIR = input('Path: %s is not absolute, please specify a different path [Default - %s] ' %
                                      (DEEPDRIVE_DIR, default_dir))
            if os.path.isfile(DEEPDRIVE_DIR):
                DEEPDRIVE_DIR = input('Path: %s is already a file, please specify a different path [Default - %s] ' %
                                      (DEEPDRIVE_DIR, default_dir))
            else:
                deepdrive_dir_set = True
        with open(deepdrive_dir_config, 'w') as f:
            f.write(DEEPDRIVE_DIR)
            print('%s written to %s' % (DEEPDRIVE_DIR, deepdrive_dir_config))
DEEPDRIVE_DIR = DEEPDRIVE_DIR.replace('\r', '').replace('\n', '')
os.makedirs(DEEPDRIVE_DIR, exist_ok=True)

# Data directories
DIR_DATE_FORMAT = '%Y-%m-%d__%I-%M-%S%p'
DATE_STR = datetime.now().strftime(DIR_DATE_FORMAT)
RECORDINGS_DIR = os.path.join(DEEPDRIVE_DIR, 'recordings')
GYM_DIR = os.path.join(DEEPDRIVE_DIR, 'gym')
LOG_DIR = os.path.join(DEEPDRIVE_DIR, 'log')
BENCHMARK_DIR = os.path.join(DEEPDRIVE_DIR, 'benchmark')
TENSORFLOW_OUT_DIR = os.path.join(DEEPDRIVE_DIR, 'tensorflow')
WEIGHTS_DIR = os.path.join(DEEPDRIVE_DIR, 'weights')

# Weights
BASELINE_WEIGHTS_DIR = os.path.join(WEIGHTS_DIR, 'baseline_agent_weights')
BASELINE_WEIGHTS_VERSION = 'model.ckpt-122427'
BVLC_CKPT_NAME = 'bvlc_alexnet.ckpt'
BVLC_CKPT_PATH = os.path.join(WEIGHTS_DIR, BVLC_CKPT_NAME)

# Urls
BASE_URL = 'https://d1y4edi1yk5yok.cloudfront.net'
BASE_WEIGHTS_URL = BASE_URL + '/weights'
BASELINE_WEIGHTS_URL = BASE_WEIGHTS_URL + '/baseline_agent_weights.zip'
BVLC_CKPT_URL = '%s/%s.zip' % (BASE_WEIGHTS_URL, BVLC_CKPT_NAME)
SIM_BIN_URL = BASE_URL + '/sim/deepdrive-sim-2.0.20171127052011.zip'

# Seeded random number generator for reproducibility
RNG = random.Random(42.77)

# Sim
SIM_DEV = 'DEEPDRIVE_SIM_DEV' in os.environ
SIM_PATH = os.path.join(DEEPDRIVE_DIR, 'sim')
if SIM_DEV:
    SIM_BIN_PATH = None
elif IS_LINUX:
    SIM_BIN_PATH = SIM_PATH + '/DeepDrive/Binaries/Linux/DeepDrive'
elif IS_MAC:
    raise NotImplementedError('Support for OSX not yet implemented')
elif IS_WINDOWS:
    raise NotImplementedError('Windows sim binary path not yet implemented')
