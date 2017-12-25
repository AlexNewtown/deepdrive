import gym_deepdrive  # forward registers gym enviornment
import gym
import logs

import config as c
from gym_deepdrive.envs.deepdrive_gym_env import gym_action as action
gym.undo_logger_setup()
log = logs.get_log(__name__)


def start(env='DeepDrive-v0', sess=None, start_dashboard=True, should_benchmark=True, should_end_on_lap=False,
          cameras=None, use_sim_start_command=False):
    env = gym.make(env)
    env = gym.wrappers.Monitor(env, directory=c.GYM_DIR, force=True)
    env.seed(0)
    dd_env = env.env
    dd_env.set_to_end_on_lap(should_end_on_lap)
    dd_env.set_use_sim_start_command(use_sim_start_command)
    dd_env.open_sim()
    dd_env.connect(cameras)
    if sess:
        dd_env.set_tf_session(sess)
    if start_dashboard:
        dd_env.start_dashboard()
    if should_benchmark:
        log.info('Benchmarking enabled - will save results to %s', c.BENCHMARK_DIR)
        dd_env.init_benchmarking()
    return env
