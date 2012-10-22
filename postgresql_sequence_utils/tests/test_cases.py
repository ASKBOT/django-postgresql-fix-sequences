from django.db.models import loading
from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from postgresql_sequence_utils.utils import Database
from postgresql_sequence_utils.tests.testapp.models import TestModel
import copy

class Tests(TestCase):

    def _pre_setup(self):
        self._backup = copy.copy(settings.INSTALLED_APPS)
        settings.INSTALLED_APPS += ('postgresql_sequence_utils.tests.testapp',)
        loading.cache.loaded = False
        call_command('syncdb', verbosity=0, interactive=False, migrate=False)
        super(Tests, self)._pre_setup()

    def _post_teardown(self):
        super(Tests, self)._post_teardown()
        settings.INSTALLED_APPS = self._backup
        loading.cache.loaded = False

    def setUp(self):
        self.database = Database()

    def execute(self, query):
        return self.database.cursor.execute(query);
    
    def test_table_exists(self):
        db = self.database
        self.assertEqual(db.table_exists('blah'), False)
        self.execute('CREATE TABLE blah (id integer)')
        self.assertEqual(db.table_exists('blah'), True)

    def test_get_largest_sequence_row_id(self):
        table_name = TestModel._meta.db_table
        last_id = self.database.get_largest_sequence_row_id(
                                table_name, 1, 1
                            )
        self.assertEqual(last_id, 0)

        one = TestModel.objects.create(text='hahahaha')
        two = TestModel.objects.create(text='hahahaha')
        three = TestModel.objects.create(text='hahahaha')
        last_id = self.database.get_largest_sequence_row_id(
                                table_name, one.id, 1
                            )
        self.assertEqual(three.id, last_id)

        last_id = self.database.get_largest_sequence_row_id(
                                table_name, two.id, 2
                            )
        self.assertEqual(two.id, last_id)

        last_id = self.database.get_largest_sequence_row_id(
                                table_name, one.id, 3
                            )
        self.assertEqual(one.id, last_id)

    def test_guess_sequence_value(self):
        item = TestModel.objects.create(text='uhahahahuhuh')
        query = 'ALTER SEQUENCE %s_id_seq INCREMENT BY 3 START WITH 1'
        table = TestModel._meta.db_table
        self.execute(query % table)
        result = self.database.guess_sequence_parameters(table)
        self.assertEqual(result[1], 3)
        current = self.database.get_current_sequence_value(table)
        self.assertEqual(current, item.id)

    def test_get_current_sequence_value(self):
        self.database.get_next_sequence_value(
                                        TestModel._meta.db_table
                                    )
        current = self.database.get_current_sequence_value(
                                        TestModel._meta.db_table
                                    )
        self.assertEqual(current, 1)
        one = TestModel.objects.create(text='hhahahaha')
        two = TestModel.objects.create(text='uhoohhaauo')
        current = self.database.get_current_sequence_value(
                                        TestModel._meta.db_table
                                    )
        self.assertEqual(current, 3)

    def test_set_current_sequence_value(self):
        #this call is to initialize the sequence in the session
        self.database.get_next_sequence_value(
                                        TestModel._meta.db_table
                                    )
        self.database.set_current_sequence_value(
                                        TestModel._meta.db_table,
                                        10
                                    )
        current = self.database.get_current_sequence_value(
                                        TestModel._meta.db_table
                                    )
        self.assertEqual(current, 10)

    def test_get_sequence_info(self):
        item = None
        for i in xrange(10):
            item = TestModel.objects.create(text='uaouaou')

        self.database.set_current_sequence_value(
                                        TestModel._meta.db_table,
                                        1
                                    )

        tables = [TestModel._meta.db_table]
        info_dict = self.database.get_sequence_info(tables, {'auto': True})
        info = info_dict[tables[0]]
        self.assertEqual(info['max_value'], item.id)
        self.assertEqual(info['current_value'], 1)
        self.assertEqual(info['broken'], True)

    def test_table_has_sequence(self):
        query = 'CREATE TABLE blah (text TEXT)'
        self.execute(query)
        self.assertEqual(
            self.database.table_has_sequence('blah', '%s_id_seq'),
            False
        )
        table = TestModel._meta.db_table
        self.assertEqual(
            self.database.table_has_sequence(table, '%s_id_seq'),
            True
        )

    def test_postgresql_fix_sequences(self):
        item = None
        for i in xrange(10):
            item = TestModel.objects.create(text='uaouoauoauau')

        first_item = TestModel.objects.all().order_by('id')[0]
        self.database.set_current_sequence_value(
                                TestModel._meta.db_table,
                                first_item.id
                            )

        #see that sequence is broken
        tables = [TestModel._meta.db_table]
        info_dict = self.database.get_sequence_info(tables, {'auto': True})
        info = info_dict[tables[0]]
        self.assertEqual(info['max_value'], item.id)
        self.assertEqual(info['current_value'], first_item.id)
        self.assertEqual(info['broken'], True)

        self.assertRaises(
            SystemExit,
            call_command,
            'postgresql_fix_sequences',
            auto=True,
            verbosity=0
        )

        #see that sequence is ok
        tables = [TestModel._meta.db_table]
        info_dict = self.database.get_sequence_info(tables, {'auto': True})
        info = info_dict[tables[0]]
        self.assertEqual(info['max_value'], item.id)
        self.assertEqual(info['current_value'], item.id)
        self.assertEqual(info['broken'], False)
