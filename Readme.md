# Reported is a small script to check the consistency of mozmill-run tests

We do this check weekly to make sure we're not missing any tests that we are
not notified about. Manually this has consumed a lot of work.

This script should help with the process.
We're scraping the web db views of the dashboard couchapp for the data.

This script was made quick and dirty in only a couple of hours.

Usage:

```
virtualenv reported
cd reported
. bin/activate
git clone http://github.com/andreieftimie/reported src
cd src
pip install -r requirements.txt
python reported.py --date=2014-08-07
```

This will generate a file named results_2014-08-07.txt with the results for that
day.
