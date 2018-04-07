Modular {Python2,Python3} IRC bot
=================================

Getting started:
- `cp bot.config.example bot.config`
- `vim bot.config`
- Create a MySQL database, i.e. `CREATE DATABASE foo; GRANT ALL ON foo.* TO ...`
- `mysql <dump.sql`
- `./run.sh`

Install croncheck.sh in your crontab, if desired.  
`* * * * * /path/to/erebus/croncheck.sh`  
To suppress croncheck.sh from restarting the bot without removing from crontab, `touch dontstart`

Output will be placed in `logfile`, which is rotated to `oldlogs/`. (I strongly recommend `rm oldlogs/*` as a weekly crontab entry.)

The bot targets both Python 2 and 3. However, it is generally only actively tested on Python 2.
If it's not working on Python 3 (or an included module isn't working on Python 3), please raise a bug.

Some modules require additional supporting materials, which can be found in `modules/contrib/`.

*****
Module API
----------
The module API has largely remained backwards-compatible and likely will remain so into the future. However, it is still currently unstable, primarily because it's only tested with the included modules. If you find a change was introduced which breaks something you relied on, please raise a bug.

There is currently no documentation as to... well, anything. A good starter template for a new module is `modules/eval.py`. `modules/control.py` uses a significant subset of the API features available. `modules/foo.py` is intended as a demonstration module, and documents some of the major features.
