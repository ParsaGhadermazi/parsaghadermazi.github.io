---
title: Using TUIs for efficiently running large numbers of commands
date: 2025-01-01
---

![A TUI interface for running bioinformatics pipelines](img/bioplumber.gif){: .post-img-right width="280"}

Running lots and lots of commands on clusters or locally can be hard to manage
for many reasons. For example, if you're running a command 100 times in a loop
over your files, it will be hard to keep track of inputs and outputs of your
commands. Besides, documenting all the inputs and outputs should be done
manually which is a pain. I created a Python package based on an amazing Python
library called Textual to address these issues and make it easier to run CLI
commands at a large scale on remote servers. If you are interested in learning
more about it, check out the GitHub repository:
[pipit](https://github.com/ParsaGhadermazi/pipit).
