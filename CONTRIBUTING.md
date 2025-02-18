# Contributing to Textual

First of all, thanks for taking the time to contribute to Textual!

## How can I contribute?

You can contribute to Textual in many ways:

 1. [Report a bug](https://github.com/textualize/textual/issues/new?title=%5BBUG%5D%20short%20bug%20description&template=bug_report.md)
 2. Add a new feature
 3. Fix a bug
 4. Improve the documentation


## Setup

To make a code or documentation contribution you will need to set up Textual locally.
You can follow these steps:

 1. Make sure you have Poetry installed ([see instructions here](https://python-poetry.org))
 2. Clone the Textual repository
 3. Run `cd textual` to make textual your current working directory
 4. Run `python -m venv .venv` to create a new python virtual environment
 5. Run `source .venv/bin/activate` to activate the virtual environment
 6. Run `python -m pip install poetry` to install poetry
 7. Run `make setup` to install all dependencies
 8. Make sure the latest version of Textual was installed by running the command `textual --version`
 9. Install the pre-commit hooks with the command `pre-commit install`

([Read this](#makefile-commands) if the command `make` doesn't work for you.)

## Demo

Once you have Textual installed, run the Textual demo to get an impression of what Textual can do and to double check that everything was installed correctly:

```bash
python -m textual
```

## Guidelines

- Read any issue instructions carefully. Feel free to ask for clarification if any details are missing.

- Add docstrings to all of your code (functions, methods, classes, ...). The codebase should have enough examples for you to copy from.

- Write tests for your code.
  - If you are fixing a bug, make sure to add regression tests that link to the original issue.
  - If you are implementing a visual element, make sure to add _snapshot tests_. [See below](#snapshot-testing) for more details.

## Before opening a PR

Before you open your PR, please go through this checklist and make sure you've checked all the items that apply:

 - [ ] Update the `CHANGELOG.md`
 - [ ] Format your code with black (`make format`)
 - [ ] All your code has docstrings in the style of the rest of the codebase
 - [ ] Your code passes all tests (`make test`)

([Read this](#makefile-commands) if the command `make` doesn't work for you.)

## Updating and building the documentation

If you change the documentation, you will want to build the documentation to make sure everything looks like it should.
The command `make docs-serve-offline` should start a server that will let you preview the documentation locally and that should reload whenever you save changes to the documentation or the code files.

([Read this](#makefile-commands) if the command `make` doesn't work for you.)

We strive to write our documentation in a clear and accessible way so, if you find any issues with the documentation, we encourage you to open an issue where you can enumerate the things you think should be changed or added.

Opening an issue or a discussion is typically better than opening a PR directly.
That's because there are many subjective considerations that go into writing documentation and we cannot expect you, a well-intentioned external contributor, to be aware of those subjective considerations that we take into account when writing our documentation.

Of course, this does not apply to objective/technical issues with the documentation like bugs or broken links.

## After opening a PR

When you open a PR, your code will be reviewed by one of the Textual maintainers.
In that review process,

- We will take a look at all of the changes you are making
- We might ask for clarifications (why did you do X or Y?)
- We might ask for more tests/more documentation
- We might ask for some code changes

The sole purpose of those interactions is to make sure that, in the long run, everyone has the best experience possible with Textual and with the feature you are implementing/fixing.

Don't be discouraged if a reviewer asks for code changes.
If you go through our history of pull requests, you will see that every single one of the maintainers has had to make changes following a review.

## Snapshot testing

Snapshot tests ensure that visual things (like widgets) look like they are supposed to.
PR [#1969](https://github.com/Textualize/textual/pull/1969) is a good example of what adding snapshot tests looks like: it amounts to a change in the file `tests/snapshot_tests/test_snapshots.py` that should run an app that you write and compare it against a historic snapshot of what that app should look like.

When you create a new snapshot test, run it with `pytest -vv tests/snapshot_tests/test_snapshots.py`.
Because you just created this snapshot test, there is no history to compare against and the test will fail.
After running the snapshot tests, you should see a link that opens an interface in your browser.
This interface should show all failing snapshot tests and a side-by-side diff between what the app looked like when the test ran versus the historic snapshot.

Make sure your snapshot app looks like it is supposed to and that you didn't break any other snapshot tests.
If everything looks fine, you can run `make test-snapshot-update` to update the snapshot history with your new snapshot.
This will write a new SVG file to the `tests/snapshot_tests/__snapshots__/` directory.
You should NOT modify these files by hand.
If a pre-existing snapshot tests fails, you should carefully inspect the diff and decide if the new snapshot is correct or if the pre-existing one is.
If the new snapshot is correct, you should update the snapshot history with your new snapshot using `make test-snapshot-update`.
If the pre-existing snapshot is correct, your change has likely introduced a bug, and you should try to fix it.
After fixing it, and checking the output of `make test-snapshot` now looks correct, you should run `make test-snapshot-update` to update the snapshot history with your new snapshot.


([Read this](#makefile-commands) if the command `make` doesn't work for you.)

## Join the community

Seems a little overwhelming?
Join our community on [Discord](https://discord.gg/Enf6Z3qhVr) to get help!

## Makefile commands

Textual has a `Makefile` file that contains the most common commands used when developing Textual.
([Read about Make and makefiles on Wikipedia.](https://en.wikipedia.org/wiki/Make_(software)))
If you don't have Make and you're on Windows, you may want to [install Make](https://stackoverflow.com/q/32127524/2828287).
