import os
import time
from datetime import datetime
import math
import glob

import gym
import tensorflow as tf
import numpy as np

import config as c
import deepdrive
from agents.dagger import net
from agents.dagger.train.train import resize_images
from gym_deepdrive.envs.deepdrive_gym_env import Action
from agents.dagger.net import AlexNet, MobileNetV2
from utils import save_hdf5, download
import logs

log = logs.get_log(__name__)


class Agent(object):
    def __init__(self, action_space, tf_session, env, should_record_recovery_from_random_actions=True,
                 should_record=False, net_path=None, use_frozen_net=False, random_action_count=0,
                 non_random_action_count=5, path_follower=False, recording_dir=c.RECORDING_DIR, output_last_hidden=False,
                 net_name=net.ALEXNET_NAME):
        np.random.seed(c.RNG_SEED)
        self.action_space = action_space
        self.previous_action = None
        self.previous_net_out = None
        self.step = 0
        self.env = env
        self.net_name = net_name

        # State for toggling random actions
        self.should_record_recovery_from_random_actions = should_record_recovery_from_random_actions
        self.random_action_count = random_action_count
        self.non_random_action_count = non_random_action_count
        self.semirandom_sequence_step = 0
        self.action_count = 0
        self.recorded_obz_count = 0
        self.performing_random_actions = False
        self.path_follower_mode = path_follower
        self.recording_dir = recording_dir
        self.output_last_hidden = output_last_hidden

        # Recording state
        self.should_record = should_record
        self.sess_dir = os.path.join(recording_dir, datetime.now().strftime(c.DIR_DATE_FORMAT))
        self.obz_recording = []

        if should_record_recovery_from_random_actions:
            log.info('Mixing in random actions to increase data diversity (these are not recorded).')
        if should_record:
            log.info('Recording driving data to %s', self.sess_dir)

        # Net
        self.sess = tf_session
        self.use_frozen_net = use_frozen_net
        if net_path is not None:
            if net_name == net.ALEXNET_NAME:
                input_shape = net.ALEXNET_IMAGE_SHAPE
            elif net_name == net.MOBILENET_V2_NAME:
                input_shape = net.MOBILENET_V2_IMAGE_SHAPE
            else:
                raise NotImplementedError(net_name + ' not recognized')
            self.load_net(net_path, use_frozen_net, input_shape)
        else:
            self.net = None
            self.sess = None

    def act(self, obz, reward, done):
        net_out = None
        if obz is not None:
            log.debug('steering %r', obz['steering'])
            log.debug('throttle %r', obz['throttle'])
            obz = self.preprocess_obz(obz)

        if self.should_record_recovery_from_random_actions:
            action = self.toggle_random_action()
            self.action_count += 1
        elif self.net is not None:
            if obz is None or not obz['cameras']:
                net_out = None
            else:
                image = obz['cameras'][0]['image']
                net_out = self.get_net_out(image)
            if net_out is not None and self.output_last_hidden:
                y_hat = net_out[0]
            else:
                y_hat = net_out
            action = self.get_next_action(obz, y_hat)
        else:
            action = Action(has_control=(not self.path_follower_mode))

        self.previous_action = action
        self.step += 1

        if obz and obz['is_game_driving'] == 1 and self.should_record:
            self.obz_recording.append(obz)
            # utils.save_camera(obz['cameras'][0]['image'], obz['cameras'][0]['depth'],
            #                   os.path.join(self.sess_dir, str(self.total_obz).zfill(10)))
            self.recorded_obz_count += 1
        else:
            log.debug('Not recording frame')

        self.maybe_save()

        action = action.as_gym()
        return action, net_out

    def get_next_action(self, obz, net_out):
        log.debug('getting next action')
        if net_out is None:
            log.debug('net out is None')
            return self.previous_action or Action()

        net_out = net_out[0]  # We currently only have one environment

        desired_spin, desired_direction, desired_speed, desired_speed_change, desired_steering, desired_throttle = \
            net_out

        desired_spin = desired_spin * c.SPIN_NORMALIZATION_FACTOR
        desired_speed = desired_speed * c.SPEED_NORMALIZATION_FACTOR
        desired_speed_change = desired_speed_change * c.SPEED_NORMALIZATION_FACTOR

        log.debug('desired_steering %f', desired_steering)
        log.debug('desired_throttle %f', desired_throttle)

        log.debug('desired_direction %f', desired_direction)
        log.debug('desired_speed %f', desired_speed)
        log.debug('desired_speed_change %f', desired_speed_change)
        log.debug('desired_throttle %f', desired_throttle)
        log.debug('desired_spin %f', desired_spin)

        actual_speed = obz['speed']
        log.debug('actual_speed %f', actual_speed)
        log.debug('desired_speed %f', desired_speed)

        if isinstance(self.net, MobileNetV2):
            # target_speed = 8 * 100
            target_speed = desired_speed
            # desired_throttle = abs(target_speed / max(actual_speed, 1e-3))
            # desired_throttle = min(max(desired_throttle, 0.), 1.)
            target_speed = 8 * 100
            desired_throttle = abs(target_speed / max(actual_speed, 1e-3))
            desired_throttle = min(max(desired_throttle, 0.), 1.)

            # if self.previous_net_out:
            #     desired_throttle = 0.2 * self.previous_action.throttle + 0.7 * desired_throttle
            # else:
            # desired_throttle = desired_throttle * 0.95

        else:
            # AlexNet
            target_speed = 9 * 100
            # Network overfit on speed, plus it's nice to be able to change it,
            # so we just ignore output speed of net
            desired_throttle = abs(target_speed / max(actual_speed, 1e-3))
            desired_throttle = min(max(desired_throttle, 0.), 1.)
        log.debug('actual_speed %r' % actual_speed)

        # log.info('desired_steering %f', desired_steering)
        # log.info('desired_throttle %f', desired_throttle)
        if self.previous_action:
            smoothed_steering = 0.2 * self.previous_action.steering + 0.5 * desired_steering
        else:
            smoothed_steering = desired_steering * 0.7

        # desired_throttle = desired_throttle * 1.1
        action = Action(smoothed_steering, desired_throttle)
        return action

    def maybe_save(self):
        if (
            self.should_record and self.recorded_obz_count % c.FRAMES_PER_HDF5_FILE == 0 and
            self.recorded_obz_count != 0
           ):
            filename = os.path.join(self.sess_dir, '%s.hdf5' %
                                    str(self.recorded_obz_count // c.FRAMES_PER_HDF5_FILE).zfill(10))
            save_hdf5(self.obz_recording, filename=filename)
            log.info('Flushing output data')
            self.obz_recording = []

    def toggle_random_action(self):
        """Reduce sampling error by diversifying experience"""
        if self.performing_random_actions:
            if self.action_count < self.random_action_count and self.previous_action is not None:
                action = self.previous_action
            else:
                # switch to non-random
                action = Action(has_control=False)
                self.action_count = 0
                self.performing_random_actions = False
        else:
            if self.action_count < self.non_random_action_count and self.previous_action is not None:
                action = self.previous_action
            else:
                # switch to random
                steering = np.random.uniform(-0.5, 0.5, 1)[0]  # Going too large here gets us stuck
                log.debug('random steering %f', steering)
                throttle = 0.65  # TODO: Make throttle random to get better variation here
                action = Action(steering, throttle)
                self.action_count = 0
                self.performing_random_actions = True
        return action

    def load_net(self, net_path, is_frozen=False, image_shape=None):
        """
        Frozen nets can be generated with something like

        `python freeze_graph.py --input_graph="C:\tmp\deepdrive\tensorflow_random_action\train\graph.pbtxt" --input_checkpoint="C:\tmp\deepdrive\tensorflow_random_action\train\model.ckpt-273141" --output_graph="C:\tmp\deepdrive\tensorflow_random_action\frozen_graph.pb" --output_node_names="model/add_2"`

        where model/add_2 is the auto-generated name for self.net.p
        """
        if image_shape is None:
            raise RuntimeError('Image shape not defined')
        if is_frozen:
            # TODO: Get frozen nets working

            # We load the protobuf file from the disk and parse it to retrieve the
            # unserialized graph_def
            with tf.gfile.GFile(net_path, "rb") as f:
                graph_def = tf.GraphDef()
                graph_def.ParseFromString(f.read())

            # Then, we can use again a convenient built-in function to import a graph_def into the
            # current default Graph
            with tf.Graph().as_default() as graph:
                tf.import_graph_def(
                    graph_def,
                    input_map=None,
                    return_elements=None,
                    name="prefix",
                    op_dict=None,
                    producer_op_list=None
                )
            self.net = graph

        else:
            if self.net_name == net.MOBILENET_V2_NAME:
                self.net = MobileNetV2(is_training=False)
            else:
                self.net = AlexNet(is_training=False)
            saver = tf.train.Saver()
            saver.restore(self.sess, net_path)

    def close(self):
        if self.sess is not None:
            self.sess.close()

    def get_net_out(self, image):
        begin = time.time()
        if self.use_frozen_net:
            out_var = 'prefix/model/add_2'
        else:
            out_var = self.net.out
        if self.output_last_hidden:
            out_var = [out_var, self.net.fc7]

        image = image.reshape(1, *self.net.input_image_shape)
        net_out = self.sess.run(out_var, feed_dict={
            self.net.input: image,})

        # print(net_out)
        end = time.time()
        log.debug('inference time %s', end - begin)
        return net_out

    # noinspection PyMethodMayBeStatic
    def preprocess_obz(self, obz):
        for camera in obz['cameras']:
            prepro_start = time.time()
            image = camera['image']
            image = image.astype(np.float32)
            image -= c.MEAN_PIXEL
            if isinstance(self.net, MobileNetV2):
                resize_start = time.time()
                image = resize_images(self.net.input_image_shape, [image], always=True)[0]
                log.debug('resize took %fs', time.time() - resize_start)
            camera['image'] = image
            log.debug('prepro took %fs',  time.time() - prepro_start)
        return obz

    def set_random_action_repeat_count(self):
        if self.semirandom_sequence_step == (self.random_action_count + self.non_random_action_count):
            self.semirandom_sequence_step = 0
            rand = c.RNG.random()
            if 0 <= rand < 0.67:
                self.random_action_count = 0
                self.non_random_action_count = 10
            elif 0.67 <= rand < 0.85:
                self.random_action_count = 4
                self.non_random_action_count = 5
            elif 0.85 <= rand < 0.95:
                self.random_action_count = 8
                self.non_random_action_count = 10
            else:
                self.random_action_count = 12
                self.non_random_action_count = 15
            log.debug('random actions at %r, non-random %r', self.random_action_count, self.non_random_action_count)

        else:
            self.semirandom_sequence_step += 1


def run(experiment, env_id='DeepDrivePreproTensorflow-v0', should_record=False, net_path=None, should_benchmark=True,
        run_baseline_agent=False, camera_rigs=None, should_rotate_sim_types=False,
        should_record_recovery_from_random_actions=False, render=False, path_follower=False, fps=c.DEFAULT_FPS,
        net_name=net.ALEXNET_NAME):
    if run_baseline_agent:
        net_path = ensure_baseline_weights(net_path)
    reward = 0
    episode_done = False
    max_episodes = 1000
    tf_config = tf.ConfigProto(
        gpu_options=tf.GPUOptions(
            per_process_gpu_memory_fraction=0.8,
            # leave room for the game,
            # NOTE: debugging python, i.e. with PyCharm can cause OOM errors, where running will not
            allow_growth=True
        ),
    )
    sess = tf.Session(config=tf_config)
    if camera_rigs:
        cameras = camera_rigs[0]
    else:
        cameras = None

    if should_record and camera_rigs is not None and len(camera_rigs) >= 1:
        should_rotate_camera_rigs = True
    else:
        should_rotate_camera_rigs = False

    if should_rotate_camera_rigs:
        randomize_cameras(cameras)

    use_sim_start_command_first_lap = c.SIM_START_COMMAND is not None
    gym_env = deepdrive.start(experiment, env_id, should_benchmark=should_benchmark, cameras=cameras,
                                  use_sim_start_command=use_sim_start_command_first_lap, render=render,
                                  fps=fps)
    dd_env = gym_env.env

    agent = Agent(gym_env.action_space, sess, env=gym_env.env,
                  should_record_recovery_from_random_actions=should_record_recovery_from_random_actions,
                  should_record=should_record, net_path=net_path, random_action_count=4, non_random_action_count=5,
                  path_follower=path_follower, net_name=net_name)
    if net_path:
        log.info('Running tensorflow agent checkpoint: %s', net_path)

    def close():
        gym_env.close()
        agent.close()

    session_done = False
    episode = 0
    try:
        while not session_done:
            if episode_done:
                obz = gym_env.reset()
                episode_done = False
            else:
                obz = None
            while not episode_done:

                act_start = time.time()
                action, net_out = agent.act(obz, reward, episode_done)
                log.debug('act took %fs',  time.time() - act_start)

                env_step_start = time.time()
                obz, reward, episode_done, _ = gym_env.step(action)
                log.debug('env step took %fs', time.time() - env_step_start)

                if render:
                    gym_env.render()
                if should_record_recovery_from_random_actions:
                    agent.set_random_action_repeat_count()
                if agent.recorded_obz_count > c.MAX_RECORDED_OBSERVATIONS:
                    session_done = True
                elif should_benchmark and dd_env.done_benchmarking:
                    session_done = True
            if session_done:
                log.info('Session done')
            else:
                log.info('Episode done, rotating camera')
                episode += 1
                if should_rotate_camera_rigs:
                    cameras = camera_rigs[episode % len(camera_rigs)]
                    randomize_cameras(cameras)
                    dd_env.change_viewpoint(cameras,
                                            use_sim_start_command=random_use_sim_start_command(should_rotate_sim_types))
                if episode >= max_episodes:
                    session_done = True
    except KeyboardInterrupt:
        log.info('keyboard interrupt detected, closing')
        close()
    close()


def randomize_cameras(cameras):
    for cam in cameras:
        # Add some randomness to the position (less than meter), rotation (less than degree), fov (less than degree),
        # capture height (1%), and capture width (1%)
        for i in range(len(cam['relative_rotation'])):
            cam['relative_rotation'][i] += math.radians(np.random.random())
        for i in range(len(cam['relative_position'])):
            if i == 0 or i == 2:
                # x - forward or z - up
                cam['relative_position'][i] += (np.random.random() * 100)
            elif i == 1:
                # y - right
                cam['relative_position'][i] += (np.random.random() * 100 - 50)

        cam['field_of_view'] += (np.random.random() - 0.5)
        cam['capture_height'] += round(np.random.random() * 0.01 * cam['capture_height'])
        cam['capture_width'] += round(np.random.random() * 0.01 * cam['capture_width'])
        pass


def random_use_sim_start_command(should_rotate_sim_types):
    use_sim_start_command = should_rotate_sim_types and np.random.random() < 0.5
    return use_sim_start_command


def ensure_baseline_weights(net_path):
    if net_path is not None:
        raise ValueError('Net path should not be set when running the baseline agent as it has its own weights.')
    net_path = os.path.join(c.BASELINE_WEIGHTS_DIR, c.BASELINE_WEIGHTS_VERSION)
    if not glob.glob(net_path + '*'):
        print('\n--------- Baseline weights not found, downloading ----------')
        download(c.BASELINE_WEIGHTS_URL + '?cache_bust=' + c.BASELINE_WEIGHTS_VERSION, c.WEIGHTS_DIR,
                 warn_existing=False, overwrite=True)
    return net_path
