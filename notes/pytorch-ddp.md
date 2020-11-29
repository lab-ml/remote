# Running PyTorch Data Distributed Parallel training on remote computers

[LabML Remote](https://github.com/lab-ml/remote) runs jobs on remote servers
through a SSH connection and synchronises
the logs back to the local computer.
The [project readme](https://github.com/lab-ml/remote/blob/master/readme.md)
gives a good overview of the project,
and this is a guide on running distributed PyTorch model training on remote computers.

### 🕹  Install [LabML Remote](https://github.com/lab-ml/remote) with pip.

```bash
pip install labml-remote
```

### ⚙️  Add server information to configurations

It is basically a YAML file with a list of servers you have,
and this is the hardest step.

```
cd [YOUR PROJECT]
labml_remote init
```

This will create a sample configuration file `[PROJECT]/.remote/configs.yaml` and `[PROJECT]/.remote/exclude.txt`.
Edit `configs.yaml` with the server information.
Here is a simple example,
and look at [this sample](https://github.com/lab-ml/remote/blob/master/sample/.remote/configs.yaml),
for a slightly more complex configuration file.

```yaml
name: my_project
servers:
  first-server:
    hostname: 3.19.32.53
  second-server:
    hostname: 3.19.32.54
```

`exclude.txt` is a list of files and folders to be excluded from syncing.
That is, files/folders that should not be send to the servers.
Here is a [sample](https://github.com/lab-ml/remote/blob/master/sample/.remote/exclude.txt) for that.

### 🖥  Prepare the servers.

```bash
labml_remote prepare
```

![labml_remote prepare](https://github.com/lab-ml/remote/raw/master/notes/ddp-prepare-servers.png)

This command will
1. Install *miniconda* on all the servers
2. Synchronize the contents of your project folder with the server using *rsync*.
3. Install pip packages based on your `requirements.txt` or `Pipfile`.

This will usually take about a minute per server.

### 🚀  Launch the distributed training.

```bash
labml_remote helper-torch-launch --cmd 'mnist.py' --nproc-per-node 2 --env GLOO_SOCKET_IFNAME enp1s0
```

![labml_remote helper-torch-launch](https://github.com/lab-ml/remote/raw/master/notes/ddp-launch.png)

That's it! 🎉 Your model will train in parallel on multiple servers.

`--cmd` is the python script and arguments that's ready for
[torch.distributed.launch](https://github.com/pytorch/pytorch/blob/master/torch/distributed/launch.py) - 
[PyTorch Distribution documentation](https://pytorch.org/docs/stable/distributed.html).

`--nproc-per-node` is the number of process per server, which is usually the number of GPUs
if each of your processes use a single GPU.

`--env`  accepts two arguments to set environment variables.
Setting `GLOO_SOCKET_IFNAME` is required
for PyTorch distributed to work with `gloo` backend.

👨‍🏫 Here is a [mnist sample code](https://github.com/lab-ml/remote/blob/master/sample/mnist.py)
 we ran for the screenshot.
This uses [LabML](https://github.com/lab-ml/labml) for experiment monitoring,
 but this is not required.
You can launch any PyTorch distributed code compatible with `torch.distributed.launch` using
`labml_remote helper-torch-launch`.

### Checking the list of jobs

```
labml_remote job-list --rsync
```

![labml_remote job-list](https://github.com/lab-ml/remote/raw/master/notes/ddp-job-list.png)

This lists all the jobs running on the servers.

`--rsync` flag will force it to synchronize back the logs of the jobs before listing.
This will make sure the job statuses are up-to-date.

It shows a list of running jobs, with following details:
1. (in blue) the job key
2. a unique job ID *(you can find the all the logs of the job in folder `[PROJECT]/.remote/jobs/[unique ID]`)*
3. (in cyan) the server on which the job is running 
4. (in pink) process ID of the job
5. (in blue) tags - you can use tags for searching and selecting jobs
6. command

Run `labml-remote job-list --help` to get help.

### Watching job output

```
labml_remote job-tail
```

![labml_remote job-tail](https://github.com/lab-ml/remote/raw/master/notes/ddp-tail.png)

This will wait, watch and show the outputs similar to `tail -f`.
You can select a job with tags.
If no tags are provided it will select a running job tagged `master`.

Run `labml-remote job-tail --help` to get help.

### Killing jobs

```
labml_remote job-kill
```

![labml_remote job-tail](https://github.com/lab-ml/remote/raw/master/notes/ddp-kill.png)

This will kill all the jobs running on all servers.
*In this screenshot the jobs `12`, `13`, and `14` died with `ConnectionResetError` when
the job `11` was killed.*

Run `labml-remote job-kill --help` to get help on how to kill specific jobs by job key or tags.

## 🐍  Python API

This library can also be used to launch jobs using Python.

```python
labml_remote.job.JOBS.create('[SERVER NAME]', 'python path/to/my_script.py',
                             {'ENV_VAR1': 'VAL',
                              'ENV_VAR2': 'VAL'}, ['tag1', 'tag2']).start()
```

[Here is an example](https://github.com/lab-ml/remote/blob/master/sample/api_sample.py)
 that launches a training session using a python script.

## 🗒  Notes

The logs of all the commands executed over SSH are stored in `[PROJECT]/.remote/logs` and the jobs 
are stored in `[PROJECT]/.remote/jobs`.