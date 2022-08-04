# holltwr
*holltwr* (/ˈhɔɬ.tur/, Welsh for *splitter*) is a command line utility for automated splitting of compact [Praat](https://www.fon.hum.uva.nl/praat/) TextGrid annotations into several separate tiers following a set annotation and conversion convention.

For instance, holltwr can take a TextGrid that only has a compact "manual" tier with an annotation such as "rexpcu-Researcher coughing" and split this across several tiers, e.g. a speaker tier showing "Researcher/Participant", a language tier showing "English/Welsh,Unknown" and comment tier showing "Researcher coughing". This can greatly speed up the work required to annotate an audio recording for basic categorial interval factors.

Imagine you have the following TextGrid in a file called 'compact.TextGrid', with a single Interval tier called 'manual':

|          |          |          |                |          |
|:--------:|:--------:|:--------:|:--------------:|----------|
| re       | rexpe    | pech      | rc-Truck noise | *manual* |

You now run *holltwr* on it using a command like this

```
holltwr split -c myconvention.json compact.TextGrid -d expanded.TextGrid
```

and get a file called 'expanded.TextGrid' with the following TextGrid:

|            |                          |                |            |               |
|:----------:|:------------------------:|:--------------:|:----------:|---------------|
| Researcher | Researcher / Participant | Participant    | Researcher | *speaker*     |
| English    | English / English        | English, Welsh | Welsh      | *language*    |
|            |                          | Hesitation     |            | *hesitation?* |
|            | Overlap                  |                |            | *overlap?*    |
|            |                          |                | Tuck noise | *comments*    |

You've saved a great deal of time by annotating everything with the compact "short hand" notation in the original annotation, but now have information nicely split and organised across a number of tiers which makes it much easier to inspect, analyse, and apply downstream tools to your TextGrid. That's holltwr!

Of course, the example given here is somewhat based on the original use case for which we wrote holltwr, which is the analysis of audio multilingual audio recordings with
several speakers and conditions, but you can equally well use this in many other scenarios, eg. by using a compact notation for intonational features, phonological constituency, etc. *holltwr* doesn't care about the meaning of what it does, it only really cares that a single symbol in compact annotations corresponds to a single value that can be filled in on other tiers with the same Interval boundaries.

## Usage

### The command-line interface

As you might already have gleaned from the example above, *holltwr* uses sub-commands to provide its functionality. You can always add the option `--help` at the end of any holltwr command to get more information on all the subcommands available, what they do, and what options they provide, e.g.

```
holltwr --help
```

### Basic usage pattern

The basic usage pattern of holltwr is as follows:

```
holltwr [OPTIONS] COMMAND [ARGS]...
```

Options start with `-` or `--`, e.g. `-c` or `--convention` specifies the convention file to use with `holltwr split`, and `--help` prints a help message.

### Configuring *holltwr*: `holltwr config`

The `config` command allows you to set some global configuration options for *holltwr*. 

Currently there is only one setting, namely that for a default convention file that *holltwr* should use unless specifically told to use a different one. This is handy as it can save much work typing with repeated uses, and will be used by `holltwr split` if the option `-c/--convention` is not supplied.

To set the default convention file, type

```
holltwr config default-convention FILENAME
```

Where *FILENAME* should be the path to a compact annotation convention in JSON format. *holltwr* will check that the annotation convention file can be loaded and conforms to the [JSON Schema](holltwr/conventions.schema.json) for convention files and then set it as its default. It's important that this file stays in the same place, because *holltwr* will remember where to find that file, rather than keeping its own copy somewhere.

To reset all settings (i.e. remove the default convention, if set) you can use the `reset` subcommand:

```
holltwr config reset
```

After running this, holltwr won't remember anything that was previously configured with `holltwr config`. Note that you will be prompted to confirm you want to reset all custom configuration -- you can confirm this before by adding the `--yes` option, i.e. calling `holltwr config reset --yes` will not prompt you but assume you're going to answer Yes to any prompt.

### Splitting compact TextGrid tiers: `holltwr split`

The brunt of *holltwr*'s functionality is its splitting function, which is invoked by `holltwr split`, with the following usage signature:

```
holltwr split [--help] [-c/--convention FILE] SOURCE... [-d/--destination FILE] [--yes]
```

The split command will split a compact annotation tier in one or more TextGrid files,specified by the *SOURCE* argument(s), following the specified annotation convention, in turn given either by the `-c/--convention` option or using a default convention which has been set globally for holltwr via `holltwr config default-convention`.

*SOURCE* can be either a single file name (e.g. `myfile.TextGrid`), a list of file names (e.g. `first.TextGrid second.TextGrid`), or a POSIX-compliant [glob pattern](https://en.wikipedia.org/wiki/Glob_(programming)), where `*` matches any string, `?` matches any single character, and `**` matches any directory including all of its subdirectories.
For example `*.TextGrid` will target all the files with the `.TextGrid` extension in the current working directory, `compact_?.TextGrid` will match `compact_a.TextGrid`, `compact_b.TextGrid` etc., and `data/**/*.TextGrid` will match all files with the `.TextGrid` extension located in any subdirectory of the `data/` directory.

By default, holltwr will overwrite the files in-situ, i.e. if given myfile.TextGrid as SOURCE, it will modify that file. The option `-d/--destination` allows this behaviour to be modified, with holltwr instead writing the result to a different file. The destination can be a single file name (e.g. `myupdatedfile.TextGrid`), a path to a directory (e.g.
`updated_files/` -- directory paths must end in `/` or `\`!), or a renaming pattern containing at most one `*`, which will be replaced with the relative path and name of the input file minus its file extension. For example, `holltwr split first.TextGrid second.TextGrid -d *_expanded.TextGrid` will write its output to the two files `first_expanded.TextGrid` and `second_expanded.TextGrid`).

Before holltwr modifies any files that already exist you will be prompted to confirm that you want to overwrite these files (this is because an annotation convention might include the instruction to remove the compact annotation tier, i.e. data could be lost). If you do not want to be prompted you can confirm that you are fine with this behaviour beforehand by specifying the option `--yes`.

### Validating files: `holltwr validate`

Because *holltwr* relies on files that will often be edited manually or by different tools, it's important to be able to check that these are valid (and to be able to see where the errors in them might be). This can be done with the `validate` command, which in turn provides two sub-commands:
* `holltwr validate convention FILENAME` validates a convention file. 
* `holltwr validate textgrid FILENAME` validates a TextGrid file.

These commands should be fairly self-explanatory and provide no other options (apart from `--help`). They will either tell you that a file seems to be valid, or otherwise will try to give as much information about what doesn't work as possible.

## License and copyright

*holltwr* was developed by Florian Breit for the Language Attitudes Research Team (LART) at Bangor University and is copyright (c) 2022 by Bangor University and Florian Breit.

The software is provided as free and open source under the terms of the [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0). You are welcome to use, modify and redistribute the software under the terms of that license, though of course it would be appreciated if you let us know and/or contribute back any improvements you make.

### License notice

```
Copyright 2022 Bangor University and Florian Breit

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

## Development and building

### Getting the source code

To obtain *holltwr*'s source code, either use `git clone` or download the ZIP archive from [holltwr's repository on GitHub](https://github.com/lart-bangor/holltwr).

To clone the git repository, you can use the following command:
```
git clone https://github.com/lart-bangor/holltwr.git
```

### Setting up the development environment

Because *holltwr* is written in [Python](https://python.org), you obviously need a Python installation on your system. If you want to contribute code you also need to have [Git](https://git-scm.com) installed. We're using **Python 3.10** for development, and 3.10 or newer is recommended, however you should be okay with Python 3.9 or newer (for now).

All the remaining development dependencies are managed via [pipenv](https://pypi.org/project/pipenv/). To install pipenv just run the following command (use `pip3` instead of `pip` if you're on Linux/Unix):
```
pip install pipenv
```

After installing pipenv, just go to the source directory (the one containing this 'README.md' and the 'holltwr.py' files) and run the following command:
```
pipenv install --dev
```

This will install all the current Python packages needed both for holltwr's development and distribution. If you add packages use `pipenv install PACKAGE_NAME` (oor `pipenv install --dev PACKAGE_NAME` if it is a development-only dependency).

**Important:** For any work on holltwr, you should always remember to first activate pipenv's virtual environment by running `pipenv shell` before doing anything else. If you get any errors because of missing packages/modules/dependencies, always double check that the pipenv virtual environment is active first.

### Running holltwr from source

While you can just run the 'holltwr.py' script (which is a simple wrapper for the *holltwr* package to facilitate building with Nuitka), it is recommended that you use Python's module invocation instead. The reason is that this ensures that *holltwr* doesn't inadvertedly become corrupted in a way that makes it unusable as a Python source-distributed package.

Thus, the recommended way to run *holltwr* as a source package is:
```
python -m holltwr
```

### Building a binary

*holltwr* uses [Nuitka](https://nuitka.net/) to build its binaries. This should have been automatically installed when setting up the development environment with `pipenv install --dev`. However, it might be possible that you have to install a compatible C compiler if Nuitka cannot find one on your system (Nuitka will prompt you if this is the case).

To build the excutable binary go to the source directory (the one containing 'holltwr.py') and run the following command:

```
nuitka holltwr.py --follow-imports --include-package-data=jschon --include-package-data=holltwr --show-progress --onefile
```

This should give you a standalone binary called 'holltwr.exe' on Windows, and 'holltwr.bin' or similar on other systems. It may also create two directories ('holltwr.build' and 'holltwr.dist') with artifacts from the build process. You can delete these after Nuitka has finished running.

## To Do
This is a brief list of planned and upcoming improvements to *holltwr*. If you want to contribute to any of these please do get in touch, help will certainly be appreciated.

* Implement TextGrid file validation
* Implement all convention schema options
* Add a convention option for merging adjacent identical Interval annotations
* Write instructions for writing custom annotation conventions
* Package and distribute via PyPI
* Source documentation / sphinx API docs
