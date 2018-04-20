import gym
import tensorflow as tf
import numpy as np
from gym import spaces

import deepdrive
import config as c
import rl
from agents.dagger.agent import Agent as DaggerAgent
from rl.ppo2.run_deepdrive import train


class BootstrapGymEnv(gym.Wrapper):
    def __init__(self, env, dagger_agent, is_discrete):
        super(BootstrapGymEnv, self).__init__(env)
        self.dagger_agent = dagger_agent

        # One thing we need to do here is to make each action an bi-modal guassian to avoid averaging 50/50 decisions
        # i.e. half the time we veer left, half the time veer right - but on average this is go straight and can run us
        # into an obstacle. right now the DiagGaussianPd is just adding up errors which would not be the right
        # thing to do for a bi-modal guassian. also, DiagGaussianPd assumes steering and throttle are
        # independent which is not the case (steering at higher speeds causes more acceleration a = v**2/r),
        # so that may be a problem as well.

        self.observation_space = spaces.Box(low=np.finfo(np.float32).min,
                                            high=np.finfo(np.float32).max,
                                            shape=(c.NUM_FC7 + c.NUM_TARGETS,),
                                            dtype=np.float32)

    def step(self, action):
        obz, reward, done, info = self.env.step(action)
        action, net_out = self.dagger_agent.act(obz, reward, done)
        if net_out is None:
            obz = None
        else:
            obz = np.concatenate((net_out[0][0], net_out[1][0]))
        return obz, reward, done, info

    def reset(self):
        return self.env.reset()


def run(env_id, bootstrap_net_path,
        resume_dir=None, experiment=None, cameras=None, render=False, fps=c.DEFAULT_FPS,
        should_record=False, is_discrete=False):
    tf_config = tf.ConfigProto(
        allow_soft_placement=True,
        intra_op_parallelism_threads=1,
        inter_op_parallelism_threads=1,
        gpu_options=tf.GPUOptions(
            per_process_gpu_memory_fraction=0.8,
            # leave room for the game,
            # NOTE: debugging python, i.e. with PyCharm can cause OOM errors, where running will not
            allow_growth=True
        ),
    )

    sess = tf.Session(config=tf_config)
    with sess.as_default():
        dagger_gym_env = deepdrive.start(experiment, env_id, cameras=cameras, render=render, fps=fps,
                                         combine_box_action_spaces=True)
        dagger_agent = DaggerAgent(dagger_gym_env.action_space, sess, env=dagger_gym_env.env,
                                   should_record_recovery_from_random_actions=False, should_record=should_record,
                                   net_path=bootstrap_net_path, output_fc7=True)



        # Wrap step so we get the pretrained layer activations rather than pixels for our observation
        bootstrap_gym_env = BootstrapGymEnv(dagger_gym_env, dagger_agent, is_discrete)

        train(bootstrap_gym_env, num_timesteps=int(10e6), seed=c.RNG_SEED, sess=sess, is_discrete=is_discrete)
    #
    # action = deepdrive.action()
    # while not done:
    #     observation, reward, done, info = gym_env.step(action)


