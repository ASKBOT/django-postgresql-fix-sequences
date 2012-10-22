django-postgresql-fix-sequences
===============================
Fixes sequences in postgresql to help prevent the 
duplicate primary key errors.

The command needs to be run with all other connections to the database
closed, so that there is no competition for the access to the sequences.

Examples:

    python manage.py postgres_fix_sequences --auto
    python manage.py postgres_fix_sequences --minvalue 1 --increment 2
    python manage.py postgres_fix_sequences --tables=auth_user --auto

The fixes can be applied either to all tables that are part of a 
django project, or to specifically selected tables, in which case
those tables do not have to be part of any django application.

Sequences can be fixed either automatically (where appropriate)
or by manually setting the sequence parameters
(supported values are minvalue and increment -
as defined in CREATE SEQUENCE postgresql command).

Fix sequences automatically with the `--auto` flag
--------------------------------------------------
Sequences will be repaired automatically.
Use this if you know that this is possible and safe,
e.g. that the starting value and the step of the sequences
are correct, but the current value may be off.

Note that either `--auto` or `--min-value` together with `--increment`
must be given.

The command takes current value in the sequence
`currval()` and the next value `netxval()`
and determines step in the sequence.

Finds the highest id number (let's call it `max_id`)
for the rows matching the given sequence,
if id number is greater or equals to what is returned by the `nextval()`
we need to set the current value with `setval()`
to exactly what we found for `max_id`.

Specify minimum value and the increment for the sequence
--------------------------------------------------------
If you cannot use the `--auto` method, then you have to specify
`--minvalue` and `--increment` for the sequence manually.
Both should be positive integers.

Specify tables manually with --tables option
-----------------------------------------------
For example, with:

    python manage.py postgres_fix_sequences --tables=auth_user,auth_group

only tables `auth_user` and `auth_group` will be fixed.

Note that with the --tables table names do not have to be
part of a django project.


Copyright: 2012 Askbot SpA, Vina del Mar, Chile.
Author: Evgeny Fadeev, evgeny.fadeev@gmail.com
License: MIT
