# Prototype

A static site generator.

## Features:
- Jinja Templates
- Sass
- Localization
- JSON Data

## Installation

	$ python setup.py install

## Quickstart

Once the application is installed, you can create as many email projects as you like using `-i <project-name>`.

	$ prototype -i new-email-project

When you want to work on your project, start the webserver. Sass is compiled automatically when the server is running.

	$ cd new-email-project/
	$ prototype
	now serving on port 2000...

You can specify port using `-p` or `--port`

	$ prototype -p 4567
	now serving on port 4567...

## Using JSON Data

JSON files can be added to the data folder and will be automatically available to the templates in the `{{ data }}` variable. For example if you add a file called `things.json`, you can access it like this:

    {{ data['things.json'] }}

## Localizing Emails

Emails can be translated into any language following the gettext protocol. Languages specified in the configuration will be build to their own directories upon build. If you have 10 emails, and 10 languages, instead of managing 100 files you still just manage the 10. 

To create a new language, add it to `config.json`, then run `prototype --gettext`. Then populate the new mo files with the correct translations, and run `prototype --gettext` again to compile the po files. The gettext command will retrieve new translation strings without harming your existing translations. Its used to both create new languages and compile po files after adding new translations.

## Assets

Although you can link directly to assets using relative or absolute paths, you should use the `{{ assets() }}` function.

## Building

Static files are compiled and saved to the build directory by using `-b` or `--build`. 

	$ prototype --build
