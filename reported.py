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
args = parser.parse_args()

# URL and query query arguments
# http://mozmill-daily.blargon7.com/_view/functional_reports?startkey=["All","All","All","2014-07-04T23:59:59"]&endkey=["All","All","All","2014-07-04T00:00:00"]&descending=true
url_template = 'http://mozmill-###DOMAIN###.blargon7.com/_view/###TESTRUN###_reports'

# Supported testruns
testruns = ['functional',
            'remote',
            # 'addons',
            'endurance',
            'update']

# We only care for Nightly, Aurora and Beta
# !!! You will need to manually update these after each release !!!
branches = ['37','36','35']

# Currently run locales
# Keep them in sync
# https://github.com/mozilla/mozmill-ci/blob/master/config/production/daily.json#L148
# https://github.com/mozilla/mozmill-ci/blob/master/config/production/release.json#L76
locales = {
    branches[0]: ['en-US'],
    branches[1]: ['de',
                  'en-US',
                  'ru',
                  'zh-CN'],
    branches[2]: ["ach",
                  "af",
                  "an",
                  "ar",
                  "as",
                  "ast",
                  "be",
                  "bg",
                  "bn-BD",
                  "bn-IN",
                  "br",
                  "bs",
                  "ca",
                  "cs",
                  "csb",
                  "da",
                  "de",
                  "dsb",
                  "el",
                  "en-GB",
                  "en-US",
                  "en-ZA",
                  "eo",
                  "es-AR",
                  "es-CL",
                  "es-ES",
                  "es-MX",
                  "et",
                  "eu",
                  "fi",
                  "fr",
                  "fy-NL",
                  "ga-IE",
                  "gd",
                  "gl",
                  "gu-IN",
                  "he",
                  "hi-IN",
                  "hr",
                  "hsb",
                  "hu",
                  "hy-AM",
                  "id",
                  "is",
                  "it",
                  "ja",
                  "kk",
                  "km",
                  "kn",
                  "ko",
                  "lij",
                  "lt",
                  "lv",
                  "mai",
                  "mk",
                  "ml",
                  "mr",
                  "ms",
                  "nb-NO",
                  "nl",
                  "nn-NO",
                  "or",
                  "pa-IN",
                  "pl",
                  "pt-BR",
                  "pt-PT",
                  "rm",
                  "ro",
                  "ru",
                  "si",
                  "sk",
                  "sl",
                  "son",
                  "sq",
                  "sr",
                  "sv-SE",
                  "ta",
                  "te",
                  "th",
                  "tr",
                  "uk",
                  "vi",
                  "xh",
                  "zh-CN",
                  "zh-TW"]
}

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
    'Mac OS X 10.9.5 x86_64',
    'Linux Ubuntu 13.10 x86', 'Linux Ubuntu 13.10 x86_64',
    'Linux Ubuntu 14.04 x86', 'Linux Ubuntu 14.04 x86_64'
]

# If no --date supplied, use today
date = args.date or datetime.date.today().isoformat()
enddate = args.enddate or date

# Query arguments for the server call
payload = {
  'startkey': '["All","All","All","%sT00:00:00"]' % date,
  'endkey': '["All","All","All","%sT23:59:59"]' % enddate
}

# Build the expected object, we'll match this against the actual reports
expected = {}
for testrun in testruns:
    expected[testrun] = {}
    # update are not localised, only en-US
    # endurance is only run against en-US nightly
    # TODO: make DRY
    if testrun is 'update':
        for branch in branches:
            expected[testrun][branch] = {}
            expected[testrun][branch]['en-US'] = {}
            for system in systems:
                expected[testrun][branch]['en-US'][system] = None
    elif testrun is 'endurance':
        branch = branches[0]
        expected[testrun][branch] = {}
        expected[testrun][branch]['en-US'] = {}
        for system in systems:
            expected[testrun][branch]['en-US'][system] = None
    else:
        for branch in branches:
            expected[testrun][branch] = {}
            for locale in locales[branch]:
                expected[testrun][branch][locale] = {}
                for system in systems:
                    expected[testrun][branch][locale][system] = None

# pp = pprint.PrettyPrinter(indent=2)
# pp.pprint(expected)

# iterate through all testrun types
for testrun in testruns:
    # different domains for nightly/aurora vs beta
    for domain in ['daily', 'release']:
        url = url_template.replace('###TESTRUN###', testrun).replace('###DOMAIN###', domain)
        r = requests.get(url, params=payload)
        print 'Fetching data for %s' % r.url
        rows = r.json()['rows']
        for row in rows:
            item = row['value']
            branch = item['application_version'].split('.')[0]
            locale = item['locale'].replace('ja-JP-mac', 'ja')
            system = '%s %s %s' % (item['system_name'], item['system_version'], item['processor'])
            # print '%s %s %s' %(branch, locale, system)

            # Save the report, only for the branches we care
            if branch in branches:
                # Fails becuase of undocumented locales run as ondeman update
                # a try will do, just omit those
                try:
                    expected[testrun][branch][locale][system] = 'DONE'
                except:
                    pass

# pp = pprint.PrettyPrinter(indent=2)
# pp.pprint(expected)

# Write results into a file
filename = 'results_%s.txt' % args.date
f = open(filename, 'w')
f.write("Missing Reports for %s\n============\n" % args.date)

# We 'really' care about missing results
for testrun in sorted(expected):
    for branch in sorted(expected[testrun]):
        for locale in sorted(expected[testrun][branch]):
            for system in sorted(expected[testrun][branch][locale]):
                if not expected[testrun][branch][locale][system]:
                    f.write("Missing: %s %s %s %s\n" % (testrun, branch, locale, system))
f.write('\n\n')

# Write all of them for posterity
for testrun in sorted(expected):
    f.write(testrun + '\n----------\n')
    for branch in sorted(expected[testrun]):
        for locale in sorted(expected[testrun][branch]):
            f.write("%s %s: " % (branch, locale))
            for system in sorted(expected[testrun][branch][locale]):
                f.write("%s [%s]\n" % (expected[testrun][branch][locale][system], system))
            f.write('\n')
        f.write('\n')
    f.write('\n')

f.close()
print "Wrote results into %s" % filename

