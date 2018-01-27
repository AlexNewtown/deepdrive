# Deepdrive [![Build Status](https://travis-ci.com/crizCraig/deepdrive-agents-beta.svg?token=hcA6yn9X8yYZspyyCMpp&branch=master)](https://travis-ci.com/crizCraig/deepdrive-agents-beta)

The easiest way to experiment with self-driving AI

## Simulator requirements

- Linux or Windows
- Python 3.5+
- 3GB disk space
- 8GB RAM

## Optional - baseline agent requirements

- CUDA capable GPU (tested and developed on 970, 1070, and 1060's)
- Tensorflow 1.1+ [See NVIDIA install tips](#nvidia-install-tips)

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
Make sure the Python you want to use is in your **system** path, then

> Tip: We highly recommend using [Conemu](https://conemu.github.io/) for your Windows terminal

```
python install.py
```

If you run into issues, try starting the sim directly as Unreal may need to install some prerequisetes. The default location is in your user directory under <kbd>DeepDrive/sim</kbd>

## Usage

Activate the [pipenv](https://github.com/pypa/pipenv) virtualenv we've created for this project

```
pipenv shell
```

Then run `main.py` to

Run the **baseline** agent
```
python main.py --baseline
```

Drive **manually**
```
python main.py --manual
```

**Record** training data for imitation learning / behavioral cloning
```
python main.py --record --record-recovery-from-random-actions
```

**Train** on recorded data
```
python main.py --train
```

**Train** on the same dataset we collected [TODO link with README  (includes windows play-in-editor and standalone data + linux standalone)]
```
python main.py --train --dataset baseline
```

or for more options, see [main.py](main.py)

### Key binds 

* <kbd>Esc</kbd> - Pause
* <kbd>P</kbd> - useful in Unreal Editor
* <kbd>J</kbd> - Toggle shared mem stats
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
* <kbd>Z</kbd> move mouse outside window and click OR shift+F1 in editor mode OR Alt+Tab - shows mouse cursor


## Benchmark top scores (50 lap average)

| Score  | Weights |  Deepdrive version |
| ---:   | :---    |   ---: |
|[3059](https://d1y4edi1yk5yok.cloudfront.net/benchmarks/2018-01-02__09-49-03PM.csv)|[baseline_agent_weights.zip](https://d1y4edi1yk5yok.cloudfront.net/weights/baseline_agent_weights.zip)|2.0.20180101022103|

## Frame rate issues on Linux

If you experience low frame rates on Linux, you may need to install NVIDIA’s display drivers including their OpenGL drivers. We recommend installing these with CUDA which bundles the version you will need to run the baseline agent. Also, make sure to [plugin your laptop](https://help.ubuntu.com/community/PowerManagement/ReducedPower). If CUDA is installed, skip to testing [OpenGL](#opengl).

[CUDA install tips](#cuda-and-nvidia-driver-install)
[cuDNN install tips](#cudnn-install-tips)

## NVIDIA install tips

- Get the older [CUDA 8 and cuDNN 6](https://developer.nvidia.com/cuda-toolkit-archive) for a standard tensorflow install later on (read here to see if this changes: https://github.com/tensorflow/tensorflow/issues/12052) - If you want to use CUDA 9 / cuDNN 7, you’ll need to install Tensorflow from source.
- Use the packaged install, i.e. deb[local] on Ubuntu, referred to in [this guide](http://docs.nvidia.com/cuda/cuda-installation-guide-linux/index.html)
- If you are feeling frisky and use the runfile method, be sure to follow [NVIDIA’s instructions](http://docs.nvidia.com/cuda/cuda-installation-guide-linux/index.html) on how to disable the Nouveau drivers if you're on Ubuntu.

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
to py.test.


## Thanks

Special thanks to [Rafał Józefowicz](https://scholar.google.com/citations?user=C7zfAI4AAAAJ) for contributing the original [training](#tensorflow_agent/train) code on which ours is based 

### Random notes (TODO: Cleanup)

TIPS:
If you lose your mouse pointer while in the game, just Alt-Tab!

Make sure the CUDA_HOME environment variable is set (we used Cuda 8 for the baseline model), specifically /usr/local/cuda

Also make sure LD_LIBRARY_PATH is set - i.e. /home/<YOU>/cuda/lib64:

PATH includes /usr/local/cuda-YOUR_CUDA_VERSION/bin


To stop the simulation from the Unreal Editor in Linux, hit Esc.

Windows
Tensorflow install tips

Add /Users/a/Miniconda3/Scripts and /Users/a/Miniconda3 to your user environment variable path

To run Tensorboard, navigate to your C:\Users\<YOU>\Miniconda3\envs\tensorflow\Scripts and run tensorboard --logdir=/tmp/gtanet

Merge your cuDNN bin, lib, and include into your CUDA install bin, lib, and include directories, i.e.
- bin files to C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v8.0\bin
- lib files to C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v8.0\lib\x64
- headers to C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v8.0\include

Add cupti64_80.dll to user PATH environment variable, i.e.
cupti64_80.dll
in
C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v8.0\extras\CUPTI\libx64
Restart programs to get new path

Download https://www.dropbox.com/s/x153v1d001fqu91/bvlc_alexnet.ckpt?dl=1


Freeglut viewer (optional)
OpenGL / Freeglut
conda install pyopengl
http://www.transmissionzero.co.uk/software/freeglut-devel/
Make sure to get the architecture (x64) that corresponds with the Python version

Mac
Mac will be unsupported at first due to poor GPU support.

You will need MacOs to download Xcode 8 and build Unreal from sources but we don’t need that for substance.

External GPU’s will allow Macs to run demanding GPU loads, but we haven’t tried this setup yet. An alternative way to run eGPUs on Apple hardware would be to use Bootcamp to run Windows which appears to have the best eGPU support as of mid-2017. 



All

Install OpenCV
conda install -c https://conda.anaconda.org/menpo opencv3
conda install scipy
conda install pillow

PyCharm Development of Environment
If you open an Unreal project in Pycharm, add Binaries, Build, Content, Intermediate, and Saved to your project’s “Excluded” directories in Project Structure or simply by right clicking and choosing “Mark Directory as” => “Excluded”. Keeping these large binary directories in the project will cause PyCharm to index them.
