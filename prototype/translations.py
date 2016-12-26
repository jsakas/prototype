from babel.messages.pofile import write_po, read_po
from babel.messages.mofile import write_mo
from babel.messages.extract import extract_from_dir, extract_from_file
from babel.messages.catalog import Catalog

import os, sys, json


class TranslationManager(object):
    def __init__(self):
        self.project_path = os.getcwd()
        self.source_path = os.path.join(self.project_path,'source')

        try:
            config_path = os.path.join(self.project_path,'config.json')
            config = open(config_path, 'r')
            self.config = json.load(config)
        except Exception as e:
            print('Fatal Error: config.json missing or corrupt.')
            raise

        self.translations_path = os.path.join(self.project_path, self.config.get('translations', ''))
        self.translations_key = self.config.get('translations_key', '')

    def init_catalog(self, language):
        """
        initialize a new catalog, only one catalog is managed at a time
        """
        print('initializing catalog with language {}...'.format(language))

        self.language = language
        self.catalog = Catalog(
            project = self.config.get('name', 'PROJECT NAME'),
            version = self.config.get('version', 'PROJECT VERSION'),
            copyright_holder = self.config.get('copyright_holder', ''),
            language_team = self.config.get('author', ''),
        )

    def build_catalog(self):
        """
        build catalog off of existing PO files
        """
        print('building catalog off of existing translations in PO file...')
        po_path = os.path.join(self.translations_path, self.language, 'LC_MESSAGES', self.translations_key + '.po')
        try:
            file = open(po_path, 'r+')
        except IOError as e:
            # po file doesn't exist, create a blank file
            if not os.path.exists(os.path.dirname(po_path)):
                os.makedirs(os.path.dirname(po_path))
            file = open(po_path, 'w+')
        catalog =  read_po(file)
        for message in catalog:
            if message.id:
                self.catalog.add(message.id, message.string)
        return


    def update_catalog(self):
        """
        open each file in the source directory, extract translations, and update the catalog
        """
        print('updating catalog with new translations found in templates...')

        keywords = {
            '_': None
        }
        for path, folders, files in os.walk(self.source_path):
            for file in files:
                if file.endswith(tuple(self.config.get('template_extensions'))):
                    extract_path = os.path.join(path, file)
                    for translation in extract_from_file('jinja2', extract_path, keywords):
                        self.catalog.add(translation[1])
        return
        

    def write_po_file(self):
        """
        write to PO file for each language specified in the config
        """
        print('updating PO file...')

        po_path = os.path.join(self.translations_path, self.language, 'LC_MESSAGES', self.translations_key + '.po')
        file = open(po_path, 'w')
        write_po(file, self.catalog)
        return

    def write_mo_file(self):
        """
        write MO files from existing PO files
        """
        print('updating MO file...')

        po_path = os.path.join(self.translations_path, self.language, 'LC_MESSAGES', self.translations_key + '.po')
        po_file = open(po_path, 'r+')
        catalog =  read_po(po_file)

        mo_path = os.path.join(self.translations_path, self.language, 'LC_MESSAGES', self.translations_key + '.mo')
        mo_file = open(mo_path, 'w+')
        write_mo(mo_file, catalog)
        return

    def run(self):
        for language in self.config.get('languages', []):
            self.init_catalog(language)
            self.build_catalog()
            self.update_catalog()
            self.write_po_file()
            self.write_mo_file()
            print('...done.')

if __name__ == "__main__":
    translation_manager = TranslationManager()
    translation_manager.run()
