"""utilities used in the postgresql_fix_sequences management command"""
from django.core.management.base import CommandError
from django.conf import settings
from django.db import connections
from django.db import models

def get_broken_sequence_info(sequence_info):
    """filter info for broken tables"""
    info = dict()
    for table, table_info in sequence_info.items():
        if table_info['broken']:
            info[table] = table_info
    return info

def parse_table_names(value):
    return map(lambda v: v.strip, value.split(','))

def validate_options(options):
    """raises :class:`CommandError` when options are invalid"""
    if not (bool(options['minvalue']) ^ options['auto']):
        raise CommandError('please either use --auto or --minvalue')

    if options['auto'] is False:
        if options['minvalue'] < 1:
            raise CommandError('--minvalue must be a positive integer')

        if options['increment'] < 1:
            raise CommandError('--increment must be a positive integer')

    if options['tables']:
        tables = parse_table_names(options['tables'])
        for table in tables:
            if ';' in table:
                raise CommandError('table name %s is invalid' % table)
                

def get_table_names(options):
    if options['tables']:
        return parse_table_names(options['tables'])
    else:
        return map(lambda v: v._meta.db_table, models.get_models())

def print_info(sequence_info):
    """prints out the sequence data"""
    format_str = "%-10s%-10s%-10s %s"
    print format_str % ('Current', 'Maximum', 'Increment', 'Table name')
    for table, info in sequence_info.values():
        print format_str % (
                    info['current_value'],
                    info['max_value'],
                    info['increment'],
                    table
                )

class Database(object):
    """A class in charge of the database queries"""

    def __init__(self, database_alias='default'):
        self.cursor = connections[database_alias].cursor()
        self.database_alias = database_alias

    def get_sequence_info(self, tables, options):
        """returns information about tables as
        dictionary of dictionaries first key table name
        keys of subdictionary:
        min_value, increment, max_value, current_value, broken
        """
        sequence_info = dict()
        for table in tables:
            #to initialize the sequence calls we need to call the
            #nextval() once, later we will reset the previous value
            first_value = self.get_next_sequence_value(table)

            if options['auto']:
                min_value, increment = self.guess_sequence_parameters(table)
            else:
                min_value, increment = options['minvalue'], options['increment']

            max_value = self.get_largest_sequence_row_id(
                                    table, min_value, increment
                                )
            if first_value > 1:
                self.set_current_sequence_value(table, first_value - increment)
            current_value = self.get_current_sequence_value(table)

            sequence_info[table] = {
                'min_value': min_value,
                'increment': increment,
                'max_value': max_value,
                'current_value': current_value,
                'broken': current_value < max_value
            }
        return sequence_info

    def get_single_value(self, query):
        self.cursor.execute(query)
        return self.cursor.fetchone()[0]

    def get_database_name(self):
        return settings.DATABASES[self.database_alias]['NAME']

    def table_exists(self, table):
        """True if table exists in the database"""
        db_name = self.get_database_name()
        query = """SELECT EXISTS (SELECT 1 FROM information_schema.tables 
        WHERE table_catalog='%s' AND table_schema='public' 
        AND table_name='%s')""" % (db_name, table)
        return self.get_single_value(query)

    def table_has_sequence(self, table, format_string):
        """True, if sequence with name format_string % table exists"""
        seq_name = format_string % table
        query = """SELECT EXISTS (SELECT 1 FROM pg_class 
        WHERE upper(relkind)='S' AND relname='%s')""" % seq_name
        return self.get_single_value(query)

    def get_next_sequence_value(self, table):
        return self.get_single_value("select nextval('%s_id_seq')" % table)

    def get_current_sequence_value(self, table):
        return self.get_single_value("select currval('%s_id_seq')" % table)

    def set_current_sequence_value(self, table, value):
        self.cursor.execute(
            "select setval('%s_id_seq', %d, True)" % (table, value)
        )

    def guess_sequence_parameters(self, table):
        """returns some reference value for the sequence
        and the increment"""
        prev_val = self.get_current_sequence_value(table)
        next_val = self.get_next_sequence_value(table)
        increment = next_val - prev_val
        self.set_current_sequence_value(table, prev_val)#reset the value
        return next_val, increment

    def get_largest_sequence_row_id(self, table, min_value, increment):
        query = """SELECT id FROM %s WHERE mod(id, %d)=%d 
        ORDER BY id DESC LIMIT 1""" % (table, increment, min_value % increment)
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        if result is None:
            return 0
        else:
            return result[0]
