# Deepdrive [![Build Status](https://travis-ci.org/deepdrive/deepdrive.svg?branch=master)](https://travis-ci.org/deepdrive/deepdrive)

The easiest way to experiment with self-driving AI

## Simulator requirements

- Linux or Windows
- Python 3.6+ (Recommend Miniconda for Windows)
- 3GB disk space
- 8GB RAM

## Optional - baseline agent requirements

- CUDA capable GPU (tested and developed on 970, 1070, and 1060's)
- 1.7 <= Tensorflow < 2.0 [See Tensorflow install tips](#tensorflow-install-tips)

## Install

```
git clone https://github.com/deepdrive/deepdrive
cd deepdrive
```

> Optional - Activate the Python / virtualenv where your Tensorflow is installed, then

#### Linux
```
python install.py
```

#### Windows
Make sure the Python you want to use is in your PATH, then

> Tip: We highly recommend using [Conemu](https://conemu.github.io/) for your Windows terminal

```
python install.py
```

#### Cloud

We've tested on Paperspace's ML-in-a-Box Linux public template which already has Tensorflow installed and just requires

```
python install.py
```

If you run into issues, try starting the sim directly as Unreal may need to install some prerequisetes (i.e. DirectX needs to be installed on the Paperspace Parsec Windows box). The default location of the Unreal sim binary is in your user directory under <kbd>Deepdrive/sim</kbd>.

## Usage

#### Running

A minimal agent can be run with

```python
import sim
env = sim.start()
forward = sim.action(throttle=1, steering=0, brake=0)
while True:
    observation, reward, done, info = env.step(forward)
```

##### Observation data

All values returned in the observation keep Unreal conventions, specifically
* All distances are in centimeters per Unreal's default data type
* All rotations / angular values are in the order of roll, pitch, yaw in degrees
* x,y,z is forward, right, up

```

{ 
  
  'acceleration': array([-264.26913452, -227.578125  ,  105.16122437]),
  'angular_acceleration': array([210980.234375, 105423.765625,  38187.28125 ]),
  'angular_velocity': array([2.59908962, 3.8214705 , 1.87282801]),
  'brake': 0.0,
  'camera_count': 1,
  'cameras': [{  'aspect_ratio': 1.0,
                 'capture_height': 227,
                 'capture_width': 227,
                 'depth_data': array([0.9995  , 0.9995  , 0.9995  , ..., 
                     0.005146, 0.005146, 0.005146], dtype=float16),
                 'horizontal_field_of_view': 1.7654,
                 'id': 1,
                 'image': array([[[ 40.,  78., 110.] ..., dtype=float32),
                 'image_data': array([0.283  , 0.557  , 0.82, 
                     ..., 0.02321, 0.02574, 0.02599], dtype=float16),
                 'image_raw': array([[[144, 195, 233]..., dtype=uint8),
                 'type': 0
              }],
  'capture_timestamp': 4132.511303506,
  'dimension': array([514.99609375, 514.99609375,  91.1796875 ]),  # Vehicle dimensions
  'distance_along_route': 70658.828125,  # centimeters of progress made along route to destination
  'distance_to_center_of_lane': 1038.8463134765625,  # centimeters to center of lane
  'world': { 'vehicle_positions': [ [ -15800.8193359375,
                                      38030.23828125,
                                      19894.62890625],
                                    [ -13854.9384765625,
                                      39296.91015625,
                                      20041.6484375],
                                    [ -10323.2744140625,
                                      39767.69921875,
                                      20409.265625],
                                    [ -6528.05810546875,
                                      38875.75390625,
                                      21034.83984375],
                                    [ 4577.29150390625,
                                      36155.37890625,
                                      22704.166015625]]},
  'distance_to_next_agent': 326125.625, # Next agent in our lane 
  'distance_to_next_opposing_agent': -1.0,  # Next agent in opposite lane
  'distance_to_prev_agent': 30758.2734375,   # Next agent in our lane
  'forward_vector': array([-0.8840133 , -0.4375411 , -0.16455328]),
  'gym_action': [0, 1, 0, 0, True],
  'gym_done': False,
  'gym_reward': -2.4653405387152016,
  'handbrake': 0,
  'is_game_driving': 0,
  'is_passing': 0,
  'is_resetting': 205,
  'lap_number': 0,
  'last_collision': { 'collidee_velocity': array([0., 0., 0.]),
                      'collision_location': 'rear_right_fender',
                      'collision_normal': array([0., 0., 0.]),
                      'time_since_last_collision': 0.0,
                      'time_stamp': 4105.741911045,
                      'time_utc': 1562958070},
  'position': array([-10163.55371094,  17115.17382812,  22500.29492188]),
  'right_vector': array([-0.8840133 , -0.4375411 , -0.16455328]),
  'rotation': array([ 0.10010731, -0.16530512, -2.68199444]),
  'route_length': 273551.21875,
  'score': { 'avg_kph': 0,
             'closest_vehicle_cm': 15812.662932649602,
             'closest_vehicle_cm_while_at_least_4kph': 15812.662932649602,
             'cm_along_route': 18730.72265625,
             'collided_with_actor': False,
             'collided_with_non_actor': True,
             'end_time': '1969-12-31T16:00:00-08:00',
             'episode_time': 11.5,
             'gforce_penalty': 90.68476390028613,
             'got_stuck': False,
             'lane_deviation_penalty': 255.7695629358121,
             'max_gforce': 0.8785649610557551,
             'max_kph': 138.7572978515625,
             'max_lane_deviation_cm': 1038.8463134765625,
             'num_steps': 0,
             'prev_progress_pct': 6.70844576752594,
             'progress_pct': 6.8472451856879175,
             'progress_reward': 0.0,
             'route_length_cm': 273551.21875,
             'speed_reward': 371.6081579415893,
             'start_time': '2019-07-12T12:00:59.003417-07:00',
             'time_penalty': 0.0,
             'total': 25.15383110549117,
             'wrong_way': False},
  'speed': 3854.369384765625,
  'steering': 0.0,
  'throttle': 1.0,
  'up_vector': array([-0.8840133 , -0.4375411 , -0.16455328]),
  'velocity': array([-3404.32958984, -1700.12841797,  -613.90289307]),
  'view_mode': 'normal',
}
```

###### Want more?

Additional observation data can be exposed without compiling C++ or Blueprints by accessing the Unreal API via [UnrealEnginePython](https://docs.deepdrive.io/v/v3/docs/tutorial/uepy/uepy). Simply modify [get_observation](https://github.com/deepdrive/deepdrive-sim/blob/c2d26a38692f1db61d48986263b20721ab136fe3/Content/Scripts/api_methods.py#L56) in `api_methods.py`. 

##### Examples

* Synchronous forward-agent

```
python example_sync.py
```

* [Remote agent example](https://github.com/deepdrive/forward-agent) - operates over the network using the [deepdrive remote api](https://github.com/deepdrive/deepdrive-api)

* **mnet2 baseline** agent
```
python main.py --mnet2-baseline --experiment my-baseline-test
```

* Built-in C++ [FSM](https://github.com/deepdrive/deepdrive-sim/tree/c2d26a38692f1db61d48986263b20721ab136fe3/Plugins/DeepDrivePlugin/Source/DeepDrivePlugin/Private/Simulation/Agent/Controllers/LocalAI/States) / [PID](https://github.com/deepdrive/deepdrive-sim/blob/v3/Plugins/DeepDrivePlugin/Source/DeepDrivePlugin/Private/Simulation/Agent/Controllers/DeepDriveAgentSteeringController.cpp) agent that can overtake in the canyons map
```
python main.py --path-follower --experiment my-path-follower-test
```

**Record** training data for imitation learning / behavioral cloning
```
python main.py --record --jitter-actions --sync
```

Note that we recorded the baseline dataset in sync mode which is much slower than async mode. 
Async mode _probably_ is fine to record in, we just haven't got around to trying it out for v3.

Optional: Convert to HDF5 files to tfrecords (for training MNET2)
```
python main.py --hdf5-2-tfrecord
```


#### Training

**Train** on recorded data
```
python main.py --train [--agent dagger|dagger_mobilenet_v2|bootstrapped_ppo2] --recording-dir <your-hdf5-or-tfrecord-dir>
```

**Train** on the same dataset we used 

Grab the [dataset](#dataset)
```
python main.py --train --recording-dir <the-directory-with-the-dataset> [--agent dagger|dagger_mobilenet_v2|bootstrapped_ppo2]
```

**Tensorboard**

```
tensorboard --logdir="<your-deepdrive-home>/tensorflow"
```

Where `<your-deepdrive-home>` below is by default in `$HOME/Deepdrive` and can be configured in `$HOME/.deepdrive/deepdrive_dir`

#### Unit Tests

```
pytest tests/unit_tests/test_sanity.py
```

### Key binds 

* <kbd>Esc</kbd> - Pause (Quit in Unreal Editor)
* <kbd>Alt+Tab</kbd> - Control other windows
* <kbd>P</kbd> - Pause in Unreal Editor
* <kbd>;</kbd> - Toggle FPS
* <kbd>1</kbd> - Chase cam
* <kbd>2</kbd> - Orbit (side) cam
* <kbd>3</kbd> - Hood cam
* <kbd>4</kbd> - Free cam (use WASD to fly)
* WASD or Up, Down, Left Right - steer / throttle
* <kbd>Space</kbd> - Handbrake
* <kbd>Shift</kbd> - Nitro
* <kbd>H</kbd> - Horn
* <kbd>L</kbd> - Light
* <kbd>R</kbd> - Reset
* <kbd>E</kbd> - Gear Up
* <kbd>Q</kbd> - Gear down
* <kbd>Z</kbd> - Show mouse
* <kbd>`</kbd><kbd>`</kbd> - Unreal console (first press releases game input capture)


## Benchmark

| Agent  |  10 lap avg score  | Weights |  Deepdrive version |
| :---    | ---:   | :---    |   ---: |
|Baseline agent (trained with imitation learning)|[1691](https://docs.google.com/spreadsheets/d/1ryFaMFJhcTMBuhXZv0eMFHO35NMcXE2_MFLYqeUosfM/edit#gid=0)|[baseline_agent_weights.zip](https://d1y4edi1yk5yok.cloudfront.net/weights/baseline_agent_weights.zip)|2.0|
|Path follower |[*1069](https://docs.google.com/spreadsheets/d/1T5EuEobdVFn5ewdYTO20i9CqcZ-jIEsAihlV5lpvLQQ/edit#gid=0)| N/A (see [3D spline follower](https://github.com/crizCraig/deepdrive-beta/blob/bde6b8c48314c34a96ce0942fc398fae840720ee/Source/DeepDrive/Private/Car.cpp#L409))|2.0|

*The baseline agent currently outperforms the path follower it was trained on, likely due to the slower
speed the at which the baseline agent drives, resulting in lower lane deviation and g-force penalties. 
Interestingly, reducing the path follower speed causes it to crash at points where it otherwise loses traction and drifts, 
so the baseline agent has actually learned a more robust turning function than the original hardcoded path follower
it was trained on.

## Dataset

100GB (8.2 hours of driving) of camera, depth, steering, throttle, and brake of an 'oracle' path following agent. We rotate between three different cameras: normal, wide, and semi-truck - with random camera intrisic/extrinsic perturbations at the beginning of each episode (lap). This boosted performance on the benchmark by 3x. We also use DAgger to collect course correction data as in previous versions of Deepdrive.

1. Get the [AWS CLI](https://github.com/aws/aws-cli)
2. Ensure you have 104GB of free space
3. Download our dataset of mixed Windows (Unreal PIE + Unreal packaged) and Linux + variable camera and corrective action recordings 
(generated with `--record`)
```
cd <the-directory-you-want>
aws s3 sync s3://deepdrive/data/baseline_tfrecords .
```
or for the legacy HDF5 files for training AlexNet
```
aws s3 sync s3://deepdrive/data/baseline .
```

If you'd like to check out our Tensorboard training session, you can download the 1GB
[tfevents files here](https://d1y4edi1yk5yok.cloudfront.net/tensorflow/mnet2_baseline_training_and_eval.zip),
unzip, and run

```
tensorboard --logdir <your-unzipped-dir>
```

and checkout [this view](http://localhost:6006/#scalars&_smoothingWeight=0.935&runSelectionState=eyIyMDE4LTA3LTE5X18wNS01My0yN1BNIjp0cnVlLCIyMDE4LTA3LTE5X18wNS01MC01NFBNIjp0cnVlfQ%3D%3D&_ignoreYOutliers=false&tagFilter=error)
, which graphs wall time.

## Architecture

![Deepdrive Architecture](/docs/images/deepdrive-architecture.svg)

## Frame rate issues on Linux

If you experience low frame rates on Linux, you may need to install NVIDIA’s display drivers including their OpenGL drivers. We recommend installing these with CUDA which bundles the version you will need to run the baseline agent. Also, make sure to [plugin your laptop](https://help.ubuntu.com/community/PowerManagement/ReducedPower). If CUDA is installed, skip to testing [OpenGL](#opengl).

## Tensorflow install tips

- Make sure to install the CUDA / cuDNN major and minor version the Tensorflow instructions specify.  i.e. CUDA 9.0 / cuDNN 7.3 for Tensorflow 1.12.0. These will likely be older than the latest version NVIDIA offers. You can see all [CUDA  releases here](https://developer.nvidia.com/cuda-toolkit-archive).
- Use the packaged install, i.e. deb[local] on Ubuntu, referred to in [this guide](http://docs.nvidia.com/cuda/cuda-installation-guide-linux/index.html)
- If you are feeling dangerous and use the runfile method, be sure to follow [NVIDIA’s instructions](http://docs.nvidia.com/cuda/cuda-installation-guide-linux/index.html) on how to disable the Nouveau drivers if you're on Ubuntu.
- On Windows, use standard (non-CUDA packaged) display drivers which meet the min required. When installing CUDA, do a custom install and uncheck the display driver install.

## OpenGL

`glxinfo | grep OpenGL` should return something like:
```
OpenGL vendor string: NVIDIA Corporation
OpenGL renderer string: GeForce GTX 980/PCIe/SSE2
OpenGL core profile version string: 4.5.0 NVIDIA 384.90
OpenGL core profile shading language version string: 4.50 NVIDIA
OpenGL core profile context flags: (none)
OpenGL core profile profile mask: core profile
OpenGL core profile extensions:
OpenGL version string: 4.5.0 NVIDIA 384.90
OpenGL shading language version string: 4.50 NVIDIA
OpenGL context flags: (none)
OpenGL profile mask: (none)
OpenGL extensions:
OpenGL ES profile version string: OpenGL ES 3.2 NVIDIA 384.90
OpenGL ES profile shading language version string: OpenGL ES GLSL ES 3.20
OpenGL ES profile extensions:
```
You may need to disable secure boot in your BIOS in order for NVIDIA’s OpenGL and tools like nvidia-smi to work. This is not Deepdrive specific, but rather a general requirement of Ubuntu’s NVIDIA drivers.


## Development

To run tests in PyCharm, go to File | Settings | Tools | Python Integrated Tools and change the default test runner 
to `pytest`.

Also, disable SciView per [this answer](https://stackoverflow.com/a/48421532/134077).
