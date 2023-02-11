# komputor
Python version of an abstract computer emulation

Implementation of an opcode driven primitive general purpose computing environment.

A research into simplified basic computer architecture, outlined in a coursebook on
machine-level programming.

A primitive "source code" input is translated into opcodes, later machine instructions
with literal, indirect and indexed memory addressing, and sequenced into "execution pipeline".

The translation divides the code into DATA and CODE sections, and executes the code.

The purpose of the implementation is to allow exercises in machine-level programming contained
in the aforementioned coursebook to be executed on a real machine, along with studying the
possibility of defining a higher level language.

## Multi-language nature

The source code is distributed with several programming language implementations in
a single repository (subject to later refinement). Currently, Python and C are the focus,
with some helper scripts written in Windows Command and Tcl.

## Further goals

A GUI interface is envisioned in the future, as well as implementing "graphical output devices",
and other peripherals, as well as possible exploration of distributed computing, and everything else that modern
language runtimes provide, but implemented as "hardware" emulations, to stay close to
"machine-level" philosophy.

Sounds nice on paper, doesn't it?

