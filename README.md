# systest
Manage multiple Cloudify manager environments.

## Prerequisites
[cloudify-system-tests](https://github.com/cloudify-cosmo/cloudify-system-tests) should be installed in editable mode in the 
relevant virtualenv.

## Installation
```
pip install https://github.com/dankilman/systest/archive/master.tar.gz
```

## Getting Started

- Choose a location that will serve as the base directory for all `systest` related configuration and generated files. For example
```
export BASEDIR=$HOME/systest
mkdir -p $BASEDIR
```
- Initialize `systest` in the base directory. While we run `init` in a specific directory, note that initialization is only performed once, i.e. the init configuration will be stored in `~/.cloudify-systest` and subsequent `systest` commands
can be executed from any directory, not specifically the directory in which `init` was performed.
```
cd $BASEDIR
systest init
```
- The `init` command created two files: `suites.yaml` and `blueprints.yaml` which will be covered in the following sections. 
  It also created a directory named `configurations` which is where generated manager blueprint configurations will be placed.
  
  
