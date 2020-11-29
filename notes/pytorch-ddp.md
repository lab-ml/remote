# Running PyTorch Data Distributed Parallel training on remote computers

[LabML Remote](https://github.com/lab-ml/remote) run jobs on remote servers
through an SSH connection and synchronises
the outputs back to your local computer.
The project [readme](https://github.com/lab-ml/remote/blob/master/readme.md)
gives a good overview of the project,
and this is a guide on running distributed PyTorch model training on remote computers,
with a few command lines instructions.

First, you need to install [LabML Remote](https://github.com/lab-ml/remote) with pip.

```bash
pip install labml-remote
```

Next, you need to add server information to [LabML Remote](https://github.com/lab-ml/remote)
 configurations. This is the hardest step.

```
cd [YOUR PROJECT]
labml_remote init
```

This will create a sample configuration file `.remote/configs.yaml` and `.remote/exclude.txt`.
Edit `configs.yaml` with the server information.
Here is a simple example,
and look at this [sample](https://github.com/lab-ml/remote/blob/master/sample/.remote/configs.yaml),
for a slightly more complex configuration file.
It is basically a list of servers you have.

```yaml
name: my_project
servers:
  first-server:
    hostname: 3.19.32.53
  second-server:
    hostname: 3.19.32.53
```

`exclude.txt` is a list of files and folders to be excluded from syncing.
That is files/folders that should not be send to the servers.
Here is a [sample](https://github.com/lab-ml/remote/blob/master/sample/.remote/exclude.txt) for that.

Once this is over you can prepare the servers.

```bash
labml_remote prepare
```

This command will
1. Install *miniconda* on all the servers
