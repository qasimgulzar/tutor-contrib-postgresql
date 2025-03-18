import os
from glob import glob

import click
import importlib_resources
from tutor import hooks

from .__about__ import __version__

########################################
# CONFIGURATION
########################################
config = {
    "defaults": {
        "VERSION": __version__,
        "IMAGE": "postgres:14-alpine",
        "HOST": "postgresql",
        "PORT": 5432,
        "ROOT_USER": "openedx",
        "OPENEDX_DB": "openedx",
        "OPENEDX_USER": "openedx",
    },
    "overrides": {
        #  Running MYSQL in parallel with PostgreSQL for development.
        # "RUN_POSTGRESQL": False # Disable PostgreSQL
        # "RUN_MYSQL": False # Disable MySQL
    },
    "unique": {
        "ROOT_PASSWORD": "{{ 8|random_string }}",
        "OPENEDX_PASSWORD": "{{ 8|random_string }}",
    },
}

hooks.Filters.CONFIG_DEFAULTS.add_items(
    [
        # Add your new settings that have default values here.
        # Each new setting is a pair: (setting_name, default_value).
        # Prefix your setting names with 'POSTGRESQL_'.
        ("RUN_POSTGRESQL", True),
        *[
            (f"POSTGRESQL_{key}", value)
            for key, value in config.get("defaults", {}).items()
        ],
    ]
)

hooks.Filters.CONFIG_UNIQUE.add_items(
    [
        # Add settings that don't have a reasonable default for all users here.
        # For instance: passwords, secret keys, etc.
        # Each new setting is a pair: (setting_name, unique_generated_value).
        # Prefix your setting names with 'POSTGRESQL_'.
        # For example:
        *[
            (f"POSTGRESQL_{key}", value)
            for key, value in config.get("unique", {}).items()
        ]
    ]
)

hooks.Filters.CONFIG_OVERRIDES.add_items(
    [
        # Danger zone!
        # Add values to override settings from Tutor core or other plugins here.
        # Each override is a pair: (setting_name, new_value). For example:
        *list(config.get("overrides", {}).items())
    ]
)

########################################
# INITIALIZATION TASKS
########################################

# To add a custom initialization task, create a bash script template under:
# tutorpostgresql/templates/postgresql/tasks/
# and then add it to the MY_INIT_TASKS list. Each task is in the format:
# ("<service>", ("<path>", "<to>", "<script>", "<template>"))
MY_INIT_TASKS: list[tuple[str, tuple[str, ...]]] = [
    # For example, to add LMS initialization steps, you could add the script template at:
    # tutorpostgresql/templates/postgresql/tasks/lms/init.sh
    # And then add the line:
    ### ("lms", ("postgresql", "tasks", "lms", "init.sh")),
    ("postgresql", ("postgresql", "tasks", "postgresql", "init")),
]

# For each task added to MY_INIT_TASKS, we load the task template
# and add it to the CLI_DO_INIT_TASKS filter, which tells Tutor to
# run it as part of the `init` job.
for service, template_path in MY_INIT_TASKS:
    full_path: str = str(
        importlib_resources.files("tutorpostgresql")
        / os.path.join("templates", *template_path)
    )
    with open(full_path, encoding="utf-8") as init_task_file:
        init_task: str = init_task_file.read()
    # Raise the priority of the init job so that the DB is initialized before the migrations are applied
    hooks.Filters.CLI_DO_INIT_TASKS.add_item((service, init_task), priority=hooks.priorities.HIGH)

########################################
# DOCKER IMAGE MANAGEMENT
########################################


# Images to be built by `tutor images build`.
# Each item is a quadruple in the form:
#     ("<tutor_image_name>", ("path", "to", "build", "dir"), "<docker_image_tag>", "<build_args>")
hooks.Filters.IMAGES_BUILD.add_items(
    [
        # To build `myimage` with `tutor images build myimage`,
        # you would add a Dockerfile to templates/postgresql/build/myimage,
        # and then write:
        ### (
        ###     "myimage",
        ###     ("plugins", "postgresql", "build", "myimage"),
        ###     "docker.io/myimage:{{ POSTGRESQL_VERSION }}",
        ###     (),
        ### ),
    ]
)

# Images to be pulled as part of `tutor images pull`.
# Each item is a pair in the form:
#     ("<tutor_image_name>", "<docker_image_tag>")
hooks.Filters.IMAGES_PULL.add_items(
    [
        # To pull `myimage` with `tutor images pull myimage`, you would write:
        ### (
        ###     "myimage",
        ###     "docker.io/myimage:{{ POSTGRESQL_VERSION }}",
        ### ),
    ]
)

# Images to be pushed as part of `tutor images push`.
# Each item is a pair in the form:
#     ("<tutor_image_name>", "<docker_image_tag>")
hooks.Filters.IMAGES_PUSH.add_items(
    [
        # To push `myimage` with `tutor images push myimage`, you would write:
        ### (
        ###     "myimage",
        ###     "docker.io/myimage:{{ POSTGRESQL_VERSION }}",
        ### ),
    ]
)

########################################
# TEMPLATE RENDERING
# (It is safe & recommended to leave
#  this section as-is :)
########################################

hooks.Filters.ENV_TEMPLATE_ROOTS.add_items(
    # Root paths for template files, relative to the project root.
    [
        str(importlib_resources.files("tutorpostgresql") / "templates"),
    ]
)

hooks.Filters.ENV_TEMPLATE_TARGETS.add_items(
    # For each pair (source_path, destination_path):
    # templates at ``source_path`` (relative to your ENV_TEMPLATE_ROOTS) will be
    # rendered to ``source_path/destination_path`` (relative to your Tutor environment).
    # For example, ``tutorpostgresql/templates/postgresql/build``
    # will be rendered to ``$(tutor config printroot)/env/plugins/postgresql/build``.
    [
        ("postgresql/build", "plugins"),
        ("postgresql/apps", "plugins"),
    ],
)

########################################
# PATCH LOADING
# (It is safe & recommended to leave
#  this section as-is :)
########################################

# For each file in tutorpostgresql/patches,
# apply a patch based on the file's name and contents.
for path in glob(str(importlib_resources.files("tutorpostgresql") / "patches" / "*")):
    with open(path, encoding="utf-8") as patch_file:
        hooks.Filters.ENV_PATCHES.add_item((os.path.basename(path), patch_file.read()))

########################################
# CUSTOM JOBS (a.k.a. "do-commands")
########################################

# A job is a set of tasks, each of which run inside a certain container.
# Jobs are invoked using the `do` command, for example: `tutor local do importdemocourse`.
# A few jobs are built in to Tutor, such as `init` and `createuser`.
# You can also add your own custom jobs:


# To add a custom job, define a Click command that returns a list of tasks,
# where each task is a pair in the form ("<service>", "<shell_command>").
# For example:
### @click.command()
### @click.option("-n", "--name", default="plugin developer")
### def say_hi(name: str) -> list[tuple[str, str]]:
###     """
###     An example job that just prints 'hello' from within both LMS and CMS.
###     """
###     return [
###         ("lms", f"echo 'Hello from LMS, {name}!'"),
###         ("cms", f"echo 'Hello from CMS, {name}!'"),
###     ]


# Then, add the command function to CLI_DO_COMMANDS:
## hooks.Filters.CLI_DO_COMMANDS.add_item(say_hi)

# Now, you can run your job like this:
#   $ tutor local do say-hi --name="Qasim Gulzar"


#######################################
# CUSTOM CLI COMMANDS
#######################################

# Your plugin can also add custom commands directly to the Tutor CLI.
# These commands are run directly on the user's host computer
# (unlike jobs, which are run in containers).

# To define a command group for your plugin, you would define a Click
# group and then add it to CLI_COMMANDS:


### @click.group()
### def postgresql() -> None:
###     pass


### hooks.Filters.CLI_COMMANDS.add_item(postgresql)


# Then, you would add subcommands directly to the Click group, for example:


### @postgresql.command()
### def example_command() -> None:
###     """
###     This is helptext for an example command.
###     """
###     print("You've run an example command.")


# This would allow you to run:
#   $ tutor postgresql example-command
