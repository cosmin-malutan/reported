import argparse
import datetime
import requests
import json
import pprint

# Arguments, only date atm
parser = argparse.ArgumentParser()
parser.add_argument('--date',
                    help='Date')
parser.add_argument('--enddate',
                    help='End Date')
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
enddate = args.enddate or date

# Query arguments for the server call
payload = {
  'startkey': '["All","All","All","%sT00:00:00"]' % date,
  'endkey': '["All","All","All","%sT23:59:59"]' % enddate
}

results = {}

# iterate through all testrun types
for testrun in testruns:
    for domain in ['release']:
        url = url_template.replace('###TESTRUN###', testrun).replace('###DOMAIN###', domain)
        r = requests.get(url, params=payload)
        print 'Fetching data for %s' % r.url
        rows = r.json()['rows']
        for row in rows:
            item = row['value']
            branch = item['application_version']

            if args.branch and branch != args.branch:
                break

            if branch not in results:
                results[branch] = {}
            if testrun not in results[branch]:
                results[branch][testrun] = {}

            if item['system_name'] not in results[branch][testrun]:
                results[branch][testrun][item['system_name']] = {}

            if 'tests_passed' not in results[branch][testrun][item['system_name']]:
                results[branch][testrun][item['system_name']]['tests_passed'] = item['tests_passed']
            else:
                results[branch][testrun][item['system_name']]['tests_passed'] += item['tests_passed']

            if 'tests_failed' not in results[branch][testrun][item['system_name']]:
                results[branch][testrun][item['system_name']]['tests_failed'] = item['tests_failed']
            else:
                results[branch][testrun][item['system_name']]['tests_failed'] += item['tests_failed']

            if 'tests_skipped' not in results[branch][testrun][item['system_name']]:
                results[branch][testrun][item['system_name']]['tests_skipped'] = item['tests_skipped']
            else:
                results[branch][testrun][item['system_name']]['tests_skipped'] += item['tests_skipped']

# Write results into a file
filename = 'failrate_%s.txt' % date
f = open(filename, 'w')
f.write("Failure rate for %s\n======================\n" % date)

# We 'really' care about missing results
for branch in sorted(results, key=lambda x: x):
    f.write("\n\nVersion %s\n--------\n" % branch)
    for testrun in results[branch]:
        f.write("\ntestrun_%s\n~~~~~~~~" % testrun)
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        for platform in results[branch][testrun]:
            f.write("\n%s" % platform.ljust(6))
            passed = results[branch][testrun][platform]['tests_passed']
            failed = results[branch][testrun][platform]['tests_failed']
            skipped = results[branch][testrun][platform]['tests_skipped']
            total = passed + failed + skipped
            total_passed += passed
            total_failed += failed
            total_skipped += skipped
            f.write("passed  %6.2f%% (%d) \n" % ((float(passed) / float(total) * 100), passed))
            f.write("      failed  %6.2f%% (%d) \n" % ((float(failed) / float(total) * 100), failed))
            f.write("      skipped %6.2f%% (%d) \n" % ((float(skipped) / float(total) * 100), skipped))

        total_total = total_passed + total_failed + total_skipped
        f.write("\nTotal passed  %6.2f%% (%d)\n" % ((float(total_passed) / float(total_total) * 100), total_passed))
        f.write("      failed  %6.2f%% (%d)\n" % ((float(total_failed) / float(total_total) * 100), total_failed))
        f.write("      skipped %6.2f%% (%d)\n" % ((float(total_skipped) / float(total_total) * 100), total_skipped))


f.close()
print "Wrote results into %s" % filename

