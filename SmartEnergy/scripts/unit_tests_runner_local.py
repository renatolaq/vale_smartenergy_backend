from django.test.runner import DiscoverRunner
from django.db import connection, connections, DEFAULT_DB_ALIAS
from django.test.utils import get_unique_databases_and_mirrors
from sql_server.pyodbc.creation import BaseDatabaseCreation
from django.conf import settings
from datetime import datetime


class SmartEnergyTestRunner(DiscoverRunner):
    """ A test runner to test without database creation """

    def setup_databases(self, **kwargs):
        """ Override the database creation defined in parent class """
        
        connection = connections[DEFAULT_DB_ALIAS]
        keepdb = True
        serialize = connection.settings_dict.get(
            'TEST', {}).get('SERIALIZE', True)

        """
        Create a test database
        """
        test_database_name = connection.creation._get_test_db_name()

        # We could skip this call if keepdb is True, but we instead
        # give it the keepdb param. This is to handle the case
        # where the test DB doesn't exist, in which case we need to
        # create it, then just not destroy it. If we instead skip
        # this, we will get an exception.
        connection.creation._create_test_db(0, False, keepdb)

        connection.creation.connection.close()
        settings.DATABASES[connection.creation.connection.alias]["NAME"] = test_database_name
        connection.creation.connection.settings_dict["NAME"] = test_database_name

        # We then serialize the current state of the database into a string
        # and store it on the connection. This slightly horrific process is so people
        # who are testing on databases without transactions or who are using
        # a TransactionTestCase still get a clean database on every test run.
        if serialize:
            connection.creation.connection._test_serialized_contents = connection.creation.serialize_db_to_string()

        # Ensure a connection for the side effect of initializing the test database.
        connection.creation.connection.ensure_connection()

        time = datetime.now().strftime("%Y%m%d%H%M%S")

        with connection.cursor() as cursor:
            cursor.execute(f"""
                DECLARE @database_file varchar(max)
                DECLARE @database_file_name varchar(max)
                DECLARE @sql varchar(max)

                SELECT @database_file_name = [name], 
                       @database_file = REPLACE([physical_name], '.mdf', '_TestRestorePoint.mdf')
	              FROM [{test_database_name}].[sys].[database_files]
                 WHERE [name] NOT LIKE '%_log'

                IF EXISTS (SELECT * 
                             FROM sys.databases
                            WHERE name='{test_database_name}_TestRestorePoint')
	                DROP DATABASE [{test_database_name}_TestRestorePoint]

                SELECT @sql = 'CREATE DATABASE [{test_database_name}_TestRestorePoint]
                                   ON (NAME='''+@database_file_name+''', 
                                      FILENAME = '''+@database_file+''') 
                                   AS SNAPSHOT OF [{test_database_name}]'

                EXEC (@sql)
            """)
        return {
            'test_database_name': test_database_name,
            'restore_point_name': f'{test_database_name}_TestRestorePoint'
        }

    def teardown_databases(self, old_config, **kwargs):
        """ Override the database teardown defined in parent class """
        if not self.keepdb:
            with connection.cursor() as cursor:
                cursor.execute(f'''
                    USE master;
                    DECLARE @dbname SYSNAME

                    SET @dbname = '{old_config['test_database_name']}'

                    DECLARE @spid int
                    SELECT @spid = min(spid) 
                      FROM master.dbo.sysprocesses
                     WHERE dbid = db_id(@dbname)
                    WHILE @spid Is Not Null
                    BEGIN
                            EXECUTE ('Kill ' + @spid)
                            SELECT @spid = min(spid) 
                              FROM master.dbo.sysprocesses
                             WHERE dbid = db_id(@dbname) 
                               AND spid > @spid
                    END
                    ALTER DATABASE [{old_config['test_database_name']}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE
                    RESTORE DATABASE [{old_config['test_database_name']}] 
                       FROM DATABASE_SNAPSHOT = '{old_config['restore_point_name']}';  
                    ALTER DATABASE [{old_config['test_database_name']}] SET MULTI_USER
                    DROP DATABASE [{old_config['restore_point_name']}]
                ''')
