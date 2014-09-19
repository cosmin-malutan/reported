import argparse
import datetime
import requests
import json
import pprint

# Arguments, only date atm
parser = argparse.ArgumentParser()
parser.add_argument('--date',
                    default=datetime.date.today().isoformat(),
                    help='Date')
parser.add_argument('--branch',
                    default=None,
                    help='Branch')
args = parser.parse_args()

# URL and query query arguments
# http://mozmill-daily.blargon7.com/_view/functional_reports?startkey=["All","All","All","2014-07-04T23:59:59"]&endkey=["All","All","All","2014-07-04T00:00:00"]&descending=true
url_template = 'http://mozmill-###DOMAIN###.blargon7.com/_view/###TESTRUN###_reports'

# Supported testruns
testruns = ['functional',
            'remote',
            'addons',
            'endurance',
            'update']

# All CI machines / architecures should be here
# !!! Update them whenever someone does a system update !!!
# ISSUE: Windows 8.1 and Windows 8 are reporting the same version
systems = [
    'Win 5.1.2600 x86',
    'Win 6.0.6002 x86',
    'Win 6.1.7601 x86', 'Win 6.1.7601 x86_64',
    'Win 6.2.9200 x86', 'Win 6.2.9200 x86_64',
    'Mac OS X 10.6.8 x86_64',
    'Mac OS X 10.7.5 x86_64',
    'Mac OS X 10.8.5 x86_64',
    'Mac OS X 10.9.4 x86_64',
    'Linux Ubuntu 12.04 x86', 'Linux Ubuntu 12.04 x86_64',
    'Linux Ubuntu 13.10 x86', 'Linux Ubuntu 13.10 x86_64'
]

# If no --date supplied, use today
date = args.date or datetime.date.today().isoformat()

# Query arguments for the server call
payload = {
  'startkey': '["All","All","All","%sT23:59:59"]' % date,
  'endkey': '["All","All","All","%sT00:00:00"]' % date,
  'descending': 'true'
}

results = {}

# iterate through all testrun types
for testrun in testruns:
    if testrun not in results:
        results[testrun] = {}
    # different domains for nightly/aurora vs beta
    for domain in ['release']:
        url = url_template.replace('###TESTRUN###', testrun).replace('###DOMAIN###', domain)
        print 'Fetching data for %s' % url
        r = requests.get(url, params=payload)
        rows = r.json()['rows']
        for row in rows:
            item = row['value']
            branch = item['application_version']

            if args.branch and branch != args.branch:
                break

            if branch not in results[testrun]:
                results[testrun][branch] = {}

            if item['system_name'] not in results[testrun][branch]:
                results[testrun][branch][item['system_name']] = {}

            if 'tests_passed' not in results[testrun][branch][item['system_name']]:
                results[testrun][branch][item['system_name']]['tests_passed'] = item['tests_passed']
            else:
                results[testrun][branch][item['system_name']]['tests_passed'] += item['tests_passed']

            if 'tests_failed' not in results[testrun][branch][item['system_name']]:
                results[testrun][branch][item['system_name']]['tests_failed'] = item['tests_failed']
            else:
                results[testrun][branch][item['system_name']]['tests_failed'] += item['tests_failed']

            if 'tests_skipped' not in results[testrun][branch][item['system_name']]:
                results[testrun][branch][item['system_name']]['tests_skipped'] = item['tests_skipped']
            else:
                results[testrun][branch][item['system_name']]['tests_skipped'] += item['tests_skipped']

# Write results into a file
filename = 'results_%s.txt' % date
f = open(filename, 'w')
f.write("Failing rate for %s\n============\n" % date)

# We 'really' care about missing results
for testrun in results:
    for branch in results[testrun]:
        f.write("\n\n\n\nTestrun %s, branch %s \n" % (testrun, branch))
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        for platform in results[testrun][branch]:
            f.write("\n          Platform  %s \n" % platform)
            passed = results[testrun][branch][platform]['tests_passed']
            failed = results[testrun][branch][platform]['tests_failed']
            skipped = results[testrun][branch][platform]['tests_skipped']
            total = passed + failed + skipped
            total_passed += passed
            total_failed += failed
            total_skipped += skipped
            f.write("\n               passed  %f \n" % (float(passed) / float(total) * 100))
            f.write("\n               failed  %f \n" % (float(failed) / float(total) * 100))
            f.write("\n               skipped  %f \n" % (float(skipped) / float(total) * 100))

        total_total = total_passed + total_failed + total_skipped
        f.write("\n          Total passed  %f \n" % (float(total_passed) / float(total_total) * 100))
        f.write("\n          Total failed  %f \n" % (float(total_failed) / float(total_total) * 100))
        f.write("\n          Total skipped  %f \n" % (float(total_skipped) / float(total_total) * 100))


f.close()
print "Wrote results into %s" % filename

