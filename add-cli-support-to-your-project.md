# 💻 Add CLI support to your project

`smokestack` allows you to make your stacks deployable from the command line.

For example, with a few lines of code, `smokestack` can allow your users to preview and deploy a change by running:

```bash
your-app --stack your-stack --preview --deploy
```

In this example, we assume that your project is called "foo".

### Setup

#### 1. Stub `__main__.py`

Stub `__main__.py` in the root of your package.

```python
def cli_entry() -> None:
    pass

if __name__ == "__main__":
    cli_entry()
```

#### 2. Describe your host application

Import `Host` from `smokestack.cli` and describe your host application.

```python
from smokestack.cli import Host

from foo import get_version()


def cli_entry() -> None:
    host = Host(
        name="foo",
        version=get_version(),
    )

if __name__ == "__main__":
    cli_entry()
```

#### 3. Construct a CLI invocation request

Import `Request` from `smokestack.cli` and describe the stacks available for deployment:

```python
from smokestack.cli import Host, Request

from foo import get_version()
from foo.stacks import StackA, StackB, StackC


def cli_entry() -> None:
    host = Host(
        name="foo",
        version=get_version(),
    )

    request = Request(
        host=host,
        stacks={
            "stack-a": StackA,
            "stack-b": StackB,
            "stack-c": StackC,
        },
    )


if __name__ == "__main__":
    cli_entry()
```

#### 4. Invoke the request

Import `invoke_then_exit` from `smokestack.cli` and pass in the request:

```python
from smokestack.cli import Host, Request, invoke_then_exit

from foo import get_version()
from foo.stacks import StackA, StackB, StackC


def cli_entry() -> None:
    host = Host(
        name="foo",
        version="1.0.0",
    )

    request = Request(
        host=host,
        stacks={
            "deployer": DeployerStack,
        },
    )

    invoke_then_exit(request)


if __name__ == "__main__":
    cli_entry()
```

### Usage

In this example, we assume that your Python application is called "foo".

If your application has been installed as a package then run:

```bash
foo --help
```

To run the code in your development directory:

```bash
python -m foo --help
```

A help page with usage information will be printed.

Your options include:

* `--stack ID`: the stack to preview and/or deploy
* `--deploy`: deploy the specified stack
* `--preview`: preview the specified stack
