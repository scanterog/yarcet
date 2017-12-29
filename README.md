# Yet Another Remote Command Execution Tool (YARCET)

The idea behind this simple tool is to execute the same "recipe" (set of instructions) to many servers 
sequentially or in parallel. Sometimes we don't need to write a playbook (Ansible) to execute some simple 
set of instructions and yarcet is useful for this reduced but still needed tasks.

In order to SSH-in to your nodes, your ssh pub key must be installed for your user in the remote node (`.ssh/authortized_keys`).
So far, the only authentication mode supported is SSH key based authentication through an SSH Agent.

Still WIP. Parallel execution not supported so far. It will be added soon. Only tested on Linux. Python2 not supported.

## Configuration file

The configuration file is a simple JSON file. By default, the tool looks for "config.json". Example:

```
{
  "connection_mode": "sequential",
  "output_mode": "tee",
  "node_groups": {
    "example.org": ["host.example.org", "mail.example.org", "backup.example.org"],
    "staging": ["10.137.16.166", "10.137.16.64", "10.137.16.8"]
  },  
  "ssh": {
    "user": "scg",
    "sudo": true,
    "agent": true
  },  
  "log_path": "./logs"
}
```

### Directives:
* `connection_mode` is either sequential or parallel. Sequential mode allows interactive session. This is useful in case you 
forgot to make your script fully non-interactive and hence we avoid hangs up.
* `output_mode` is only available for sequential and ignored for parallel. It is either stdout or tee. 
"tee" is stdout + log to file. "stdout" can't be disabled for sequential.
* `node_groups` specifies the groups of nodes (or clusters) we usually work with. The node group to work with must be selected 
in the command line as shown later below.
* `ssh` allows us to specify information related to SSH auth and if the recipe will be executed with sudo. 
___Constraint___: "agent" must be true. Other auth method is not supported so far.
* `log_path`: path where logs will be sent.

# Usage example:
```
./yarcet staging recipes/add_user.sh
```
![output](https://people.sugarlabs.org/scg/yarcet.png)

