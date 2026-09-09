#!/usr/bin/env python3
"""
Synthetic data generator for the WIP Power BI model.
====================================================

WHY THIS EXISTS
---------------
The report this model drives was originally built against live client data in
SharePoint. To publish the project as a portfolio piece, that data had to be
replaced with something that is (a) completely fabricated and (b) still shaped
closely enough that every visual, measure and relationship behaves as it does
in production.

This script does not invent data from nothing. It profiles an existing seed
extract and then samples from the distributions it finds, which is what keeps
the report looking real rather than uniform-random.

WHAT IT PRESERVES FROM THE SEED DATA
------------------------------------
  * Value pools -- the 246-person roster, 632 client codes, 192 deliverables
    and 21 SLA values are reused verbatim, weighted by observed frequency so
    the team and client mix is unchanged.
  * Functional dependencies -- userName determines userId/teamName/stlName,
    and tcRef determines clientName/Xero Name. Both are 1:1 in the seed and
    stay 1:1 in the output, so no visual gains a spurious extra row.
  * Joint distributions -- Rates and Standard Hours are drawn as a PAIR from
    combinations that actually co-occur. Sampling them independently is the
    obvious approach and it is wrong: the top rate (343.75) meeting the top
    hours (910) pushes Forecasted Revenue to 312k against a seed max of 30k.
  * Column sparsity -- the four fact_client_data measures are populated at
    their observed rates (62%/66%/48%/62%) rather than being filled in, and
    Forecasted Revenue is kept equal to Rates x Standard Hours where both
    exist, matching the seed's own internal arithmetic.
  * Formats -- date and time columns are emitted as the same text/datetime
    shapes the Power Query layer expects, so no M changes are needed.
  * Referential integrity -- every generated tcRef and tcref_bs_id resolves
    to a dim_clients row.

WHAT IT ADDS DELIBERATELY
-------------------------
  * Coverage from 2026-01-01 to 2026-09-03 on weekdays, filling the windows
    the seed extract did not reach.
  * Seasonality: a quiet January, BAS-lodgement humps in late February and
    late April, and the Australian financial-year-end peak across May-July.
  * Non-billable activity -- LEAVE, SICK LEAVE, ADMIN - BREAK and
    UNCHARGEABLE HRS at roughly 10% combined, plus a 3% slice of billable
    rows carrying Admin/Operations/Workforce Experience SLAs. Without these
    the 'Category for Productivity Page' calculated column has six dead
    branches and the Productivity page can only ever show billable hours.
  * Public holidays, where volume collapses and leave dominates.

DETERMINISM
-----------
Seeded with a fixed value, so re-running reproduces the committed workbook
byte-for-byte in content. Change SEED for a different draw.

USAGE
-----
    pip install openpyxl
    python tools/generate_synthetic_data.py

Expects Synthetic_Data.xlsx alongside it (see SRC below), containing the
seed rows. Existing rows are never modified -- new rows are appended, and the
script recovers the seed by truncating to the row counts in ORIG.
"""
import openpyxl, collections, datetime as dt, json, random, statistics, os

SEED = 20260903
random.seed(SEED)

# Workbook lives at the repository root, one level up from tools/
SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'Synthetic_Data.xlsx')
TODAY = dt.date(2026, 9, 3)

# Row counts of the original seed extract. Truncating to these recovers the
# seed regardless of how many times this script has been run.
ORIG = {'fact_activities': 5000, 'fact_client_data': 5000, 'dim_clients': 632}

FILL = [(dt.date(2026, 1, 1), dt.date(2026, 4, 30)),
        (dt.date(2026, 8, 1), TODAY)]

# reshaped: Jan trough -> Feb BAS hump -> Mar trough -> Apr BAS hump
# -> May/Jun/Jul FY-end peak (existing, fixed at 1.0) -> Aug dip -> Sep recovery
MONTH_MULT = {1: 0.55, 2: 0.90, 3: 0.76, 4: 0.93, 8: 0.80, 9: 0.85}

HOLIDAYS = {
    dt.date(2026, 1, 1):  'Public Holiday',
    dt.date(2026, 1, 26): 'Public Holiday',
    dt.date(2026, 4, 3):  'Public Holiday',
    dt.date(2026, 4, 6):  'Public Holiday',
    dt.date(2026, 8, 31): 'Public Holiday',
}

NONBILLABLE = {'LEAVE': 0.035, 'SICK LEAVE': 0.015,
               'ADMIN - BREAK': 0.035, 'UNCHARGEABLE HRS': 0.015}
SPECIAL_SLA = ['Admin', 'Operations', 'Workforce Experience']
NB_DELIVERABLE = {
    'LEAVE':            ['Annual Leave', 'Planned Leave', 'Leave - Approved'],
    'SICK LEAVE':       ['Sick Leave', 'Carers Leave', 'Medical Appointment'],
    'ADMIN - BREAK':    ['Team Break', 'Meal Break', 'Rest Break'],
    'UNCHARGEABLE HRS': ['Internal Admin', 'Training', 'Team Meeting',
                         'System Downtime', 'Onboarding Support'],
}
NB_SLA = {'LEAVE': 'Workforce Experience', 'SICK LEAVE': 'Workforce Experience',
          'ADMIN - BREAK': 'Operations', 'UNCHARGEABLE HRS': 'Admin'}

# ------------------------------------------------------- reset to originals
wb = openpyxl.load_workbook(SRC)

def truncate(name, keep):
    ws = wb[name]
    rows = list(ws.iter_rows(values_only=True))
    hdr = list(rows[0])
    data = [list(r) for r in rows[1:] if any(v is not None for v in r)][:keep]
    wb.remove(ws)
    return hdr, data

order = wb.sheetnames[:]
FA_H, FA = truncate('fact_activities', ORIG['fact_activities'])
FC_H, FC = truncate('fact_client_data', ORIG['fact_client_data'])
DC_H, DC = truncate('dim_clients', ORIG['dim_clients'])
# release_notes: first pass wrote 11 generated rows THEN the 3 originals
rows = list(wb['release_notes'].iter_rows(values_only=True))
RN_H = list(rows[0])
RN = [list(r) for r in rows[1:] if any(v is not None for v in r)][-3:]
wb.remove(wb['release_notes'])

A = {c: i for i, c in enumerate(FA_H)}
C = {c: i for i, c in enumerate(FC_H)}
D = {c: i for i, c in enumerate(DC_H)}
R = {c: i for i, c in enumerate(RN_H)}
assert len(FA) == 5000 and len(FC) == 5000 and len(DC) == 632 and len(RN) == 3

# ----------------------------------------------------------- learn from source
roster = {r[A['userName']]: (r[A['userId']], r[A['teamName']], r[A['stlName']]) for r in FA}
USERS = sorted(roster)
uw = collections.Counter(r[A['userName']] for r in FA)
UW = [uw[u] for u in USERS]

client_map = {r[A['tcRef']]: (r[A['clientName']], r[A['Xero Name']]) for r in FA}
TCREFS = sorted(client_map)
tw = collections.Counter(r[A['tcRef']] for r in FA)
TW = [tw[t] for t in TCREFS]

DELIVERABLES = sorted(set(r[A['deliverableName']] for r in FA))
dw = collections.Counter(r[A['deliverableName']] for r in FA)
DW = [dw[d] for d in DELIVERABLES]
SLAS = sorted(set(r[A['sla']] for r in FA))
sw = collections.Counter(r[A['sla']] for r in FA)
SW = [sw[s] for s in SLAS]
REMARKS = sorted(set(r[A['remarks']] for r in FA if r[A['remarks']]))
remark_rate = sum(1 for r in FA if r[A['remarks']]) / len(FA)
ot_rate = sum(1 for r in FA if r[A['isOT']]) / len(FA)

DURATIONS = [15, 20, 30, 45, 60, 75, 90, 120, 150, 180, 240]
dur_w = collections.Counter()
for r in FA:
    a = [int(x) for x in str(r[A['startTime']]).split(':')]
    b = [int(x) for x in str(r[A['endTime']]).split(':')]
    dur_w[((b[0]*60+b[1]) - (a[0]*60+a[1])) % 1440] += 1
DUR_W = [dur_w.get(d, 1) for d in DURATIONS]

ACTIONS = ['Created', 'Submitted', 'Updated', 'Approved', 'Reopened']
CHANGE_FIELDS = ['Date', 'Task', 'Start Time', 'Client', 'Deliverable', 'Team', 'End Time']
BASE_PER_DAY = statistics.mean(collections.Counter(r[A['date']].date() for r in FA).values())

# --- FIX 1: joint (Rates, Standard Hours) pairs observed in the original data.
# Restricted to rows where Forecasted Revenue is ALSO present, because those are
# the pairs the original generator actually allowed to be multiplied together.
# Pairs drawn from rows with a null Forecasted can multiply out to 113k.
JOINT_RS = [(r[C['Rates']], r[C['Standard Hours']]) for r in FC
            if r[C['Rates']] is not None and r[C['Standard Hours']] is not None
            and r[C['Forecasted Revenue']] is not None]
JOINT_RS_ANY = [(r[C['Rates']], r[C['Standard Hours']]) for r in FC
                if r[C['Rates']] is not None and r[C['Standard Hours']] is not None]
RATES_ONLY = [r[C['Rates']] for r in FC if r[C['Rates']] is not None]
STD_ONLY = [r[C['Standard Hours']] for r in FC if r[C['Standard Hours']] is not None]
XEROREV = [r[C['Xero Revenue']] for r in FC if r[C['Xero Revenue']] is not None]
FCASTREV = [r[C['Forecasted Revenue']] for r in FC if r[C['Forecasted Revenue']] is not None]
FCAST_MAX = max(FCASTREV)
p_rate = sum(1 for r in FC if r[C['Rates']] is not None) / len(FC)
p_fcast = sum(1 for r in FC if r[C['Forecasted Revenue']] is not None) / len(FC)
p_std = sum(1 for r in FC if r[C['Standard Hours']] is not None) / len(FC)
p_xero = sum(1 for r in FC if r[C['Xero Revenue']] is not None) / len(FC)
FC_ROWS = round(len(FC) / len(set(r[C['Date']] for r in FC)))
FC_DIST = round(len({(r[C['tcref_bs_id']], r[C['Date']]) for r in FC})
                / len(set(r[C['Date']] for r in FC)))
FC_CLIENTS = [(r[D['TC Reference*']], r[D['Xero Name*']], r[D['Business Stream*']],
               r[D['tcref_bs_id']]) for r in DC]

# ------------------------------------------------------------------ helpers
def weekdays(a, b):
    d = a
    while d <= b:
        if d.weekday() < 5:
            yield d
        d += dt.timedelta(days=1)

def fmt_time(m): return f'{(m//60)%24:02d}:{m%60:02d}:00'

def ampm(m):
    h, mm = (m//60) % 24, m % 60
    return f'{h%12 or 12:02d}:{mm:02d} {"AM" if h<12 else "PM"}'

def day_volume(d):
    mult = MONTH_MULT[d.month]
    if d.month == 1 and d.day <= 9:
        mult *= 0.45
    elif d.month == 1 and d.day <= 16:
        mult *= 0.75
    if d.month == 2 and d.day >= 20:      # BAS Q2 lodgement crunch
        mult *= 1.12
    if d.month == 4 and d.day >= 20:      # BAS Q3 lodgement crunch
        mult *= 1.12
    if d in HOLIDAYS:
        mult *= 0.18
    n = BASE_PER_DAY * mult
    return max(4, int(random.gauss(n, n*0.11)))

def make_history(row_date, deliv, client, team, s, e, created):
    out = []
    for _ in range(random.choice([1, 1, 2, 2])):
        vals = {'Date': row_date.strftime('%Y-%m-%d'), 'Task': deliv[:28],
                'Deliverable': deliv[:28], 'Client': client or 'N/A', 'Team': team,
                'Start Time': ampm(s), 'End Time': ampm(e)}
        ts = created + dt.timedelta(minutes=random.randint(0, 60*24*30))
        if ts.date() > TODAY:
            ts = dt.datetime.combine(TODAY, dt.time(random.randint(8, 20), random.randint(0, 59)))
        out.append({'user': random.choice(USERS),
                    'timestamp': ts.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                    'action': random.choice(ACTIONS),
                    'changes': [f'{f}: "N/A" → "{vals[f]}"'
                                for f in random.sample(CHANGE_FIELDS, random.randint(1, 5))]})
    return json.dumps(out, ensure_ascii=False)

# ------------------------------------------------------- fact_activities
nb_cum, acc = [], 0.0
for k in NONBILLABLE:
    acc += NONBILLABLE[k]
    nb_cum.append((k, acc))
NB_TOTAL = acc

new_fa = []
for a, b in FILL:
    for d in weekdays(a, b):
        holiday = HOLIDAYS.get(d)
        for _ in range(day_volume(d)):
            user = random.choices(USERS, weights=UW, k=1)[0]
            uid, team, stl = roster[user]
            roll, kind = random.random(), None
            if holiday:
                kind = 'LEAVE' if random.random() < 0.85 else 'UNCHARGEABLE HRS'
            elif roll < NB_TOTAL:
                for k, c in nb_cum:
                    if roll < c:
                        kind = k
                        break
            if kind:
                tcref = cname = xero = kind
                deliv = random.choice(NB_DELIVERABLE[kind])
                sla = NB_SLA[kind]
            else:
                tcref = random.choices(TCREFS, weights=TW, k=1)[0]
                cname, xero = client_map[tcref]
                deliv = random.choices(DELIVERABLES, weights=DW, k=1)[0]
                sla = (random.choice(SPECIAL_SLA) if random.random() < 0.03
                       else random.choices(SLAS, weights=SW, k=1)[0])
            dur = (random.choice([15, 20, 30, 30, 45, 60]) if kind == 'ADMIN - BREAK'
                   else random.choices(DURATIONS, weights=DUR_W, k=1)[0])
            s = random.randrange(7*60, 19*60, 5)
            e = s + dur
            created = dt.datetime.combine(d, dt.time(random.randint(7, 19), random.randrange(0, 60)))
            upd = created + dt.timedelta(minutes=random.randint(0, 60*24*45))
            cap = dt.datetime.combine(TODAY, dt.time(23, 59))
            if upd > cap:
                upd = cap - dt.timedelta(minutes=random.randint(0, 60*24*3))
            upd = max(upd, created)
            lv = random.choice([7.6, 7.6, 7.6, 3.8, 4.0, 8.0]) if kind in ('LEAVE', 'SICK LEAVE') else None
            is_ot = (random.random() < ot_rate) and not kind
            remark = ('overtime approved in advance' if is_ot
                      else (random.choice(REMARKS) if random.random() < remark_rate else None))
            row = [None]*len(FA_H)
            row[A['createdAt']] = created;          row[A['updatedAt']] = upd
            row[A['userId']] = uid;                 row[A['teamName']] = team
            row[A['stlName']] = stl;                row[A['userName']] = user
            row[A['tcRef']] = tcref;                row[A['clientName']] = cname
            row[A['deliverableName']] = deliv;      row[A['sla']] = sla
            row[A['date']] = dt.datetime.combine(d, dt.time(0, 0))
            row[A['startTime']] = fmt_time(s);      row[A['endTime']] = fmt_time(e)
            row[A['history']] = make_history(d, deliv, cname, team, s, e, created)
            row[A['holidayType']] = holiday if kind in ('LEAVE', 'SICK LEAVE') else None
            row[A['isOT']] = bool(is_ot);           row[A['remarks']] = remark
            row[A['Xero Name']] = xero;             row[A['leaveHours']] = lv
            new_fa.append(row)

# ----------------------------------------------------- fact_client_data
def fridays(a, b):
    d = a
    while d.weekday() != 4:
        d += dt.timedelta(days=1)
    while d <= b:
        yield d
        d += dt.timedelta(days=7)

new_fc = []
for a, b in FILL:
    for d in fridays(a, b):
        mult = MONTH_MULT[d.month]
        distinct = max(20, int(FC_DIST*mult))
        total = max(distinct, int(FC_ROWS*mult))
        chosen = random.sample(FC_CLIENTS, min(distinct, len(FC_CLIENTS)))
        picks = list(chosen) + [random.choice(chosen) for _ in range(total-len(chosen))]
        random.shuffle(picks)
        datestr = f'{d.month}/{d.day:02d}/{d.year}'
        for name, xero, bs, tbid in picks:
            has_r, has_f = random.random() < p_rate, random.random() < p_fcast
            has_s, has_x = random.random() < p_std, random.random() < p_xero
            rate = std = None
            if has_r and has_s:
                # FIX 1: draw the pair jointly, from the F-present pool when the
                # row will carry a Forecasted value so rate*hours stays in range
                rate, std = random.choice(JOINT_RS if has_f else JOINT_RS_ANY)
            elif has_r:
                rate = random.choice(RATES_ONLY)
            elif has_s:
                std = random.choice(STD_ONLY)
            if has_f:
                if rate is not None and std is not None and random.random() < 0.97:
                    fcast = round(rate*std, 2)
                else:
                    fcast = round(min(random.choice(FCASTREV)*random.uniform(0.9, 1.1), FCAST_MAX), 2)
                fcast = min(fcast, FCAST_MAX)
            else:
                fcast = None
            xrev = round(random.choice(XEROREV)*random.uniform(0.88, 1.12), 2) if has_x else None
            row = [None]*len(FC_H)
            row[C['Name of Clients (TC Reference)']] = name
            row[C['Xero Name']] = xero
            row[C['Business Stream']] = bs
            row[C['Date']] = datestr
            row[C['tcref_bs_id']] = tbid
            row[C['Rates']] = rate
            row[C['Forecasted Revenue']] = fcast
            row[C['Standard Hours']] = std
            row[C['Xero Revenue']] = xrev
            new_fc.append(row)

# ------------------------------------------------------------- dim_clients
new_dc = []
for k in NONBILLABLE:
    row = [None]*len(DC_H)
    row[D['Source.Name']] = 'TC Master.csv'
    row[D['TC Reference*']] = k
    row[D['Xero Name*']] = k
    row[D['Business Stream*']] = 'Internal'
    row[D['Principal*']] = 'Aretex'
    row[D['Responsible*']] = 'INT'
    row[D['Status']] = 'Active'
    row[D['Type']] = 'Core'
    row[D['Remarks']] = 'Internal / non-billable code'
    row[D['Added By']] = 'Jearomel'
    row[D['tcref_bs_id']] = f'{k}.Internal'
    new_dc.append(row)

# ----------------------------------------------------------- release_notes
REL = [
    ('01/16/2026', 'v1.8', 'Feature', 'Overview', 'Initial WIP portfolio dashboard released to the leadership team', 2),
    ('01/30/2026', 'v1.9', 'Fix', 'Client Overview', 'Corrected client count when a client spans multiple business streams', 3),
    ('02/13/2026', 'v2.0', 'Feature', 'Team Performance', 'Added Team Performance page with STL rollup and utilisation split', 2),
    ('02/27/2026', 'v2.0', 'Fix', 'Time Details Analysis', 'Duration now handles activities that cross midnight', 3),
    ('03/20/2026', 'v2.1', 'Feature', 'Top/Bottom Clients', 'Added Top/Bottom Clients ranking with configurable N', 2),
    ('04/10/2026', 'v2.2', 'Feature', 'Overview', 'Forecasted vs Xero revenue variance added to the client scorecard', 2),
    ('04/24/2026', 'v2.2', 'Fix', 'Client Overview', 'Business Stream slicer no longer resets when drilling through', 3),
    ('06/12/2026', 'v2.3', 'Feature', 'Time Details Analysis', 'Productivity categories split into Billable, Leave, Break and Unchargeable', 2),
    ('07/17/2026', 'v2.4', 'Feature', 'Other Reports', 'Added Other Reports page linking the operational extracts', 2),
    ('07/31/2026', 'v2.4', 'Fix', 'Team Performance', 'Fixed blank STL row appearing for internal activity codes', 3),
    ('08/21/2026', 'v2.5', 'Feature', 'Overview', 'Fiscal year toggle added across all pages', 2),
]
new_rn = []
for ds, ver, typ, page, desc, ts in REL:
    row = [None]*len(RN_H)
    row[R['Date']] = ds
    row[R['Version']] = ver
    row[R['Type']] = typ
    row[R['Page']] = page
    row[R['Description']] = desc
    row[R['TypeSort']] = ts
    row[R['Date Display']] = dt.datetime.strptime(ds, '%m/%d/%Y').strftime('%b %y')
    new_rn.append(row)

# ------------------------------------------------------------------- write
def build(name, hdr, rows):
    ws = wb.create_sheet(name)
    ws.append(hdr)
    for r in rows:
        ws.append(r)

build('fact_activities', FA_H, FA + new_fa)
build('fact_client_data', FC_H, FC + new_fc)
build('dim_clients', DC_H, DC + new_dc)
build('release_notes', RN_H, new_rn + RN)
for i, n in enumerate(order):
    wb.move_sheet(n, offset=i - wb.sheetnames.index(n))
wb.save(SRC)

print(f'fact_activities  : {len(FA)} original + {len(new_fa)} new = {len(FA)+len(new_fa)}')
print(f'fact_client_data : {len(FC)} original + {len(new_fc)} new = {len(FC)+len(new_fc)}')
print(f'dim_clients      : {len(DC)} original + {len(new_dc)} new = {len(DC)+len(new_dc)}')
print(f'release_notes    : {len(new_rn)} history + {len(RN)} original = {len(new_rn)+len(RN)}')
print('sheets:', wb.sheetnames)
