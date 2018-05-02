from __future__ import print_function

import os

import numpy as np
import scipy.misc
import tensorflow as tf

import config as c
from agents.dagger import net
from agents.dagger.net import Net, AlexNet, MobileNetV2
from agents.dagger.train.data_utils import get_dataset
from utils import download, has_stuff
import logs


log = logs.get_log(__name__)


def visualize_model(model_in, model_out, y):
    names = ["spin", "direction", "speed", "speed_change", "steering", "throttle"]
    for i in range(6):
        p = tf.reduce_mean(model_out[:, i])
        tf.summary.scalar("losses/{}/p".format(names[i]), tf.reduce_mean(p))
        err = 0.5 * tf.reduce_mean(tf.square(model_out[:, i] - y[:, i]))
        tf.summary.scalar("losses/{}/error".format(names[i]), err)
    tf.summary.image("model/x", model_in, max_outputs=10)


def visualize_gradients(grads_and_vars):
    grads = [g for g, v in grads_and_vars]
    var_list = [v for g, v in grads_and_vars]
    for g, v in grads_and_vars:
        if g is None:
            continue
        tf.summary.histogram(v.name, v)
        tf.summary.histogram(v.name + "/grad", g)
        tf.summary.scalar("norms/" + v.name, tf.global_norm([v]))
        tf.summary.scalar("norms/" + v.name + "/grad", tf.global_norm([g]))
    grad_norm = tf.global_norm(grads)
    tf.summary.scalar("model/grad_global_norm", grad_norm)
    tf.summary.scalar("model/var_global_norm", tf.global_norm(var_list))


def run(resume_dir=None, data_dir=c.RECORDING_DIR, agent_name=None, overfit=False):
    with tf.variable_scope("model"):
        global_step = tf.get_variable("global_step", [], tf.int32, initializer=tf.zeros_initializer, trainable=False)
    agent_net = get_agent_net(agent_name, global_step)
    log.info('starter learning rate is %f', agent_net.starter_learning_rate)
    sess_eval_dir, sess_train_dir = get_dirs(resume_dir)

    targets_tensor = tf.placeholder(tf.float32, (None, agent_net.num_targets))
    total_loss = setup_loss(agent_net, targets_tensor)
    opt = tf.train.AdamOptimizer(agent_net.learning_rate)
    tf.summary.scalar("model/learning_rate", agent_net.learning_rate)
    summary_op, sv, train_op = get_train_ops(agent_net, global_step, opt, sess_train_dir, targets_tensor, total_loss)

    eval_sw = tf.summary.FileWriter(sess_eval_dir)

    train_dataset = get_dataset(data_dir, log, overfit=overfit, mute_spurious_targets=agent_net.mute_spurious_targets)
    eval_dataset = get_dataset(data_dir, log, train=False, mute_spurious_targets=agent_net.mute_spurious_targets)
    config = tf.ConfigProto(allow_soft_placement=True)
    with sv.managed_session(config=config) as sess, sess.as_default():
        train_data_provider = train_dataset.iterate_forever(agent_net.batch_size)
        log.info('\n\n*********************************************************************\n'
                 'Start tensorboard with \n\n\ttensorboard --logdir="' + c.TENSORFLOW_OUT_DIR +
                 '"\n\n(In Windows tensorboard will be in your python env\'s Scripts folder, '
                 'i.e. C:\\Users\\<YOU>\\Miniconda3\\envs\\tensorflow\\Scripts) but this should already be in your path \n'
                 'Then navigate to http://localhost:6006 - You may see errors if Tensorboard was already '
                 'started / has tabs open. If so, shut down Tenosrboard first and close all Tensorboard tabs. '
                 'Sometimes you may just need to restart training if you get CUDA device errors.'
                 '\n*********************************************************************\n\n')
        while True:
            for i in range(1000):
                loss = train_batch(agent_net, i, sess, summary_op, sv, targets_tensor, train_data_provider,
                                   train_op, total_loss)
                step = global_step.eval()

                log.info('step %d loss %f', step, loss)

            step = global_step.eval()
            perform_eval(step, agent_net, agent_net.batch_size, eval_dataset, eval_sw, sess)


def get_dirs(resume_dir):
    os.makedirs(c.TENSORFLOW_OUT_DIR, exist_ok=True)
    if resume_dir is not None:
        date_str = resume_dir[resume_dir.rindex('/') + 1:resume_dir.rindex('_')]
    else:
        date_str = c.DATE_STR
    sess_train_dir = '%s/%s_train' % (c.TENSORFLOW_OUT_DIR, date_str)
    sess_eval_dir = '%s/%s_eval' % (c.TENSORFLOW_OUT_DIR, date_str)
    os.makedirs(sess_train_dir, exist_ok=True)
    os.makedirs(sess_eval_dir, exist_ok=True)
    return sess_eval_dir, sess_train_dir


def get_agent_net(agent_name, global_step, overfit=False):
    if agent_name is None or agent_name == c.DAGGER:
        agent_net_fn = AlexNet
    elif agent_name == c.DAGGER_MNET2:
        agent_net_fn = MobileNetV2
    else:
        raise NotImplementedError('%r agent_name not supported' % agent_name)
    agent_net = agent_net_fn(global_step, overfit=overfit)
    return agent_net


def get_train_ops(agent_net, global_step, opt, sess_train_dir, targets_tensor, total_loss):
    grads_and_vars = opt.compute_gradients(total_loss)
    visualize_model(agent_net.input, agent_net.out, targets_tensor)
    visualize_gradients(grads_and_vars)
    summary_op = tf.summary.merge_all()
    update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
    with tf.control_dependencies(update_ops):
        train_op = opt.apply_gradients(grads_and_vars, global_step)
    init_fn = agent_net.get_tf_init_fn(tf.global_variables_initializer())
    saver = tf.train.Saver()
    sv = tf.train.Supervisor(is_chief=True,
                             logdir=sess_train_dir,
                             summary_op=None,  # Automatic summaries don't work with placeholders.
                             saver=saver,
                             global_step=global_step,
                             save_summaries_secs=30,
                             save_model_secs=60,
                             init_op=None,
                             init_fn=init_fn)
    return summary_op, sv, train_op


def setup_loss(agent_net, targets_tensor):
    l2_norm = tf.global_norm(tf.trainable_variables())
    loss = 0.5 * tf.reduce_sum(tf.square(agent_net.out - targets_tensor)) / tf.to_float(tf.shape(agent_net.input)[0])
    tf.summary.scalar("model/loss", loss)
    tf.summary.scalar("model/l2_norm", l2_norm)
    total_loss = loss + agent_net.weight_decay * l2_norm
    tf.summary.scalar("model/total_loss", total_loss)
    return total_loss


def train_batch(agent_net, i, sess, summary_op, sv, targets_tensor, train_data_provider, train_op, total_loss):
    images, targets = next(train_data_provider)
    log.debug('num images %r', len(images))
    log.debug('num targets %r', len(targets))
    valid_target_shape = True
    resize_images(agent_net.input_image_shape, images)
    loss = None
    for tgt in targets:
        if len(tgt) != 6:
            log.error('invalid target shape %r skipping' % len(tgt))
            valid_target_shape = False
    if valid_target_shape:
        feed_dict = {agent_net.input: images, targets_tensor: targets}  # , 'phase:0': 1}
        if i % 10 == 0 and i > 0:
            # Summarize: Do this less frequently to speed up training time, more frequently to debug issues
            try:
                _, summ, loss = sess.run([train_op, summary_op, total_loss], feed_dict)
            except ValueError as e:
                print('Error processing batch, skipping - error was %r' % e)
            sv.summary_computed(sess, summ)
            sv.summary_writer.flush()
        else:
            # print('evaluating %r' % feed_dict)
            try:
                _, loss = sess.run([train_op, total_loss], feed_dict)
            except ValueError as e:
                print('Error processing batch, skipping - error was %r' % e)
    return loss


def perform_eval(step, agent_net, batch_size, eval_dataset, eval_sw, sess):
    losses = []
    for images, targets in eval_dataset.iterate_once(batch_size):
        resize_images(agent_net.input_image_shape, images)
        predictions = sess.run(agent_net.eval_out, {agent_net.input: images, 'is_training': False})
        losses += [np.square(targets - predictions)]
    losses = np.concatenate(losses)
    summary = tf.Summary()
    eval_loss = float(0.5 * losses.sum() / losses.shape[0])
    log.info('eval loss %f', eval_loss)
    summary.value.add(tag="eval/loss", simple_value=eval_loss)
    names = ["spin", "direction", "speed", "speed_change", "steering", "throttle"]
    for i in range(len(names)):
        loss_component = float(0.5 * losses[:, i].mean())
        loss_name = names[i]
        summary.value.add(tag="eval/{}".format(loss_name), simple_value=loss_component)
        log.info('%s loss %f', loss_name, loss_component)
    eval_sw.add_summary(summary, step)
    eval_sw.flush()


def resize_images(input_image_shape, images):
    for img_idx, img in enumerate(images):
        img = images[img_idx]
        if img.shape != input_image_shape:
            log.debug('invalid image shape %s - resizing', str(img.shape))
            images[img_idx] = scipy.misc.imresize(img, (input_image_shape[0],
                                                        input_image_shape[1]))


if __name__ == "__main__":
    run()
