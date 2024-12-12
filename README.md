Torch OWL (towl)
=================

Torch OWL is a tool for tracing memory allocations with PyTorch and Intel® Gaudi® AI accelerators.

The project contains the following Python subpackages:

* `towl-db` - Database interface that contains database definition and procedures to build one from collected traces.
* `towl-user` - End user interface that can be used with Jupyter notebook. Requires `towl-db`.
* `towl-instrument` - Instrumentation that contains various helpers to instrument topology and gather more data during runtime. It is a minimal dependency package that helps to prevent errors in your runtime environment.

We are currently in the early stages of developing the tool and expect to make significant changes to improve its usability in the near future.

## Instaling Packages from Sources

To install packages from a source, run `pip install .` in an suitable directory.

For example:

```
cd towl-user
pip install .
```

A helper for the `towl-db` and `towl-user` packages installation is located inside `Makefile`.

## Building Wheel Packages

You can build wheel packages using `poetry` Python build system. 
A helper for running build process on every Python subpackage is located inside `Makefile`.

For example:

```
make build
```

## Building API Documentation

You can build API documentation using pdoc3.
A helper for running build process on every Python subpackage is located inside `Makefile`.

For example:

```
make docs
```

## Usage and Examples

Refer to `examples/00_introduction` notebook.


## Comming Soon

Documentation updates and tool enhancements.
