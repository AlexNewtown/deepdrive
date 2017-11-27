from __future__ import print_function
import sys
from distutils.version import LooseVersion as semvar


def main():
    error_msg = '\n\n*** Warning: %s, baseline imitation learning agent will not be available. ' \
                'HINT: Check out our CUDA / cuDNN install tips on the readme ' \
                'https://github.com/deepdrive/deepdrive-agents if you choose to install Tensorflow. ' \
                '\n\n'

    print('Checking for valid Tensorflow installation')
    try:
        # noinspection PyUnresolvedReferences
        import tensorflow as tf
        check = tf.constant('string tensors are not tensors but are called tensors in tensorflow')
        with tf.Session(config=tf.ConfigProto(log_device_placement=False,
                                              gpu_options=tf.GPUOptions(per_process_gpu_memory_fraction=0.01,
                                                                        allow_growth=True))) as sess:
            if not get_available_gpus():
                print('\n\n*** Warning: %s \n\n' %
                      'Tensorflow could not find a GPU, performance will be severely degraded on CPU.')
            sess.run(check)
            print('Tensorflow is working.')

    except ImportError:
        print(error_msg % 'Tensorflow not installed', file=sys.stderr)
        return
    except Exception:
        print(error_msg % 'Tensorflow not working', file=sys.stderr)
        return

    if semvar(tf.__version__) < semvar("1.1"):
        print(error_msg % 'Tensorflow version less than 1.1 detected', file=sys.stderr)
        return


def get_available_gpus():
    from tensorflow.python.client import device_lib
    local_device_protos = device_lib.list_local_devices()
    return [x.name for x in local_device_protos if x.device_type == 'GPU']


if __name__ == '__main__':
    main()
