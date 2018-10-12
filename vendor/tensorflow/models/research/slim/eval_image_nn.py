# Copyright 2016 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Generic evaluation script that evaluates a model using a given dataset."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import glob
import math
import os

import tensorflow as tf

from config import TENSORFLOW_OUT_DIR, CONTROL_NAMES
from vendor.tensorflow.models.research.slim.datasets import dataset_factory
from vendor.tensorflow.models.research.slim.nets import nets_factory
from vendor.tensorflow.models.research.slim.preprocessing import preprocessing_factory

from agents.dagger.net import MOBILENET_V2_SLIM_NAME

slim = tf.contrib.slim


def create_flags():
    tf.app.flags.DEFINE_integer(
        'batch_size', 100, 'The number of samples in each batch.')

    tf.app.flags.DEFINE_integer(
        'max_num_batches', None,
        'Max number of batches to evaluate by default use all.')

    tf.app.flags.DEFINE_string(
        'master', '', 'The address of the TensorFlow master to use.')

    tf.app.flags.DEFINE_string(
        'checkpoint_path', None,
        'The directory where the model was written to or an absolute path to a '
        'checkpoint file.')

    tf.app.flags.DEFINE_string(
        'eval_dir', None, 'Directory where the results are saved to.')

    tf.app.flags.DEFINE_integer(
        'num_preprocessing_threads', 4,
        'The number of threads used to create the batches.')

    tf.app.flags.DEFINE_string(
        'dataset_name', 'imagenet', 'The name of the dataset to load.')

    tf.app.flags.DEFINE_string(
        'dataset_split_name', 'test', 'The name of the train/test split.')

    tf.app.flags.DEFINE_string(
        'dataset_dir', None, 'The directory where the dataset files are stored.')

    tf.app.flags.DEFINE_integer(
        'labels_offset', 0,
        'An offset for the labels in the dataset. This flag is primarily used to '
        'evaluate the VGG and ResNet architectures which do not use a background '
        'class for the ImageNet dataset.')

    tf.app.flags.DEFINE_string(
        'model_name', 'inception_v3', 'The name of the architecture to evaluate.')

    tf.app.flags.DEFINE_string(
        'preprocessing_name', None, 'The name of the preprocessing to use. If left '
                                    'as `None`, then the model_name flag is used.')

    tf.app.flags.DEFINE_float(
        'moving_average_decay', None,
        'The decay to use for the moving average.'
        'If left as None, then moving averages are not used.')

    tf.app.flags.DEFINE_integer(
        'eval_image_size', None, 'Eval image size')


def main(_):
    create_flags()
    FLAGS = tf.app.flags.FLAGS
    slim_eval_image_nn(FLAGS.eval_dir, FLAGS.dataset_dir, FLAGS.dataset_name, FLAGS.dataset_split_name, FLAGS.model_name,
                       FLAGS.master, FLAGS.checkpoint_path, FLAGS.max_num_batches, FLAGS.labels_offset, FLAGS.moving_average_decay,
                       FLAGS.num_preprocessing_threads, FLAGS.batch_size, FLAGS.preprocessing_name, FLAGS.eval_image_size)


def slim_eval_image_nn(eval_dir=None, dataset_dir=None, dataset_name='imagenet', dataset_split_name='test',
                       model_name='inception_v3', master='', checkpoint_path=None, max_num_batches=None,
                       labels_offset=0, moving_average_decay=None, num_preprocessing_threads=4, batch_size=100,
                       preprocessing_name=None, eval_image_size=None):

    if eval_dir is None:
        eval_dir = max(glob.glob(TENSORFLOW_OUT_DIR + '/*'), key=os.path.getmtime)

    if not dataset_dir:
        raise ValueError('You must supply the dataset directory with --dataset_dir')

    tf.logging.set_verbosity(tf.logging.INFO)
    with tf.Graph().as_default():
        tf_global_step = slim.get_or_create_global_step()

        ######################
        # Select the dataset #
        ######################
        dataset = dataset_factory.get_dataset(
            dataset_name, dataset_split_name, dataset_dir)

        ####################
        # Select the model #
        ####################
        ######################
        # Select the network #
        ######################
        if model_name == MOBILENET_V2_SLIM_NAME:
            network_fn = nets_factory.get_network_fn(
                model_name,
                num_classes=None,
                num_targets=6,
                is_training=False, )

        else:
            network_fn = nets_factory.get_network_fn(
                model_name,
                num_classes=(dataset.num_classes - labels_offset),
                is_training=False)

        #####################################
        # Select the preprocessing function #
        #####################################
        preprocessing_name = preprocessing_name or model_name
        image_preprocessing_fn = preprocessing_factory.get_preprocessing(
            preprocessing_name,
            is_training=False)

        eval_image_size = eval_image_size or network_fn.default_image_size

        ##############################################################
        # Create a dataset provider that loads data from the dataset #
        ##############################################################
        provider = slim.dataset_data_provider.DatasetDataProvider(
            dataset,
            shuffle=False,
            common_queue_capacity=2 * batch_size,
            common_queue_min=batch_size)
        if model_name == MOBILENET_V2_SLIM_NAME:
            [image, spin, direction, speed, speed_change, steering, throttle] = provider.get(
                ['image', 'spin', 'direction', 'speed', 'speed_change', 'steering', 'throttle'])

            image = image_preprocessing_fn(image, eval_image_size, eval_image_size)

            images, targets = tf.train.batch(
                [image, [spin, direction, speed, speed_change, steering, throttle]],
                batch_size=batch_size,
                num_threads=num_preprocessing_threads,
                capacity=5 * batch_size)
        else:
            [image, label] = provider.get(['image', 'label'])
            label -= labels_offset

            image = image_preprocessing_fn(image, eval_image_size, eval_image_size)

            images, labels = tf.train.batch(
                [image, label],
                batch_size=batch_size,
                num_threads=num_preprocessing_threads,
                capacity=5 * batch_size)

        ####################
        # Define the model #
        ####################
        logits, _ = network_fn(images)

        if moving_average_decay:
            variable_averages = tf.train.ExponentialMovingAverage(
                moving_average_decay, tf_global_step)
            variables_to_restore = variable_averages.variables_to_restore(
                slim.get_model_variables())
            variables_to_restore[tf_global_step.op.name] = tf_global_step
        else:
            variables_to_restore = slim.get_variables_to_restore()

        if model_name == MOBILENET_V2_SLIM_NAME:
            # targets = tf.Print(targets, [targets[0][0], logits[0][0]], 'epxpected and actual spin ')
            # targets = tf.Print(targets, [targets[0][1], logits[0][1]], 'epxpected and actual direction ')
            # targets = tf.Print(targets, [targets[0][2], logits[0][2]], 'epxpected and actual speed ')
            # targets = tf.Print(targets, [targets[0][3], logits[0][3]], 'epxpected and actual speed_change ')
            # targets = tf.Print(targets, [targets[:, 4]], 'expected steering ', summarize=600)
            # targets = tf.Print(targets, [logits[:, 4]],  'actual steering   ', summarize=600)
            # targets = tf.Print(targets, [targets[0][5], logits[0][5]], 'epxpected and actual throttle ')

            target_delta = logits - targets

            for net_out_i, net_out_name in enumerate(CONTROL_NAMES):
                delta = target_delta[:, i]
                target_delta = tf.Print(target_delta, [delta], net_out_name + '_delta ', summarize=1000)
                mean_delta = tf.reduce_mean(tf.abs(delta))
                tf.summary.scalar('deepdrive_error/%s_eval' % net_out_name, mean_delta)
                targets = tf.Print(targets, [mean_delta], 'eval %s error ' % net_out_name)

            sq_root_normalized_target_delta = target_delta / targets.shape[1].value ** .5
            # sq_root_normalized_target_delta = tf.Print(sq_root_normalized_target_delta, [sq_root_normalized_target_delta], 'sq_root_normalized_target_delta ')

            dd_loss = tf.nn.l2_loss(sq_root_normalized_target_delta)

            targets = tf.Print(targets, [dd_loss], 'eval loss ')
            # targets = tf.Print(targets, [targets, logits], 'targets and logits ', summarize=100)
            # targets = tf.Print(targets, [targets, logits], 'target_delta ', summarize=100)

            # Define the metrics:
            names_to_values, names_to_updates = slim.metrics.aggregate_metric_map({
                'Accuracy': slim.metrics.streaming_accuracy(logits, targets)
            })

        else:
            predictions = tf.argmax(logits, 1)
            labels = tf.squeeze(labels)

            # Define the metrics:
            names_to_values, names_to_updates = slim.metrics.aggregate_metric_map({
                'Accuracy': slim.metrics.streaming_accuracy(predictions, labels),
                'Recall_5': slim.metrics.streaming_recall_at_k(
                    logits, labels, 5),
            })

        # Print the summaries to screen.
        for name, value in names_to_values.items():
            summary_name = 'eval/%s' % name
            op = tf.summary.scalar(summary_name, value, collections=[])
            op = tf.Print(op, [value], summary_name)
            tf.add_to_collection(tf.GraphKeys.SUMMARIES, op)

        # TODO(sguada) use num_epochs=1
        if max_num_batches:
            num_batches = max_num_batches
        else:
            # This ensures that we make a single pass over all of the data.
            num_batches = math.ceil(dataset.num_samples / float(batch_size))

        if model_name == MOBILENET_V2_SLIM_NAME:
            if not checkpoint_path:
                checkpoint_path = max(glob.glob(TENSORFLOW_OUT_DIR + '/*'), key=os.path.getmtime)

        if tf.gfile.IsDirectory(checkpoint_path):
            checkpoint_path = tf.train.latest_checkpoint(checkpoint_path)
        else:
            checkpoint_path = checkpoint_path

        tf.logging.info('Evaluating %s' % checkpoint_path)

        slim.evaluation.evaluate_once(
            master=master,
            checkpoint_path=checkpoint_path,
            logdir=eval_dir,
            num_evals=num_batches,
            eval_op=list(names_to_updates.values()),
            variables_to_restore=variables_to_restore)


if __name__ == '__main__':
    tf.app.run()