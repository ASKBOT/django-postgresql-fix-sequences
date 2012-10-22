"""management command that helps to fix sequences
in the postgresql"""
import sys
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from optparse import make_option
from postgresql_sequence_utils.utils import Database
from postgresql_sequence_utils.utils import validate_options
from postgresql_sequence_utils.utils import print_info
from postgresql_sequence_utils.utils import get_table_names
from postgresql_sequence_utils.utils import get_broken_sequence_info

class Command(BaseCommand):
    help = "Helps to fix sequences in postgresql"

    option_list = BaseCommand.option_list + (
                make_option('--auto',
                    action='store_true',
                    dest='auto',
                    default=False,
                    help='try to automatically determine sequence increment'
                ),
                make_option('--minvalue',
                    action='store',
                    dest='minvalue',
                    type='int',
                    default=None,
                    help='minimum value for the sequence (integer)'
                ),
                make_option('--increment',
                    action='store',
                    dest='increment',
                    type='int',
                    default=1,
                    help='sequence increment (integer)'
                ),
                make_option('--tables',
                    action='store',
                    dest='tables',
                    type='string',
                    default=None,
                    help='comma-separated list of database table names'
                ),
                make_option('--dry-run',
                    action='store_true',
                    dest='dry_run',
                    default=False,
                    help='show only list of tables with broken sequences'
                ),
                make_option('--database-alias',
                    action='store',
                    dest='database_alias',
                    default='default',
                    help='database alias, default value "default"'
                )
            )

    def handle(self, *args, **options):
        """the command handler function"""
        validate_options(options)

        tables = get_table_names(options)

        database = Database(options['database_alias'])

        for table in tables:
            if not database.table_exists(table):
                raise CommandError('table %s does not exist' % table)

        filtered_tables = list()
        #a limitation - only work on sequences ending with <table_name>_id_seq
        for table in tables:
            if database.table_has_sequence(table, '%s_id_seq'):
                filtered_tables.append(table)

        tables = filtered_tables

        sequence_info = database.get_sequence_info(tables, options)

        for table, info in sequence_info.items():
            if info['broken'] and options['dry_run'] is False:
                database.set_current_sequence_value(table, info['max_value'])

        broken_sequence_info = get_broken_sequence_info(sequence_info)
        if options['verbosity'] > 0 and len(broken_sequence_info):
            if options['dry_run']:
                print 'Broken sequences:'
            else:
                print 'Following sequences were fixed:'
            print_info(broken_sequence_info)

        if len(broken_sequence_info):
            sys.exit(1)
        return
