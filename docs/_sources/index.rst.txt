Smokestack
==========

**Smokestack** is a Python framework for deploying Amazon Web Services CloudFormation stacks.

- Supports template files (YAML or JSON) or any template generator (i.e. Troposphere).
- Renders beautiful execution previews.
- Execute or preview in CI based on branch name.
- Deploys stacks in parallel, with dependencies described per-stack.
- Makes your infrastructure-as-code deployable via the command line.

Requirements
------------

Smokestack requires Python 3.8 or later.

Installation
------------

.. code-block:: console

   pip install smokestack

Contents
--------

.. toctree::
   :maxdepth: 1

   self
   usage/index
   cli
