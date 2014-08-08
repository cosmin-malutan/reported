# Reported is a small script to check the consistency of mozmill-run tests

We do this check weekly to make sure we're not missing any tests that we are
not notified about. Manually this has consumed a lot of work.

This script should help with the process.

Usage:

```
virtualenv reported
cd reported
git clone http://github.com/andreieftimie/reported src
cd src
pip install < requirements.txt
python reported.py --date=2014-08-07
```
