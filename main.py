import argparse
import glob
import logging

import os

import tensorflow as tf

import camera_config
import config as c
import logs
import deepdrive


def main():
    parser = argparse.ArgumentParser(description=None)
    parser.add_argument('-e', '--env-id', nargs='?', default='DeepDrive-v0', help='Select the environment to run')
    parser.add_argument('-r', '--record', action='store_true', default=False,
                        help='Records game driving, including recovering from random actions')
    parser.add_argument('--baseline', action='store_true', default=False,
                        help='Runs pretrained imitation learning based agent')
    parser.add_argument('-t', '--train', action='store_true', default=False,
                        help='Trains tensorflow agent on stored driving data')
    parser.add_argument('--use-last-model', action='store_true', default=False,
                        help='Run the most recently trained model')
    parser.add_argument('--recording-dir', nargs='?', default=c.RECORDING_DIR, help='Where to store and read recorded '
                                                                                    'environment data from')
    parser.add_argument('--render', action='store_true', default=False,
                        help='SLOW: render of camera data in Python - Use Unreal for real time camera rendering')
    parser.add_argument('--record-recovery-from-random-actions', action='store_true', default=False,
                        help='Whether to occasionally perform random actions and record recovery from them')
    parser.add_argument('--path-follower', action='store_true', default=False,
                        help='Whether to let the in-game path follower drive')
    parser.add_argument('--net-path', nargs='?', default=None,
                        help='Path to the tensorflow checkpoint you want to test drive. '
                             'i.e. /home/a/DeepDrive/tensorflow/2018-01-01__11-11-11AM_train/model.ckpt-98331')
    parser.add_argument('--resume-train', nargs='?', default=None,
                        help='Path to the tensorflow training session you want to resume, '
                             'i.e. /home/a/DeepDrive/tensorflow/2018-01-01__11-11-11AM_train')
    parser.add_argument('-v', '--verbose', help='Increase output verbosity',
                        action='store_true')
    parser.add_argument('--camera-rigs', nargs='?', default=None, help='Name of camera rigs to use')
    parser.add_argument('-n', '--experiment-name', nargs='?', default=None, help='Name of your experiment')
    parser.add_argument('--fps', type=int, default=c.DEFAULT_FPS, help='Frames / steps per second')
    parser.add_argument('--agent', nargs='?', default='dagger', help='Agent type (dagger, bootstrap)')



    args = parser.parse_args()
    if args.verbose:
        logs.set_level(logging.DEBUG)

    if args.camera_rigs:
        camera_rigs = camera_config.rigs[args.camera_rigs]
    else:
        camera_rigs = camera_config.rigs['baseline_rigs']

    if args.use_last_model:
        if args.train:
            args.resume_train = get_latest_model()
        else:
            args.net_path = get_latest_model()

    if args.train:
        # TODO: Add experiment name here as well, and integrate it into Tensorflow runs, recording names, model checkpoints, etc...
        if args.agent == 'dagger':
            '''
            Really it's just the first iteration of DAgger where our policy is random.
            This seems to be sufficient for exploring the types of mistakes our AI makes and labeling
            the corrections to those mistakes and does a better job at handling edge cases that
            the agent would not encounter acting under its own policy during training.
            In this way, we come a little closer to reinforcement learning, as we explore randomly covering
            a larger number of possibilities.
            '''
            from agents.dagger.train import train
            train.run(resume_dir=args.resume_train, recording_dir=args.recording_dir)
        elif args.agent == 'bootstrapped_ppo2':
            from agents.rl.ppo2.run_deepdrive import train
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
            sess.as_default()
            from agents import dagger

            # TODO: Make the dagger agent an environment wrapper, where you can call step, reset, etc...
            # Then when you call step, you get the codes back and resets will work as expected from the ppo2 code
            #

            dagger_code_gen = dagger.agent.run(args.experiment_name,
                                               net_path=args.net_path, env_id=args.env_id,
                                               run_baseline_agent=args.baseline, render=args.render, camera_rigs=camera_rigs,
                                               fps=args.fps, bootstrap=True, sess=sess)
            train(args.env_id, num_timesteps=int(10e6), seed=c.RNG_SEED, sess=sess, obz_gen=dagger_code_gen)

        else:
            raise Exception('Agent type not recognized')
    elif args.path_follower:
        done = False
        render = False
        episode_count = 1
        gym_env = None
        try:
            gym_env = deepdrive.start(args.experiment_name, args.env_id, fps=args.fps)
            log.info('Path follower drive mode')
            for episode in range(episode_count):
                if done:
                    gym_env.reset()
                while True:
                    action = deepdrive.action(has_control=False)
                    obz, reward, done, _ = gym_env.step(action)
                    if render:
                        gym_env.render()
                    if done:
                        gym_env.reset()
        except KeyboardInterrupt:
            log.info('keyboard interrupt detected, closing')
        except Exception as e:
            log.error('Error running agent. %s', e)
            if gym_env:
                gym_env.close()
            raise e
        if gym_env:
            gym_env.close()
        log.info('Last episode complete, closing')
    else:
        from agents.dagger import agent
        if args.record and not args.record_recovery_from_random_actions:
            args.path_follower = True
        agent.run(args.experiment_name,
                  should_record=args.record, net_path=args.net_path, env_id=args.env_id,
                  run_baseline_agent=args.baseline, render=args.render, camera_rigs=camera_rigs,
                  should_record_recovery_from_random_actions=args.record_recovery_from_random_actions,
                  path_follower=args.path_follower, fps=args.fps)


def get_latest_model():
    train_dirs = glob.glob('%s/*_train' % c.TENSORFLOW_OUT_DIR)
    latest_subdir = max(train_dirs, key=os.path.getmtime)
    if not latest_subdir:
        raise RuntimeError('Can not get latest model, no models found in % s' % c.TENSORFLOW_OUT_DIR)
    latest_model = max(glob.glob('%s/model.ckpt-*.meta' % latest_subdir), key=os.path.getmtime)
    if not latest_model:
        raise RuntimeError('Can not get latest model, no models found in %s' % latest_subdir)
    latest_prefix = latest_model[:-len('.meta')]
    return latest_prefix


log = logs.get_log(__name__)

if __name__ == '__main__':
    main()

