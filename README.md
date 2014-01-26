# blt: provides simple CLI superpowers

**blt** is a python package that aims to make it easier for application
developers to wrap command line interfaces for the various tools they use day
to day. blt was inspired by Heroku's toolbelt, fabric, and clint. We hope
to stand on the shoulders of giants.

## Overview

At blt's root is the concept of a ``tool``, blt provides several tools out of
the box. Currently we have support for:

* AWS (S3)
* Django
* Heroku
* South (django database migrations)

These tools encapsulate commands that you would want to interface with each
system. For example, you might want to be able to push files to an S3 bucket
with the AWS tool, or you might want to run a migration using the South tool.
blt standardizes the interface for running the command and handles things like
configuration injection so you can easily differentiate between dev/staging/prod
settings when running a command.

## Real-world Example

Let's take a quick look at a practical example of blt in action. Here is a sample
command for running an AWS S3 sync on our staging environment:

```bash
blt e:staging aws.sync_s3 /path/to/my/dir
```

That's it! Running that command will pick up the staging environment
configuration, connect to S3, determine the changed files between the S3 bucket
and the files in /path/to/my/dir, and push them up to AWS. blt is able to
automatically grab things like AWS authentication keys for staging and inject
the settings into the runtime so blt can connect to the bucket. Pretty sweet!

## blt Grammar

blt has an opinionated command grammar and enforces a strict way of running
commands for tools. blt was designed to have a consistent run style so that no
matter what tool you are running commands for, it will have the same basic
format.  Let's break down the aws run from above:

         blt          e:staging     aws       .       sync_s3    /path/to/my/dir
          ^               ^          ^        ^          ^              ^
          |               |          |        |          |              |
          |               |          |        |          |              |

    blt executable   environment    tool   separator  command         args

## Installation

Currently blt is not on PyPI, so you'll need to build/install from the filesystem. Here are the steps to accomplish this:

#### Clone the blt rep

```bash
git clone git@github.com:pubvest/utils.git
```

#### Run the sdist directive on setup.py

```bash
cd utils/blt
python setup.py sdist
```

#### Install via pip

```bash
cd utils/blt/dist
pip install blt-VERSION.tar.gz
```

## More to come!

More documentaion/examples to come down the road!



