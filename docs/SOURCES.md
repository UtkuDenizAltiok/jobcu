# Source and service index

This indexes the adapters in the current code and the dated access evidence behind them.
It does **not** confirm today's availability, vacancies, terms or recall.

Dates below describe recorded checks, not current availability. Historical investigations are
retained in Git. Adapter parsing and request details are in `src/jobcu/sources/`.

## Temporary provider recovery — 2026-10-23

Google's [background execution guide](https://ai.google.dev/gemini-api/docs/background-execution)
documents asynchronous execution for standard models, including Gemini 3.8 Flash. Normal HTTP
connections commonly close around 60 seconds; an immediately returned interaction ID supports
retrieval after a dropped connection. This is consistent with a long-request failure mode,
not proof of which component closed any particular connection. Background requests require
`store=true`; they cannot provide stateless recovery.

The [Interactions overview](https://ai.google.dev/gemini-api/docs/interactions-overview)
documents paid-tier stored-interaction retention of up to 55 days and early deletion. Stateless
`store=false` requests do not appear in interaction observability logs; waiting for a missing
stateless request to appear there cannot recover its bill. Jobcu's optional recovery setting
explicitly discloses temporary request/answer storage and automatic deletion, with retained local
IDs for failed cleanup. No account retention/logging setting is changed. Provider data terms and
billing attribution still apply; an operation ID does not itself prove complete usage or quality.

## Routes billing

**Routes pricing rechecked 2026-10-16:** Google's [global price list](https://developers.google.com/maps/billing-and-pricing/pricing)
lists Compute Route Matrix Essentials/Pro/Enterprise at USD5/10/15 per 1,000 events in the first
paid tier. [Routes billing guidance](https://developers.google.com/maps/documentation/routes/usage-and-billing)
describes matrix elements as origins multiplied by destinations and feature-dependent SKUs.
Free allowances and account-specific charges are separate; a conservative development estimate
does not establish an invoice. Count attempted elements and keep existing monthly controls.

**Transit timing measured 2026-10-30 (real requests, next Wednesday):** a route matrix `duration`
stays the same for departures 10:30-10:45 when the journey is the same, so it holds no wait for the
first vehicle, and `staticDuration` equals it. It can still hold waits between vehicles, overnight
in the worst case. It is the journey arriving first after the time asked, which can be slower than
the next one, so one departure can overstate by up to 25 minutes. An `arrivalTime` gave the same
kind of answer. The destination matters more: up to about 35 minutes between a city's centre and a
main station. Jobcu's `data/stations.csv` holds GeoNames points; Google's own geocoded points are
not stored.

## Local deletion evidence

**Checked 2026-10-09.** SQLite's [secure_delete documentation](https://www.sqlite.org/pragma.html#pragma_secure_delete)
says ordinary deleted content is overwritten when enabled; virtual/shadow tables have caveats.
[VACUUM](https://www.sqlite.org/lang_vacuum.html) rebuilds the database, removes deleted content
and needs temporary disk space; active transactions/readers can prevent completion.
[Journal modes](https://www.sqlite.org/pragma.html#pragma_journal_mode) distinguish DELETE
(journal removed at commit), PERSIST (header cleared, file retained) and persistent WAL mode.
Jobcu restores DELETE mode before resetting rows and compacts afterwards, with fictional tests
for all three starting modes. This verifies app-file behavior, not SSD/OS-snapshot erasure.

## Implemented job sources

The registry is `src/jobcu/sources/__init__.py`; requests go through `sources/http.py` and budgets
through `sources/budget.py`. A failed source reports its own status and does not stop others.
Countries below describe the adapter's scope, not complete market coverage.

| Source | Scope and method | Evidence and caveats |
|---|---|---|
| Adzuna | Ten supported countries; official API, app ID/key | No Ireland; descriptions are summaries. Blocked ad pages are not fetched. |
| Reed | UK; official API/key, job details | List dates have day precision; full details are separate. |
| Bundesagentur | Opt-in: off unless the person accepts its terms | [Access hold](#bundesagentur-access-hold--2026-10-17) and [owner's decision](#bundesagentur-opt-in--2026-10-30). |
| JobsIreland | Ireland; public list and job pages | Match titles locally; an empty first page may be a service failure. |
| Arbeitnow | Germany/UK feeds; public API | Free-text locations need interpretation. |
| FreeHire | Every country; public search API, no key | Employers' own ads plus some board copies; [check](#freehire--2026-11-02). Some employers are named by their career site's address ("riedelcommunications"); the duplicate rules read it as the spaced name. |
| jobs.ac.uk | UK/Ireland; search pages and JobPosting data | Academic/research/technical jobs; personal-use terms. Its JobPosting data marks hybrid jobs remote too; the listing's "Hybrid" decides. Closing dates come as midnight of the closing day; Jobcu reads any midnight closing time as the whole day. |
| Gradcracker | Opt-in: off unless the person accepts its terms; UK (a few Irish jobs) graduate lists of the areas the search words name | No dates: a job new on a list since the last reading counts as posted that day, and only such jobs are passed on ([record](#gradcracker--2026-11-25)). |
| EURAXESS | Supported countries; research-job pages | Throttling and per-search request limits apply. |
| JobTech | Sweden; public JobSearch API | Full text; local timestamps and paging limits need handling. |
| service.bund.de | Germany; RSS and job pages | Feed has a bounded recent window. |
| Teaching Vacancies | England; API and job pages | OGL attribution applies; page text adds requirements. |
| NHS Jobs | England/Wales; XML search and job pages | Full person specifications need page parsing. |
| Le Forem | Belgium; open structured dataset | CC BY-SA attribution; summary evidence, blocked job pages. |
| Werken voor Nederland | Netherlands; sitemap and job pages | Sitemap lastmod is not a posting date. |
| NAV | Norway; public experimental feed token | Production-token permission is a separate owner/account decision. |
| Employer career systems | Directory plus discovered employers; public lists, feeds or sitemaps | Check each employer host's permission and full-ad evidence. |

Career adapters: Ashby, Avature (opt-in, [Siemens' terms](#avature-siemens-and-siemens-energy--2026-11-24)),
d.vinci, Eightfold, Greenhouse, Jibe, Lever, Oracle, Personio, Phenom (opt-in,
[ABB's terms](#phenom-career-sites--2026-11-24)), Prospective, Recruitee, generic job
sitemaps, employers' own job list pages ([2026-11-25](#employers-own-job-list-pages-and-german-application-systems--2026-11-25)),
SmartRecruiters (opt-in, [its terms](#smartrecruiters-career-pages--2026-11-24)), Jobvite
(opt-in, [its terms](#jobvite-career-sites-power-integrations--2026-11-26)),
Softgarden, SuccessFactors, Teamtailor, Workable and Workday.
Recruitee, SuccessFactors and Teamtailor career sites are also recognised on an employer's own
address (Recruitee's answers the same public `/api/offers/` there).
`src/jobcu/data/employers.json` is the directory; `tools/check_employers.py` is its maintenance tool.
Directory membership does not establish reachable vacancies or engineering recall.

## Access and protocol records

### TU Berlin's job exchange (Stellenticket) — 2026-11-26

Stellenticket (`stellenticket.tu-berlin.de`) is TU Berlin's job exchange: its own posts (research
and doctoral positions) and those employers place there for its students and graduates. robots.txt
allows everything and names its sitemap, which lists 275 jobs, each in German
(`/stellenangebote/{number}`) and English (`/en/job-offers/{number}`), all dated the day the sitemap
was written. Each job page carries JobPosting data naming the employer that hires (a federal
research institute's post was read with its posting day, Berlin and the ad). The addresses name no
title, so it is read like BMW's site (`"titles": false`): the first search records the list, and
from the next one only the pages of jobs new on it are opened, dated by their first sight; the
directory's pattern names each job by its number, so the two languages are one job. DE 20 of the
20 pages surveyed. Universities' other job systems vary (interamt, their own pages): not read.

### Research employers: DLR and the Leibniz institutes — 2026-11-26

- **DLR** (German Aerospace Center; electric aviation propulsion in Cottbus, vehicle concepts in
  Stuttgart, energy systems in Oldenburg, quantum sensors in Hannover): a SuccessFactors career
  site of its own, `jobs.dlr.de`, whose sitemap lists its job pages (DE 278 of its jobs, ES 3).
  A live read with an electronics engineer's search words over seven days gave an
  "Elektronikentwicklerin (w/m/d) für Quantensensoren" in Hannover with its full ad.
- **The Leibniz Association's job list** (`www.leibniz-gemeinschaft.de/en/careers/jobs`: the
  vacancies of its institutes, among them the Ferdinand-Braun-Institut's GaN power electronics
  and IHP's microelectronics): one page, each title a link to the job's page, the institute and
  its town written below it; the job pages carry no job data and are read as text. robots.txt
  answers 404 (no rules). DE 13 of the pages surveyed.

Also checked: the Helmholtz Association's EURAXESS export
(`www.helmholtz.de/en/helmholtzdatensaetze/news-und-presseinformationen/stellenangebote/euraxess-xml-export`,
67 offers, almost all doctoral and postdoctoral posts in the sciences, also listed on EURAXESS): no
reader. The Semiconductor Catapult (formerly the Compound Semiconductor Applications Catapult;
power electronics in Newport) lists its vacancies through Occupop, which Jobcu has no reader for.

### Workday lists that name no posting day — 2026-11-26

MBDA's German Workday site (`mbda.wd3.myworkdayjobs.com/MBDA-DE`, 165 jobs) lists each job's
title, place and vacancy number but no "Posted ..." day, and has no country filter. A live read
with an electronics engineer's search words over seven days returned all 165 jobs with an
unknown date, every one a title the search words miss, so each search would have read its whole
list (nine pages) and handed all of them to the person's AI again. The 163 Workday copies in the
last saved search all had a day, so such sites are rare. Their jobs are now dated by their first
sight on the list, as SuccessFactors' and Avature's are (`listmemory`): the first search records
the list; from the next one, a job new since the last reading counts as posted that day and one
listed since before the window began as older. The reading is remembered per country where the
site filters by country.

### Employers behind good job-site cards, read from their own sites — 2026-11-26

Saved search results name employers whose good matches came only through job sites
(`tools/unread_employers.py` in the maintainer's tools; most are agencies). The real employers
among them were looked up as in the record below (FreeHire's job addresses, robots.txt first,
each list read once):
- **thyssenkrupp, with TKMS** (Atlas Elektronik's sonar and electronics development in Bremen,
  naval shipbuilding in Kiel and Wismar, and the group's other companies): one job site under
  two addresses, `jobs.thyssenkrupp.com` and `jobs.tkmsgroup.com`, whose sitemaps list the same
  884 jobs (`/en/job/{title}-{town}/{number}`, each with its day); TKMS's pages answer at its own
  address. Read from thyssenkrupp's sitemap only, so no job is read twice. Each job page carries
  JobPosting data (a "Designer/Layouter" in Bremen, posted 24 November, with its full ad). robots.txt
  closes only the API, newsletter, sign-in and profile pages.
- **Huawei R&D UK** (Teamtailor `huaweiuk`: research and laboratory jobs in Cambridge; GB 56).
  Huawei's research centre in Germany was already read.
- **Proxima Fusion** (Ashby `proxima-fusion`: fusion power plant engineering in Munich; DE 50),
  **Hypersonica** (Lever `hypersonica-prod`; Munich and London; DE 65, GB 30), **GKN Aerospace**
  (SuccessFactors `careers.gknaerospace.com`; Bristol and Germany; GB 58, DE 14).
- **Sunfire** (electrolysers, Dresden): Softgarden's newer layout on `sunfire.career.softgarden.de`,
  read through its sitemap as NewTec's (DE 18). **pro-beam** (electron-beam systems, Gilching):
  its umantis list `recruitingapp-5365.de.umantis.com/Jobs/All`, read as Diehl's (DE 19).
  **TOPTICA Eagleyard** (laser diodes, Berlin): Softgarden `toptica-eagleyard` (DE 4); TOPTICA's
  own jobs are on helixjobs, which Jobcu has no reader for.

Not readable or not added: VINCORION (power electronics in Wedel; its vacancies come through
b-ite's script loader, which needs the employer's key), Weller Tools (XING only), Molex, Terepco,
Sikora, INELTA, Redur, ESMC, SYOS Aerospace and Indra Renewable Technologies (no list of their
own found), enqt (coveto). Bosch, Clarios, Advantest and Saab were checked on 2026-11-24.

### Lists paged by buttons and whole-card links: Jungheinrich, Ziehl-Abegg, Hager — 2026-11-26

- **Jungheinrich** (forklift drives, chargers and motor inverters; development in Norderstedt and
  Moosburg) lists its jobs on onlyfy (`jungheinrich.onlyfy.jobs/en`): ten of its 172 jobs a
  page, newest first, each a link around the job's card (title in a heading, then "Hamburg |
  Full-time employee | 26.11.2026"), and the page's buttons for further pages have no addresses.
  The same list answers `?page=2` with the next ten, whose job links carry the visitor's list
  page (`?career_page_search=page%3D2`). Its job pages carry JobPosting data (the whole ad, the
  posting time, the place). robots.txt closes only the recruiters' area and language switching
  and asks for `Crawl-delay: 1`; it has no sitemap (404). The directory now names such a list's
  page parameter (`"pages": "page"`): the reader reads its pages by number while each brings new
  jobs, within its ten-page limit (the newest 100 jobs, 11 requests and about 11 seconds), and
  leaves the visitor's list page out of each job's address. DE 10 of the pages surveyed.
- **Ziehl-Abegg** (EC motors and their drive electronics; Künzelsau) moved its vacancies to
  `karriere.ziehl-abegg.de/jobs`: one page of 98 jobs, each a link around its card (title in an
  `<h4>`, then level, department and "Deutschland, Künzelsau"); its job pages
  (`/detail/job/{24-digit code}`) carry no job data and are read as text. The reader took the
  whole card's text for the title and found no place, so the check placed all twenty surveyed
  jobs abroad; now a job link holding a heading takes the heading as the title and the rest of
  its card as the job's details. Checked on the twenty other list-page employers' current lists:
  no title or place changed. robots.txt closes only the site's technical folders. DE 20.
- **Hager** (electrical distribution, EV charging and energy management; development in
  Blieskastel) runs a Radancy career site whose sitemap (`careers.hager.com/en/sitemap.xml`)
  lists 224 job pages (`/en/job/{town}/{title}/3352/{number}`) beside category, location and
  employment pages; the directory gives the job pages' pattern. Each job page carries JobPosting
  data. robots.txt closes only `/search-jobs/`. DE 7, GB 2, IE 1 of the pages surveyed.

Also checked: Safran's job site (Talentsoft, `safran.profils.org`) closes everything to robots,
so it stays unread.

### Field employers on career systems Jobcu reads — 2026-11-26

Found by asking FreeHire's public search once per employer name (`q_fields=company`, 58 names of
electronics, drives, power and instruments employers in Germany, the UK and Ireland that the
directory lacked): its results carry each job's real address, which names the employer's career
system. Every list below comes from such addresses (no Workday address was guessed) and was read
once with `tools/check_employers.py`; robots.txt was read first for every host.

- SuccessFactors: **ifm** (`jobs.ifm.com`; sensor and power electronics in Tettnang; DE 75),
  **Kärcher** (`careers.kaercher.com`; DE 116, GB 7), **Stiebel Eltron**
  (`karriere.stiebel-eltron.de`; heat-pump electronics in Holzminden; DE 69), **AGCO (Fendt)**
  (`careers.agcocorp.com`; DE 137), **CLAAS** (`recruiting.claas.com`; DE 103) and **Kistler**
  (`jobs.kistler.com`; DE 12). A live read with an electronics engineer's search words gave
  ifm's "Elektroingenieur als Hardwareentwickler für induktive Sensoren" and "Entwicklungsingenieur
  Elektronik Drucksensorik" with their full ads. An old ifm job address from a job board
  (`/job/...aspx?LCID=2057`) answered 403 ("forbidden by administrative rules"): an address of the
  site's earlier system, which Jobcu never reads; the career site itself answered.
- Workday (wd3, wd103 and wd502 servers, not the wd1/wd5 ones behind the human check): **Miele**
  (`miele.wd3.myworkdayjobs.com/miele-jobs`; DE 78, GB 12, IE 3), **Pepperl+Fuchs**
  (`pepperlfuchs.wd103.myworkdayjobs.com/PepperlFuchs`; DE 26), **Bürkert**
  (`burkert.wd502.myworkdayjobs.com/burkert-career`; DE 54), **MBDA (Germany)**
  (`mbda.wd3.myworkdayjobs.com/MBDA-DE`; Schrobenhausen and Aschau; DE 165; MBDA's UK site was
  already read) and **Megger** (`megger.wd3.myworkdayjobs.com/MeggerCareers`; test instruments
  for power networks in Dover and Germany; GB 2, DE 5).
- Oracle: **Ford** (`efds.fa.em5.oraclecloud.com`, site `CX_1`; Cologne and Aachen; DE 19,
  GB 10) and **Cummins** (`fa-espx-saasfaprod1.fa.ocs.oraclecloud.com`, site `jobsearch`; GB 69,
  DE 3, IE 2).
- Greenhouse: **Cambridge Consultants** (`cambridgeconsultantslimited`; electronics and systems
  engineering, graduate roles; GB 82). Its board is on Greenhouse's EU host, and the public Job
  Board API answers for it as for any board.
- Teamtailor on the employers' own addresses: **Surrey Satellite Technology**
  (`jobs.sstl.co.uk`; spacecraft electronics in Guildford; GB 11) and **Ceres Power**
  (`careers.ceres.tech`; fuel-cell and power systems in Horsham; GB 8).
- SmartRecruiters (opt-in): **Enoda** (`ENODA`; grid power electronics in Edinburgh; GB 3).
- A rexx list page: **LAPP** (`www.lappcareer.com/stellenangebote.html`; cables and charging
  technology in Stuttgart; DE 20). Its robots.txt closes the site only to generic HTTP libraries
  by name (python-requests, wget and others), not to Jobcu's own named client.

Not added: Balluff (its careers page answered with a bot check: left alone), JUMO (its career
host refused the connection), Murrelektronik (its vacancies are built by scripts), ebm-papst
(Cornerstone, which Jobcu has no reader for: 128 ads), Hager (Radancy), Safran (Talentsoft),
ITM Power (JOIN, decided 2026-11-25), ePropelled (Zoho Recruit), Hyundai Motorsport (its
Softgarden name answered 404), Heidenhain (its ads are PDF files only), Eberspächer,
Kostal, Marquardt, Wilo, BSH, Festool, Recom, Sumida, Dräger, Melexis, WAE, Pulsiv, Protean,
Saietta, Turntide, Equipmake, 42 Technology, IQE and Plextek (no list of their own on any
system; their jobs reach Jobcu through job sites and the Bundesagentur). Already read under
another entry: Semikron Danfoss (in Danfoss's SuccessFactors site), Tesat-Spacecom (Airbus's
Workday site lists its jobs: 36), Hitachi Energy (Hitachi's Workday site); already in the
directory: Nexperia, Oxford
Instruments, Lotus and MBDA's UK site.

### Job lists whose links only say "View job details" — 2026-11-26

TDK-Lambda (power supplies; its UK design and manufacturing centre in Ilfracombe, its EMEA head
office in Achern) lists its vacancies on its own site (`www.emea.lambda.tdk.com/uk/about/
tdk-lambda-recruitment` and `/de/...`): each job is a heading with its title, a line with its
place and a link that says only "View job details" (`/uk/about/tdk-lambda-job/2277`); the job
pages carry no job data, open with the site's own heading ("About TDK-Lambda") and a country
switcher ("Change Location : France"), and give the ad after the job's title with "Location :
Kingsley Avenue, Ilfracombe, Devon". The list-page reader took every link's text for the job's
title and the text after it for its place, so all five UK jobs were called "View job details",
and the page reader took the switcher's France for the place. Now a link whose whole text only
invites to open the job ("View job details", "Read more", "Mehr erfahren", "Zur Stelle",
"Apply now", "Voir l'offre") takes its title from the last heading before it, and its place from
the text between that heading and the link; a job page read as text starts where it names the
title its list gives. robots.txt closes only the site's technical folders; no terms of use
against reading were found. Added: TDK-Lambda (UK), 5 jobs (Senior Electrical Design Engineer,
"Power + Design Engineer", test engineering), and TDK-Lambda (Germany), 7.

### Murata Power Solutions; more field employers checked — 2026-11-26

**Murata Power Solutions** (DC-DC converters and power supplies designed in Milton Keynes and
Bordon) runs a SuccessFactors career site on its own address, `careers.murata-ps.com`
(`/job/Milton-Keynes-...-MK8-0ES/1286750000`), read by the SuccessFactors reader: GB jobs and
others in the US and Canada. The group's `jobs.murata.com` (already in the directory) lists
other Murata companies.

Checked and not added: Diodes Incorporated (its careers page answered with a bot check: left
alone), Leuze electronic (its HR4YOU list frame builds its jobs with scripts), Toshiba Electronics
Europe (`careers.toshiba.eu`: list built by scripts), Fuji Electric Europe and STÖBER (no list of
their own found). ROHM Semiconductor (Personio) was already in the directory.

### Job pages that show their ad in a frame: iCIMS career sites — 2026-11-26

An iCIMS career site (`{company}.icims.com`) lists its jobs in a sitemap
(`/sitemap.xml`: `/jobs/{number}/{title}/job` with each job's last change) and its robots.txt
closes only referral, login, candidate, reminder and "connect" pages. A job's page carries no
job data itself: it embeds a frame from the same site (`/jobs/6336/manufacturing-engineer/job?in_iframe=1`),
and that frame has the whole ad with JobPosting data (title, posting day, town, country, type).
The sitemap and list-page readers now read the frame a page embeds from its own site when the
page has no job data (as a browser shows it; one more request, only for such pages); the job
keeps its page's address for the person's link. Frames of other sites (video, analytics) are
never read.

Added: **TT Electronics** (power modules and electronics manufacturing in Bedlington, Rochdale,
Manchester and Eastleigh; `global-portal-ttelectronics.icims.com`, 65 jobs, 12 in the UK of the
20 newest; its website terms, linked from the portal, say nothing of automated reading),
**Bruker** (scientific instruments; electronics development in Berlin, Hamburg, Bremen,
Karlsruhe, Leipzig: `germancareers-bruker.icims.com`, 47 jobs, and
`internationalcareers-bruker.icims.com`, 150) and **Ricardo** (engineering consultancy;
power-electronics and controls graduate roles in Leamington Spa and Shoreham:
`careers-ricardo.icims.com`, 13 jobs). A live read with an electronics engineer's search words
over 30 days gave Bruker's "Hardwareentwickler Elektronik" (Leipzig) with its full ad. The
iCIMS sites of Schneider Electric, Arm and AMD stay unread: their robots.txt closes them.

### Jobvite career sites: Power Integrations — 2026-11-26

Power Integrations (gate drivers and power conversion ICs; its gate-driver development in Ense
and field applications in Munich, a lab in Cambridge) lists its jobs on Jobvite:
`jobs.jobvite.com/power-integrations/jobs`, 46 jobs, each link under its title with its place
beside it ("Munich, Germany"), each job page with JobPosting data (posting day, country, the
whole ad). The host answers robots.txt with 404 (no rules). Jobvite's terms of use
(`www.jobvite.com/terms-of-use`) say of all content "on or through the Site": "You may not copy,
distribute, scrape ... any of these materials"; no legal action against readers of job pages was
found. So Jobvite is read as an opt-in source, like Avature or SmartRecruiters: only for a person
who switches it on in Settings and so accepts that for their own job search. It is read like
employers' own list pages (`sources/jobvite.py`), and a Jobvite job link in a search's results
names its company's list, so Jobcu learns other Jobvite employers by itself for such a person.

The directory check opened the list's first twenty job pages (all abroad: San José, Penang,
Pasig City) and found no supported country, so the company would have been dropped. A list page
names each job's place beside its link; the check now also counts the countries that text
names, as it counts the towns at the end of a sitemap's job addresses (record below): Power
Integrations hires in Germany and the UK, and elsewhere.

### More power-electronics, drives and motorsport employers — 2026-11-26

Found by web searches for the field's employers in Germany and the UK that no source covered;
each list asked once, robots.txt first. Added with existing readers:
- **Maschinenfabrik Reinhausen** (Regensburg; grid power electronics, converter control,
  hardware-in-the-loop): its application portal's sitemap `career.reinhausen.com/sitemap.xml`
  (127 job pages `/{number}-{title}/job.html` with JobPosting); robots.txt asks for
  `Crawl-delay: 10`, which Jobcu now keeps. DE 13.
- **AEG Power Solutions** (Warstein; UPS and industrial power electronics): Softgarden `aegps`.
  DE 16, ES 9.
- **Bender** (Grünberg; insulation monitoring, EV charge controllers) and **Isabellenhütte**
  (Dillenburg; precision resistors and current measurement): rexx lists
  (`karriere.bender.de/stellenangebote.html`, `karriere.isabellenhuette.com/stellenangebote.html`;
  robots.txt closes them only to generic HTTP libraries by name). DE 18 and DE 10.
- **Vincotech** (Unterhaching; power modules; a Mitsubishi Electric company): its list page
  `www.vincotech.com/career/open-positions/` (job pages without job data, read as text). DE 1,
  HU 5.
- **Cosworth** (Northampton; electronics and powertrain): Teamtailor on its own address
  `currentopportunities.cosworth.com`. GB 11.

Not added: Red Bull Powertrains (its Workday site named in a job ad answered 422), KEB
Automation (vacancies built by scripts), Benning, Baumüller, SIEB & MEYER, Drive System Design,
Advanced Electric Machines (no list of their own found), Mitsubishi Electric Europe (its German
jobs reach Jobcu through the Bundesagentur), KACO new energy (a Siemens company), EA
Elektro-Automatik (its careers address refused the connection). Already in the directory: Jaguar
Land Rover.

### A job page's country outside the supported ones — 2026-11-26

TT Electronics' job pages (iCIMS) name each job's country in their JobPosting data, and its site
lists jobs in the UK, the US, Mexico, China and India. A page for a power-electronics job in
Olathe, Kansas, says `"addressCountry": "US"`. Jobcu read only the supported countries from that
field, so "US" counted as no country written; the directory check then saw the employer's jobs as
UK jobs and jobs of unknown place ("elsewhere" false), and a search placed the Kansas job in the
UK, the one country the employer's entry names. Now a JobPosting country outside the supported
ones (any ISO 3166 two- or three-letter code, or a country's name such as "Mexico") marks the job
abroad, and the job leaves the search as other foreign jobs do; a job offered in several places
is in the first supported country they name; three-letter codes of supported countries ("DEU",
"GBR", "IRL") are read too. Words that name no country ("EMEA", "Remote") and "NA" (written for
"not available") still decide nothing. The same applies to the employer's own pages the Workday
reader opens.

### Crawl delays in robots.txt — 2026-11-26

Maschinenfabrik Reinhausen's application portal (`career.reinhausen.com`; power-electronics
development in Regensburg) asks every robot for `Crawl-delay: 10` in its robots.txt. Jobcu kept
such pauses only where they were written into its own table (service.bund.de's 30 seconds,
Lever's 1 second), so a new site's request was honoured only if someone added it by hand. Now a
career site's robots.txt, read once a search, sets that site's pace when it asks for a delay:
the delay of the group for Jobcu or, without one, for every robot, at most a minute between
requests. Reading the file also changed in one way: a group whose rules are only an empty
`Disallow:` (allowing everything) or a `Crawl-delay` now ends at the next `User-agent` line, as
the standard says; before, the next robot's `Disallow: /` was taken as Jobcu's too.

### Electronics and power employers read from their own sites — 2026-11-26

Nineteen employers in electronics, power conversion, drives and automation in Germany and the UK
were neither in the directory nor read through another source. Each one's real job list was
found by a web search and asked once, robots.txt first.

Added, with existing readers (jobs in the supported countries on the day):
- **YASA** (axial-flux motors, Oxford): Rippling list `ats.rippling.com/yasa/jobs` (list-page
  reader, as MBRYONICS); 2 jobs. Its old `careers.yasa.com` refused the connection.
- **Raspberry Pi** (Cambridge): Workable `raspberrypi`; 4 UK jobs.
- **Lenze** (drives, Aerzen): rexx list `karriere.lenze.com/stellenangebote.html`, job pages with
  JobPosting; DE 8, AT 2. Its robots.txt closes the site only to generic HTTP libraries by name
  (wget, python-requests ...); Jobcu reads under its own name, for which every page is open.
- **FEV** (powertrain and vehicle engineering, Aachen): d.vinci on its own host `career.fev.com`;
  DE 34 and 13 elsewhere in Europe.
- **McLaren Automotive** (Woking): Avature, `mclarencareers.mclaren.com/careers/SearchJobs`; 97 UK
  jobs (robots.txt allows `/careers`; the site links no terms of its own). Read with the Avature
  switch. Its pages write the ad under labelled headings ("What You'll Do", "What You'll Bring")
  and cut the standard job data to the ad's first sentences, so the Avature reader now also keeps
  labelled fields of 150 characters or more as parts of the ad, and the longer of the two ads
  (a power-electronics systems job: 361 characters before, 4,870 now).
- **ams OSRAM** (Regensburg, Garching, Premstätten, Exeter): its job sitemap
  `jobs.ams-osram.com/sitemap.xml` (271 job pages with JobPosting); countries from the job
  addresses (record below).
- **Beckhoff Automation** (Verl): its German site's sitemap `www.beckhoff.com/de-de/sitemap.xml`
  (12,407 addresses, 2.7 MB, one request a search) has its ~70 German job pages
  (`/de-de/unternehmen/stellenangebote/{title}-{town}.html`, JobPosting on each); the directory's
  pattern picks them.
- **Weidmüller** (Detmold): rexx list `www.weidmueller.de/de/jobboard/stellenangebote.html`;
  DE 19, CH 1.
- **Preh** (Bad Neustadt): rexx portal `preh8-portal.rexx-recruitment.com/stellenangebote.html`,
  whose links (`career.preh.com/...?yid=3938`) lead to the portal's job pages with JobPosting;
  DE 9 and abroad.

A live read of each with an electronics engineer's search words over 30 days found, among
others, Lenze's "Hardware Entwickler Electronics", Weidmüller's "Senior System Architect Power
Electronics" (Paderborn), ams OSRAM's "Application Engineer - Electronics Display" (Regensburg)
and McLaren's "Senior Systems Engineer, Power Electronics" (Woking), each with its full ad.

Already covered: Hitachi Rail (Hitachi's Workday site lists its UK jobs).

Not read, and why: McLaren Racing (robots.txt closes everything); WAGO (its job list comes from
its site search, which robots.txt closes; its jobs reach Jobcu through the Bundesagentur); JCB,
Eberspächer, Varta and Rosenberger (their lists are built in the browser by scripts, with no job
sitemap or feed found); Turbo Power Systems (adverts are PDFs, only when hiring; none now);
Imagination Technologies (PageUp list readable, job pages without job data; mostly GPU chip
design); LEONI (its SmartRecruiters page leads to its own site, which the SmartRecruiters reader
doesn't follow); STFC (UK SBS's SelectMinds site refused the connection; STFC's jobs reach Jobcu
through jobs.ac.uk); Power Integrations (Jobvite; Jobvite's terms of use forbid scraping content
on or through its site: only an opt-in source could read it).

### Countries a sitemap's job addresses name — 2026-11-26

The directory check opens a job sitemap's twenty newest pages to see which countries its
employer hires in. On a large international site they can all be abroad: ams OSRAM's sitemap
(`jobs.ams-osram.com/sitemap.xml`, 271 jobs) gave twenty pages in Austria, Malaysia, the US and
elsewhere and not one of its German jobs, so searches in Germany would have skipped it. Its
addresses end in the job's town (`/en/job/Hardware-Engineer-d_m_f-Regensburg/20931`): 19 end in
Regensburg, Munich, Garching or Jena and 12 in Exeter or Leeds. The check now also counts the
countries the last one to three words of each job address name (the place names Jobcu knows),
for countries the opened pages didn't show, from the sitemap it has already read: no more
requests. A wrong country there costs one reading of the list in a search of that country;
towns are still recorded only from pages. List pages are left out (their own text beside each
link names the place, and their addresses end in numbers or languages).

### UKAEA's job list, and pages without a day or a place — 2026-11-25

The UK Atomic Energy Authority (fusion research at Culham, Rotherham and West Burton; a graduate
engineering scheme; power-supply and electrical engineering jobs) lists its vacancies on
`careers.ukaea.uk/current-vacancies/` (WordPress; robots.txt closes only `/wp-admin/`). Each card
links `/job/<title>/` and names the site ("UKAEA Culham, Oxfordshire", "Rotherham, United
Kingdom"); the job pages carry no JobPosting data and leave their "Site Location" empty, and
neither gives a day. Its job sitemap (45 pages) keeps filled jobs whose pages answer 404, so the
list page is read (list-page reader; 10 jobs that day, 2 requests). No legal action against readers
of job ads was found; its careers site has no terms of use of its own.

Two general rules came with it: a job whose page gives no posting day takes the day its list
gives, else its first sight on the list (before, a job matching the search words whose page had
no day stayed "Posting date unknown" however new); a job whose page names no place takes the text
its list shows beside its link, as title-only jobs did, the country only where that text or the
employer's own countries resolve it (never "abroad" from it: UKAEA's text is sometimes only
"Engineering"). An empty place label on a page no longer takes the next line as the place unless
that line names a place. The directory check counts 8 of UKAEA's 10 jobs in the UK by these texts.

Added with it, UK employers in fusion and power conversion that no saved search had shown: Tokamak
Energy (Workable, 4 jobs), IONATE (Workable, 8; grid-connected power converters) and Nidec Control
Techniques (drives R&D in Newtown, Powys: its own list at `moen.nidec.com/.../current-vacancies`, 6
jobs; robots.txt allows everything; job pages without job data, read as text: "Hardware Engineer",
"Location: Newtown, Powys, UK"). The directory's Nidec Workday site lists only Greece and Italy.
Equipmake's jobs weren't found (one posting on Breathe HR, which Jobcu has no reader for).
### Pinpoint career sites, and BambooHR — 2026-11-25

**Pinpoint.** A company's feed, `https://{company}.pinpointhq.com/postings.json` (or the same
address on a career site of the company's own that Pinpoint serves: Sagentia's
`careers.sagentia.com`, OCU Group's `careers.ocugroup.com`), lists every published job with its
title, place (town, county, postcode), type, workplace (on site, hybrid, remote), closing time and
the whole ad as the career page shows it (description, responsibilities, skills, benefits). robots.txt
closes only `/mydata`, `/admin` and `/companies`. The feed gives no posting date; each job's page
carries JobPosting data with the exact posting time and the country. Pinpoint's own terms for
visitors weren't found; the feed is what each company's career page itself loads. Jobcu reads the
feed (one request a company and search), notes each job's first sight (`listmemory`), opens the
pages of the jobs whose titles match the search words (at most 30 a company, remembered once read)
for their posting time, and gives the titles the words miss to the person's AI when the job is new
on the list. A UK postcode or an Eircode in the place gives the country. Pinpoint addresses in job
sites' links are recognised, so more such employers are learned by themselves.

FreeHire's catalogue (hardware, embedded and engineering-design ads on Pinpoint) named 13 UK
employers, one in Ireland, none in Germany. Checked once each with `tools/check_employers.py`:
Rowden Technologies (47 jobs in the UK; RF hardware), OCU Group (82; a graduate design engineer
scheme), Alternative Heat (29 UK, 14 Ireland, 3 Germany; electrical design), Plessey (22), Sagentia
(20; electronics engineers), AccelerComm (15), Aston Martin F1 (13), inMusic Brands (5), LiveLink
Aerospace (2; an electronics engineer in Havant), OxTS (1; a senior electronics engineer). Thermon's
robots.txt closes its feed: not read.

**BambooHR not read.** A company's list (`{company}.bamboohr.com/careers/list`, JSON without dates,
each job's `careers/{id}/detail` with its day) answers and robots.txt allows everything, but
BambooHR's [terms of service](https://www.bamboohr.com/legal/terms-of-service) forbid using "any
robot, spider, other automated device, or manual process to monitor or copy any content from the
Service", and only one employer in the field was seen on it (OPAL-RT, power-electronics
simulation, its UK jobs few). Not built; reconsider only with many more employers in the field.

### Mercedes-Benz's job sitemap, and sitemaps whose addresses name no job — 2026-11-25

**Access.** `jobs.mercedes-benz.com/robots.txt` allows every robot everything and names its
sitemap, an index of four: German, English, US English (only the start page) and Hungarian. Each
lists the group's open jobs worldwide (959 German addresses, 929 English, 916 Hungarian; 967
different jobs), and every job page carries JobPosting data: title, full ad, posting day, town,
country and the hiring company (Mercedes-Benz AG, its Chinese, Polish and Hungarian companies...).
The site's own job list is built in the browser, so the sitemap is the way in. Its careers terms
([General Terms & Conditions](https://group.mercedes-benz.com/careers/general-terms-conditions.html))
are about misuse of accounts and uploaded content and say nothing about reading job ads; no legal
action by Mercedes-Benz against readers of job ads or job aggregators was found (web search,
2026-11-25). Jobcu reads the sitemaps (five requests a search) and opens only the pages of jobs whose
address matches the search words, or that are new on the list and kept by the person's AI.

**What the reader needed.** The addresses speak of no job (`/de/pcb-pcb-layout-design-engineer-
248186-mer000469f`), so the sitemap reader, which keeps addresses with "job", "stelle" and the like,
kept none. The directory now gives such a site the pattern of its job pages' addresses (`jobs`, as
for list pages); its first group names the vacancy. Mercedes-Benz numbers each language's page apart
(`-233242-` German, `-233238-` English) and keeps one code for the vacancy (`bei00000us`): the code
says which addresses are one job, so it is read once, in the searched country's language, and it
isn't part of the title the address spells. The sitemap dates every page to the seconds it was
written in, so its dates order nothing: pages new on the list since its last reading are opened
first (also on every other sitemap and list page), and the directory check, which looked at the
first twenty pages (alphabetical: China, Hungary, no German job), samples pages spread over the
whole list when the dates span less than a day (9 of 20 in Germany).

**Measured.** With the saved search words of an electronics engineer, 6 of the 967 titles matched
(in China and Poland, older than the window); the German list is mostly internships and working
students now, with a PCB layout, a power-net and a high-power charging engineer and the Tech Trainee
programme among the rest. A repeat reading takes 6 requests (pages are remembered).

Porsche's job sitemap (`jobs.porsche.com`, 759 pages, robots open) dates its pages, but the pages
carry no JobPosting data and their addresses no title (`index.php?ac=jobad&id=22236`); BMW's
(`bmwgroup.jobs`, robots open, 748 job pages) gives neither dates nor titles and no JobPosting data.
Both are read since the same day: [record](#bmws-and-porsches-job-pages-without-job-data--2026-11-25).

### BMW's and Porsche's job pages without job data — 2026-11-25

**Why.** In every saved search (search 21: 2,097 job copies over 72 hours) not one job of BMW,
Porsche or Mercedes-Benz arrived: their own sites are where they advertise, and BMW's and Porsche's
pages carry no JobPosting data, so search engines' job listings (and JSearch) don't show them either.

**Access.** BMW: `www.bmwgroup.jobs/robots.txt` names only its sitemap (no rule), and the site's
[terms of use](https://www.bmwgroup.jobs/en/general/terms-of-use.html) cover the career pages'
legal owners and the application system, nothing about reading job ads. Its sitemap (2.7 MB, one
request) lists 748 job pages, `/en/jobfinder/job-description-copy.<number>.html`, without dates.
The site loads a bot-detection script; its pages answered Jobcu's client normally. Porsche:
`jobs.porsche.com/robots.txt` names only its sitemap; the portal links no terms of use, only its
privacy pages. Its sitemap lists 745 job pages, `/index.php?ac=jobad&id=<number>`, with the dates
they were last changed (which don't establish a posting day). No legal action by either against
readers of job ads or scrapers was found (web search, 2026-11-25).

**What the pages give.** A heading with the title, the ad in the page's `<main>`, the place under a
label ("Location: Munich" on BMW's, "Einsatzort: Stuttgart" on Porsche's; BMW's also put department,
town and day above the title) and the hiring company under a label ("Company: BMW AG",
"Gesellschaft: Porsche Zentrum Bensberg"). Porsche's places are often districts and small towns
(Zuffenhausen, Weissach, Bensberg) whose names alone don't tell the country; they are placed in
the one of the employer's countries that has them.

**Reader.** The directory gives both sites the pattern of their job pages (`jobs`) and says that the
addresses name no title (`"titles": false`). A search reads the sitemap whole (list memory) and
opens only the pages of jobs new on it since its last reading, at most 60 a site, which their first
sight dates (as on SuccessFactors sites without dates); jobs listed before are older than the window.
A page without job data is read as text only where the directory names the site's job pages, and
only when its address still names a job page after redirects. Titles the search words miss go to
the person's AI's title check like other career sites' titles. A first reading opens nothing.

Daimler Truck's job search (`jobsearch.daimlertruck.com`) runs on the same platform as Porsche's:
robots.txt names only its sitemap (358 jobs, `//index.php?ac=jobad&id=<number>`, no titles), and
its group's [legal notice](https://www.daimlertruck.com/anbieter-rechtliche-hinweise) says nothing
about reading job ads. Its pages do carry JobPosting data, so only the opening of new pages applies;
the directory check found 9 of its sampled pages in Germany.

**Measured** (a copy of the data folder, the saved search words of an electronics engineer, the
newest 25 of BMW's and 12 of Porsche's jobs made new): BMW 26 requests in 26 seconds, 13 jobs in
Germany (Munich, Regensburg, Landshut, Leipzig; that day mostly internships), each with title,
town, company, its first-sight day and a full ad of 2,700 to 4,200 characters; Porsche 9 jobs in
Germany, its pages remembered from the directory check. The directory check samples 20 pages
spread over BMW's list (no dates): 12 in Germany, one each in the UK, Greece and Hungary.

### Plain job lists recognised by themselves — 2026-11-25

When the person's AI names an employer whose careers page shows no career system Jobcu knows,
Jobcu now looks whether that page (or its job-list link, or its `jobs.`/`careers.` host) lists jobs
as plain links: links of one shape naming at least three different job numbers (a number of four
digits or more, a UUID, or a code of letters and digits; a title spelled before the number is no
part of the shape; shapes whose addresses speak of jobs first). It opens one such job page (at most
three shapes a page) and keeps the list only when that page carries JobPosting data with a title;
the list is then checked like any found employer and read with the list-page reader, its pattern
kept in the person's data folder (migration 27). On the saved pages it found the job links of
dSPACE, Würth Elektronik, Pfisterer, Tyndall, MBRYONICS, Diehl, Rheinmetall's list page and TDK
(whose pages carry no job data, so TDK would not be kept). This happens only in the employer
look-up every 14 days, for employers on no known system.

### Employers found through FreeHire's catalogue — 2026-11-25

FreeHire's public search (`source_type=ats|company`, the last 60 days) was asked twelve
electronics-hardware words in Germany, the UK and Ireland: 369 employers had ads on their own
career systems; those missing from the directory whose list Jobcu can read were checked once with
`tools/check_employers.py` and 52 added. Greenhouse: SiTime (13 jobs in Germany), Rocket Factory
Augsburg (56). Ashby: Neura Robotics (399 in Germany), Black Semiconductor, Tactilia Robotics,
Lumai, Foundational. SuccessFactors: AVL, Heraeus (155 in Germany), STIHL, Enercon, Kannegiesser,
Knorr-Bremse, Mersen, AMETEK (107 in the UK), Bugatti Rimac, Codan, Power Electronics (Spanish
inverter maker; 10 in the UK). Workday: Spellman High Voltage Electronics, TTI Europe, Pickering,
Dover (54 in Germany: SIKORA among its companies), elobau, Multimatic. Personio: quantune, twentyfour
industries, Hive Robotics, sivonic, Quantum Motion, Swissbit. Softgarden: the Plath group's site
(81), F & S Prozessautomation (power converter projects), MagnoTherm. Teamtailor: BYD Europe, Open
Cosmos, Breathe Battery Technologies, Malloy Aeronautics, Marshall, KNDS UK. Workable: Filtronic,
Cambridge GaN Devices, Mesa Quantum Systems, Oxford Quantum Circuits. Recruitee: Quantum-Systems
(151). SmartRecruiters (read for those who accept its terms): Integral Powertrain (with a graduate
electronics role), General Dynamics UK, Elatec, Delta Electronics, Energym, White Lab, Pektron, TTP.
List pages: VACUUMSCHMELZE and JAT (both rexx; [record](#employers-own-job-list-pages-and-german-application-systems--2026-11-25)).
A second pass with graduate and junior words added Babcock (182 jobs in the UK, an electrical
engineering graduate programme among them), Goldwind (wind power; a graduate programme in
Frankfurt) and Graphcore's early-careers board (27 in the UK); most other employers it named
were outside electronics (construction, utilities, retail).

Not added: PA Consulting's and Western Digital's SmartRecruiters pages listed no job in the
supported countries; NewTec's and Burmester's Softgarden sites use Softgarden's newer layout,
which has no list at `/de/vacancies`; both publish a sitemap of their job pages, which carry
JobPosting data, and are read as job sitemaps (NewTec 59 pages, Burmester 6 jobs in Germany).
Five Workday sites on the wd1 and wd5 servers (BD's German and Irish sites, Frazer-Nash on KBR's,
NCR Atleos, Videojet on Veralto's) answered with Workday's human check while the first one read on
that server (Spellman) answered: Workday was then left alone. The same evening (18:57-19:06 UTC+1)
Analog Devices' wd1 robots.txt still answered with the check while its list answered (762 jobs),
and each of the five, asked once and minutes apart at their real addresses (FreeHire's links to
their jobs), answered: they are read since. BD has 35 jobs in Germany and 20 in Ireland (two sites
of its own), Frazer-Nash 72 in the UK, NCR Atleos 37 in the UK (hardware engineering in Dundee) and
Videojet 8 in Germany and 13 in the UK. NCR Atleos' location filter writes its sites without a
country ("DUNDEE-GBR"), so its UK towns came out as only Warrington; since then a place that names
no country counts as a town of the one country of the site's own filter that has it (ambiguous
names are left out). Seen on
systems Jobcu doesn't read: Cornerstone (OHB, 11 ads; Weller's owner Apex Tool; Spirax-Sarco),
Rippling (MBRYONICS), umantis (pro-beam), HiBob (Cambridge Aerospace), Zoho Recruit (ePropelled),
digitalrecruiters (AES Aerospace Embedded Solutions), ADP (Advantest, Diodes), beesite
(Mercedes-Benz, read through its job sitemap since the same day:
[record](#mercedes-benzs-job-sitemap-and-sitemaps-whose-addresses-name-no-job--2026-11-25); Porsche).

### Employers' own job list pages, and German application systems — 2026-11-25

**Which German application systems to read.** FreeHire's public facets (its catalogue reads
employers' own systems, rexx, coveto and JOIN among them) counted open German ads per system in
its hardware, embedded and engineering-design categories. Systems Jobcu didn't read: coveto 244
(mostly staffing agencies: Leasotec, Neo Temp, Personalhaus), JOIN 175 (small firms and agencies),
rexx 139 (mostly building and planning firms' draughtsman and TGA jobs), helixjobs 40, Cornerstone
15, umantis 7, onlyfy 7, HR4you none listed. In three days FreeHire first saw 4 coveto, 4 rexx and
1 umantis ads in those categories in all of Germany, and these reach Jobcu through FreeHire
already. So none of these systems got a reader of its own. The employers in electronics that use
them have pages Jobcu can read in other ways: Rheinmetall's HR4you jobs are on its own site and in
its sitemap ([record](#rheinmetalls-job-sitemap-and-sitemaps-in-many-languages--2026-11-25)),
and Würth Elektronik's rexx site lists its jobs on plain pages. Diehl (umantis: its job pages lead
back to its career site) and TDK Electronics (own pages without JobPosting data) are left for now.

**Reader.** Many employers publish a list page of their jobs whose job pages carry JobPosting
data for search engines, whatever system runs behind it. The directory gives such an employer's
list page and the pattern of its job pages' addresses (`jobs`); Jobcu reads the list page and the
further pages it links to for paging (same address, a page in the query; at most ten, and none
after a page that brings no new job), takes each job page's address from links or from the page's
own data, its title from the link's text, its label or that data, and its place from that data or
the text beside the link. Session numbers in addresses (rexx's `sid=`) are left out. Then it works
like a job sitemap: matching titles have their page read, titles new since the list's last reading
go to the title check, the list's first sight dates a page without a date. Where a list's data
names a job's place, that place stands: dSPACE's job pages give the head office (Paderborn,
Germany) for every job, its jobs in Zagreb and Trivandrum included.

**Employers added** (robots.txt allows the list and job pages; legal notices read on 25 November
have no clause on automated reading; one list page and the matching or kept job pages per search):
- **dSPACE** (`www.dspace.com/de/gmb/home/career/jobfinder/stellen.cfm`, job pages
  `fuseaction=einzel&jid=`): 62 jobs in the page's data, in Germany (Paderborn and other sites),
  France, Croatia, India and elsewhere; JobPosting with exact posting times.
- **Würth Elektronik** (rexx, `jobs.we-online.com/stellenangebote.html`, job pages `-j{number}.html`):
  100 jobs a page, two pages; JobPosting with posting day, place and the group company's name.
- **Pfisterer** (its list on `www.pfisterer.com/de/stellenangebote` links MHM eRecruiting pages,
  `pfisterer.mhm.jobs/{number}-...`): 51 jobs; the links are icons whose label names the job.
A live read with an electronics engineer's search words over 30 days found one open
power-electronics development job each at dSPACE and Würth Elektronik (posted in June and August).

**Pages without job data; Ireland (same day).** A listed job whose page carries no JobPosting data
now comes with the list's title and place and its first sight on the list, its link opening the
employer's ad, instead of being lost; a sitemap's page without such data is still no job (it is
usually a page about working there). Style and script blocks in a list are not read as text.
Added: **Tyndall National Institute** (Cork; JazzHR, `tyndallnationalinstitute.applytojob.com/apply`,
11 jobs, research posts in electronics and packaging; robots.txt closes only `/cb`; job pages carry
JobPosting) and **MBRYONICS** (Galway, space photonics and electronics; Rippling,
`ats.rippling.com/mbryonics/jobs`, 13 jobs; robots.txt closes only `/internal/`; its job pages
build the ad with scripts, so its jobs come title-only).

**Cards, listed days and Diehl (same day).** A job's place on a list page now comes from its own
card: the largest element around its link that holds no other job's link (a table row, a list
item, a box), without its title, resolved to a town and country where it names one ("Galway,
Ireland"; umantis writes "Überlingen am Bodensee (DE)"). Before, the text after a link could run
into the next job's company and town. A day the card states after a label ("Online seit:
25.11.2026", "Veröffentlicht am", "Posted on") dates a job whose page gives none. Added: **Diehl**
(umantis, `career.diehl.com/Jobs/All`, ten jobs a page, the next page named in
`data-pagination-next-href`; robots.txt answers 403, so no rules; its job pages lead to its career
site's job board, so its jobs come title-only with the list's place and day; Diehl's legal notice
has no clause on automated reading). A live read over 30 days with an electronics engineer's words
found three development-engineer jobs among its newest hundred, one in power electronics
(Markdorf).

### Rheinmetall's job sitemap, and sitemaps in many languages — 2026-11-25

**Access.** Rheinmetall publishes its jobs on its own site (`www.rheinmetall.com/{language}/job/
{title}/{number}`, run by HR4you behind the scenes). Its robots.txt names its sitemap
(`sitemap.site_1.xml`, 4.9 MB) and allows the German and English job pages while closing the other
eleven languages. The sitemap lists 1,423 jobs (25 November), each in 13 languages, every entry with
its last change; each job page carries JobPosting data with the full ad, the posting day and its
places (as lists: `"addressLocality": ["Unterlüß", "Kiel"]`, `"addressCountry": ["Germany"]`, now
read as two towns in Germany). Its legal notice (Impressum) has no clause on automated reading, it
publishes no terms of use for the public site, and no legal action by Rheinmetall against readers of
job lists or aggregators was found (web search, 25 November). Read as a job sitemap: one request for
the sitemap per search, pages only as below, at Jobcu's polite pace with its own name.

**Changes to the sitemap reader.** (a) A job listed under several languages (`/de/job/x/1`,
`/en/job/x/1`...) is one job: Jobcu keeps the page in the searched countries' ad language, else
English, so a German search opens Rheinmetall's German page once instead of every copy. (b) A page
robots.txt closes is neither opened nor counted among the 60 pages a search may open. (c) Titles the
search words miss: address words matched 2 of about 73 electronics jobs changed in one week
("Entwicklungsingenieur Elektrotechnik", "Elektrischer Entwickler", "Systemingenieur
Missionselektronik" spell none of an electronics engineer's search words). Now, as on SuccessFactors
([2026-11-21](#successfactors-titles-the-search-words-miss--2026-11-21)), the whole list is
remembered at each reading (`listmemory`, language-free addresses), and a job new on it since the
last reading goes to the title check with the title its address spells, dated to its first sight;
its page is opened only if the check keeps it. A list's first reading dates nothing. Checked live on
a copy of the data: the second reading of Rheinmetall's sitemap with 40 jobs new since the first
passed those 40 titles on with 2 requests (robots.txt and the sitemap). (d) A directory check of a
sitemap or an Avature list sees only some jobs (the newest 20 pages; a list's first page), so it no
longer records their towns: twenty pages named 6 of Rheinmetall's German towns, and recorded towns
make a search around a city skip an employer whose known towns are all far away. The directory's
sitemap and Avature entries (BAE Systems, Arm, Redline Group, Siemens and others) lost such towns.

### Gradcracker — 2026-11-25

Gradcracker (gradcracker.com) is the UK's main board for engineering and technology graduate jobs,
placements and apprenticeships (BAE Systems, Rolls-Royce, Cambridge Consultants, Network Rail,
CERN and hundreds of smaller engineering employers). Read with Jobcu's own client: robots.txt allows
everything but the keyword search, outgoing links, downloads and campaigns; the sitemap names each
list (`/search/{discipline}/{area}-graduate-jobs`, also per town and "rest of the world"); a list
page shows 80 jobs as cards (`<article data-search-result="{number}">`: title, job page, employer,
place, salary, deadline, start), `?page=2` and on (the electronic and electrical graduate list had
7 pages, about 1 MB each; all disciplines' graduate list 19). A job's page has the full ad
(`div.body-content`) and the same facts; neither gives a posting date or standard job data.

Terms: its legal page says "you're not allowed to download, distribute or scrape any part of this
website, but we do allow you to make copies for reading or browsing and you may also make permanent
copies for your personal use". No legal action or threat by Gradcracker against anyone reading its
pages was found (web search, 2026-11-25). Under the owner's rule (terms alone don't rule a source
out; lawsuits and lasting bans do) it is read only for a person who switches it on in Settings,
accepting that for their own job search, like the Bundesagentur, Avature, SmartRecruiters and Phenom.

How it is read: only the graduate lists of the areas whose names share a field word with the
person's English search words ("Power Electronics Engineer" → electronic-electrical; "Hardware
Design Engineer" → hardware; a nurse's or chef's words name none, so nothing is read), at most four
lists, each whole, at the polite pace; never the board. The lists give no dates, so each reading is
remembered (`listmemory`): a job new on a list since a reading at most 36 hours before counts as
posted that day, and only such jobs are passed on, so "Posted within" stays exact (a list's first
reading passes none). A job's page is opened only for a job still in the running. A UK list's job is
in the UK unless its place names another country (a CERN post in Geneva, Irish jobs of Tetra Tech).


### JSearch assessment — 2026-10-18

**Decision, updated after the owner's implementation request:** add JSearch as an optional
extra source through its direct Free API. It stays off until explicitly enabled and does not
replace existing feeds. The earlier assessment-only status is superseded by the implementation
below; its coverage, rights and metering qualifications still apply. No live vacancy/API test,
owner-data review, account change or purchase was made. Useful unique coverage and net cost
remain unmeasured.

#### Contract and evidence quality

OpenWeb Ninja's [product page](https://www.openwebninja.com/api/jsearch) describes a commercial
API over Google for Jobs results. This is a third-party service, not Google's own public job
search API or proof of separate direct partnerships with every named board. Its breadth is
a vendor claim. The [current OpenAPI](https://openwebninja.s3.us-east-1.amazonaws.com/portal/openapi/jsearch.yaml)
and [maintainer reference](https://github.com/OpenWeb-Ninja/openwebninja-skills/blob/main/openwebninja/apis/jsearch/README.md)
were read directly, rather than relying on cached search snippets or tutorial examples.

| Area | Current contract | Implication for Jobcu |
|---|---|---|
| Search | `/search-v2`, `data.jobs[]`, continuation in `data.cursor`; up to 10 jobs per page, 1–20 pages per call | Retain cursors and count page credits, not just HTTP requests. Search ranking is not exhaustive coverage. |
| Details | `/job-details` accepts up to 20 comma-separated IDs; each ID consumes a request credit | Batching reduces round trips, not credit use. Recover only additional evidence actually needed. |
| Descriptions | `job_description` is described as full text but is nullable | Potentially better than a snippet. A field name alone cannot establish complete employer requirements. |
| Links | Main apply URL, direct-link flags and alternative publisher apply options | Prefer a matching permitted employer/ATS vacancy when supplied; do not promise every link reaches an employer or remains live. |
| Locations | Nullable city, country and coordinates | A coordinate can describe a town rather than the actual workplace. Preserve provenance and ambiguity; it cannot establish commuting time. |
| Enrichment | Detail fields describe AI-extracted sponsorship, experience and skills | These are derived claims, not quoted requirements or independent scoring truth. Unknown sponsorship stays unknown. |

The downloaded schema contains `/search-v2`, details and two salary endpoints; `/search` is
absent. Older marketplace overview text and cached references still describe `/search`, and
an older cached reference mentions a deep-pagination multiplier not present in the current
contract. Integrations must use the current cursor contract and reconcile actual metering.
The schema mentions `enrich=true` in response-field descriptions without declaring that query
parameter or its fee. Do not enable it or assume the public sample's enriched fields are
ordinary guaranteed output. Marketing mentions expiration data, but the current schema does
not declare an expiration field. Neither discrepancy proves actual runtime behavior.

For reproducibility, the public schema retrieved on this date had SHA-256
`9f9ef1eec6cd97873211941c35b49c51b6ce8390fae803f2c2186b1127b7d03c`.
No provider example ad or third-party document text is copied into Jobcu's fixtures.

#### Countries, freshness and the existing pipeline

Google's [JobPosting guidance](https://developers.google.com/search/docs/appearance/structured-data/job-posting#region-availability)
lists Germany, UK, Switzerland, Netherlands, Belgium and Italy; Ireland is absent. That does
not prove JSearch returns no Irish jobs. It leaves Irish contribution and support across all
30 Jobcu countries unestablished. Google also documents expired results and incorrect
locations despite its publication rules. Search-index presence cannot prove vacancy validity.

The API accepts country/language inputs and relative date filters (`today`, `3days`, `week`,
`month`), without a documented exact rolling 24-hour parameter. Its timestamps are nullable;
ISO formatting alone cannot prove time precision or the employer's original publication date.
**Inference:** compare a conservative wider discovery window with Jobcu's exact saved window,
historical identity and permitted original dates. Do not widen the user's accepted age or
translate a refreshed board/index date into a new vacancy. Test boundary behavior first.

**Boundary check — 2026-10-24.** `3days` is looser than its name: two live queries returned
ads stamped 40-88 hours old and, for one German query, 160 and 184 hours old, all at day
precision. A 72-hour search that asked for `week` kept only 47 of 109 results; 62 were older
than its window. Searches up to 72 hours therefore ask for `3days` and 168-hour searches for
`week`: the tightest filter that covers the window, so no fresh ad is lost and more of each
paid page is usable.

**Lag check — 2026-10-29.** Two 24-hour searches counted no JSearch ad for 10 credits; in the
second, all 23 ads returned were dated before the window. A direct check of "Hardwareentwickler in Germany"
returned nothing for `today` and ten ads dated 68-92 hours earlier for `3days`. Jobcu had shown
three of them in earlier searches (one 15 days before its JSearch date: the date is the
index's, not the vacancy's); seven were jobs Jobcu had never shown. So JSearch lists ads about
two to three days late. From 2026-10-29 its ads counted up to 72 hours before the window when
Jobcu had never shown the job; from 2026-11-04 "Posted within" is strict again at the person's
request (those late ads were 55 of a 24-hour search's 186 cards). JSearch still asks
`date_lag_hours` (72) further back, so an older copy marks a repost, and the ads it indexes
within the window still count (8 good matches only it found in that search).

**Short texts — 2026-11-24.** JSearch passes on what each job site gives. In one search's results
34 of 705 texts were under 700 characters yet counted as whole ads: jobleads.com's summaries
(median 475 characters), and learn4good and Jooble texts cut mid-word at 250-400, while whole ads
ran 2,000-4,000. Twelve scored jobs (five at 70 or more) had only such a text, so the scorer took
missing requirements as absent. A text under 700 characters now counts as part of the ad. Its paid
details repeat a short text word for word, so they are bought only for a text cut with an ellipsis,
or for a missing date or place.

JSearch does not provide the evidence needed to decide population shares, city-election
comparisons, sampled journeys or personal fit. Its radius filter is not a travel-time filter.
More structured full text could reduce some online-ad research, but additional unique jobs
can also add downstream work. A net saving requires measured total AI/source/Maps usage on
equal coverage and quality. It is not established by API prices or a short response time.

The integration is one isolated `JobSource`, using the existing local
key store, request accounting, Stop handling, deduplication and freshness/location gates.
There is no need to install the vendor's agent skill/MCP server or change the chosen AI.
Use vacancy/requisition identity across providers; a JSearch ID alone does not deduplicate
Adzuna, a recruiter and the employer. Retain current employer feeds for originals and backup.
Never pay to score a job whose location gate is still unresolved or fails.

#### Price and spending controls

The [direct price list](https://www.openwebninja.com/api/jsearch) currently advertises:

| Direct plan | USD price | Included allowance | Extra usage |
|---|---:|---:|---:|
| Free | $0/month | 200 credits/month | Hard limit |
| Pay as you go | $0.005 per unit | No monthly fee | Usage billed |
| Pro | $25/month | 10,000 credits/month | $0.003 per extra |

The [marketplace pricing page](https://rapidapi.com/letscrape-6bRBa3qguO5/api/jsearch/pricing)
likewise lists 200 free units and Pro at $25 for 10,000. It additionally displays a bandwidth
platform fee: 10,240 MB/month included, then
$0.001/MB. The direct provider advertises no credit card for its free tier and no RapidAPI
transfer limit. Marketplace onboarding rules differ; do not assume a generic platform FAQ
overrides this API's actual plan/checkout. No checkout was inspected or accepted.

For ordinary requests, budget search pages plus requested detail IDs, with separate allowances
for any other opted-in endpoints and attempted retries. Reserve the maximum requested pages
before dispatch; release only reconciled unused capacity. Do not assume an empty response,
error, timeout or same-query retry is free. The current published error-charging treatment is
not sufficiently explicit to make that claim. Paid overages are not a spending ceiling.

Measured 2026-10-30 to 11-07 (~470 paid requests): replies usually come in about 2 s, but 9
requests stalled past the 30-second timeout every site gets (3 in one search), and an
interrupted request is never sent again, so its jobs were lost. JSearch now waits up to 120 s
for a reply and logs replies slower than 20 s, which gives the slow ones a measured time.

#### Rights and privacy

The provider's current [terms](https://www.openwebninja.com/terms), sections 2, 3 and 8, expressly
allow official API integration and use of API output in applications, including commercial
products. They limit that grant to the provider's own rights and leave original-source terms,
third-party rights and lawful storage/reuse with the customer. They exclude a competing
standalone data/API resale product. This is permission to use their API under its plan, not
blanket proof that every upstream board's full text can be stored and forwarded for matching.
Clarify the intended local history, display, AI processing and provenance before activation;
do not use an intermediary to bypass a held host or infer a board partnership from its logo.
No support message was sent and no legal agreement accepted during this research.

The [privacy policy](https://www.openwebninja.com/privacy) describes US hosting and one-year API
request-log/IP retention. The adapter sends only generated role/skill terms and search country;
it has no reason to upload a CV, cover letter or private preference narrative. Jobcu remains
local, but enabling it adds another external recipient for those search terms. The policy does
not establish that query bodies are never retained. Provider log retention is not a licence
for Jobcu to keep third-party ad text indefinitely.

#### Implemented controls

`sources/jsearch.py` uses direct `x-api-key` authentication and `/search-v2` cursor pages.
Saving a key does not enable collection, including when upgrading an existing installation.
Before vacancies, `/usage?api_id=jsearch` must report an active direct Free plan and a complete,
current request allowance no greater than 200. Paid, unknown and incomplete accounts stop this
source. Calendar-month reservations are atomic and capped at 200, including account checks;
provider-period remaining quota can further reduce the allowance. The provider's advertised
Free hard limit is also required: local accounting alone cannot cap other clients' usage.

Each search receives an adaptive share, at most 40 credits including account checks and full-ad
details. Countries and native/English queries take turns; cursor pages follow initial queries,
with at most three pages per query. Two units are kept for selective missing full ads when the
allowance permits. Small allowances rotate the starting country. Exhaustion is reported as
partial coverage, while other feeds continue. One page or one detail ID is requested per call;
reserved attempts are never assumed free or refunded after errors. Automatic HTTP and transport
retries are disabled for this adapter, and credentials never follow redirects. No enrichment,
salary-estimate, marketplace, storefront or wallet route is used.

Supplied descriptions and application alternatives enter existing reuse, deduplication and
admission checks. Earlier dates and complete text survive weaker detail replies. Missing dates
stay unknown, midnight dates are day precision, and a wider source date filter does not widen
the user's accepted age. Lookup country is stored separately from workplace evidence. Source
coordinates are not promoted to an address; derived sponsorship/skill fields are not requirements.
Employer links require both the supplied direct flag and a matching employer/known ATS host;
original board routes remain available. A search makes no request to those destinations merely
to resolve a redirect; a person's click reads the one page they asked for (see ENGINEERING.md). Fictional tests cover hardware, nursing and teaching, failures and ceilings.

### Bundesagentur access hold — 2026-10-17

The current [portal terms](https://www.arbeitsagentur.de/nutzungsbedingungen), section 2a(3),
prohibit robots/webspiders and automated data collection contrary to the intended interface use.
This supersedes the earlier assumption that the public website endpoint was sufficient
permission. Pause automated search/details and deny these destinations in the HTTP client,
including redirects, until an explicitly permitted interface or permission is established.
Keep the historical parser, source identifiers, saved ads and manual links; no login, alternate
host or blocked-page workaround is authorized. Other permitted sources continue independently.
The hold has a coverage cost; no complete replacement is claimed.

A portal copy's first-publication date is not proof of an employer vacancy's original date.
Identity, earlier matching copies and permitted original posting/closing metadata are still
needed to distinguish a fresh opening from a refreshed advertisement.

These are retained decisions from dated checks; no new access was tested during this cleanup.

### FreeHire — 2026-11-02

[FreeHire](https://freehire.me) is an open-source catalogue of job ads that it reads from
employers' career systems (about 220 systems such as Workday, SuccessFactors, Softgarden,
SmartRecruiters, JOIN, Personio, rexx and coveto) and from about 130 boards, with duplicates
merged. On 2026-11-02 its facets counted 229,817 open ads in Germany, 124,731 in the UK and
11,262 in Ireland. Its [API](https://freehire.me/docs/api) needs no key:
`/api/v1/agent/jobs/search` returns each hit's full text, `/api/v1/jobs/facets` the live counts.

- **Permission.** Its [terms](https://freehire.me/terms) (updated 2026-10-28) forbid scraping
  beyond the documented API and say that without a plan the API "is for personal and
  non-commercial use — your own job search, research, or a tool you run for yourself", which
  is how each person runs Jobcu. Showing its ads in a service for others needs a plan. Its
  robots.txt allows `/api/` for every robot and asks robots to use the API instead of the
  pages. The ads still belong to the employers.
- **Limits.** 120 requests a minute (its `X-RateLimit-*` headers); Jobcu pauses 0.6 s between
  requests and asks at most 80 times a search (one search on the day: 8 requests, 4 s).
- **Dates.** `posted_at` is the date the ad's own source states, which some boards restate;
  `created_at` is FreeHire's first sight. Jobcu dates a job by the earlier of the two and leaves
  out an ad FreeHire flags as `fake_freshness`. It asks with `open_within_days` (first sight),
  the window plus a 48-hour lag: of 81 recent ads, half were listed within 7.5 hours of their
  date and the latest after 42. An ad dated before the window doesn't count; it only marks a
  repost.
- **Copies.** Ads from boards (Adzuna, Reed, EURES, XING and others) carry the board's link and
  can hold only the start of the ad (Adzuna's 500 characters). Only ads from the sources the
  facets list under `source_type=ats|company` count as complete ads on the employer's own page.
  Some of those systems Jobcu doesn't read itself (SmartRecruiters' interface admits only
  LinkedIn's crawler; its career pages are read for those who switch them on, below): Jobcu reads
  FreeHire's copy, and a click on such a link opens it as it is.
- **EURES titles.** German EURES copies are the Bundesagentur's vacancies with the agency's
  occupation added in brackets ("Senior Engineer (m/w/d) (Hardwareentwickler/in)": all 100 of a
  day's sample). Jobcu removes that bracket, so the copy matches the agency's own ad.
- **Word search in the ad text (2026-11-03).** A field word can miss an ad that says it only far
  into its text: Nexperia's "Automotive Application Engineer" (6,800 characters) was found by
  "power semiconductor", which its first paragraph names, but not by "power electronics", which
  first appears after 3,100 characters. Jobcu therefore also asks for the components and
  technologies a field works with (ads name them early) and reads key employers' career sites
  itself.
- **Coverage measured.** With a hardware engineering search's 25 titles (title only), FreeHire
  had 34 ads first known in the two days Jobcu had searched (29-31 October; the earlier of
  posted and first seen). Jobcu had collected 12 of them; 22 had reached it through no source,
  7 of those relevant: from Lenze's rexx, SMA's SuccessFactors, veralto's Workday, Agile
  Robots' Greenhouse, Infineon's Eightfold and a recruiter's Loxo system, and one Adzuna copy.

### Source checks — 2026-10-30

- **EURES** has a public search interface (`POST
  https://europa.eu/eures/api/jv-searchengine/public/jv-search/search`, the portal's own; JSON
  body with keywords, `publicationPeriod` such as `LAST_DAY`, `locationCodes` such as `de`). It
  returns full descriptions, first-publication time, employer, NUTS regions and contract codes.
  The [legal notice](https://eures.europa.eu/legal-notice_en) authorises re-use with the
  European Labour Authority credited and says nothing against automated access; robots.txt
  does not exclude the search, and europa.eu asks for `Crawl-delay: 10`. For Germany it carries
  the Bundesagentur's vacancies (same titles and wording); for Ireland it held 5 jobs of the
  last day, all German-posted. A candidate for the other EU countries' public employment
  services and for people who keep the Bundesagentur off; not built yet.
- **JobsIreland.ie** answered 403 to every address (robots.txt included) from the owner's
  connection, to an ordinary browser there and to an outside fetcher, from 2026-10-29 evening.
  Jobcu sends it 1-4 requests a day, so this is the site's refusal, now reported as one.
- **SmartRecruiters** (Bosch, ETAS, Delta Electronics): `api.smartrecruiters.com/robots.txt`
  allows only LinkedInBot, so its interface is never used. Since 2026-11-24 the companies' public
  career pages are read for those who switch them on
  ([record](#smartrecruiters-career-pages--2026-11-24)).

### Bundesagentur opt-in — 2026-10-30

The owner asked the agency for permission on 2026-10-25. On 2026-10-29 its technical support
replied only that the owner should call their local Agentur für Arbeit; it neither gave nor
refused permission. The terms (Stand 08.07.2026, section 2a(3)) still say robots, web spiders
and using existing interfaces contrary to the agency's intended purpose are not allowed. The
owner decided to read it again for their own job search and accepts that. The source is
therefore an opt-in like JSearch: off for everyone until switched on in Settings, which shows
the terms note; only then does the HTTP client let requests reach arbeitsagentur.de hosts
(`sources.accepted_terms`, `http.terms_denial`). Nothing works around a block, the agency's
own public client ID is used as before, and requests keep their pause (0.7 s) and per-search
ceiling. Evidence for the decision: searches 1-5 (before the hold) had 11-47 German cards
each from it, almost all found by no other source; on 2026-10-29 one query found six
hardware-developer ads of the last day, five of which Jobcu had not found elsewhere.

- Held boards: StepStone, Totaljobs, IrishJobs and Jobs.ie
  lack established permission for direct automated collection. Do not infer permission from robots alone.
  Rechecked 2026-11-26 under the rule that only a real legal or lasting-ban risk rules a source
  out: StepStone obtained a court injunction in Germany against a competing job portal, OFiR,
  for linking to its job ads (one of the first cases under the EU database rules,
  [report](https://itworldcanada.com/?p=29449)). A board that has gone to court against an
  aggregator stays unread, and so do the group's other boards.
- Unused sources: EURES (see the 2026-10-30 check below); publicjobs.ie, UK Civil Service Jobs
  and DWP Find a Job blocked automated access.
- LinkedIn/StepStone: no established direct
  vacancy-reading API for Jobcu. AI-found links need permitted original evidence and date checks.
- Employer restrictions also apply; see the [additional access boundaries](#additional-access-boundaries).
- Country candidates are research leads, not adapters.
  The later 2026-10-06 update takes precedence:
  Engineers Ireland is a manual benchmark candidate pending collection checks; VDAB requires a
  partnership; Job-Room's employer-management API is not a public vacancy-search feed.

### Avature: Siemens and Siemens Energy — 2026-11-24

**Access.** `jobs.siemens.com` (= `siemens.avature.net`) and `jobs.siemens-energy.com` run Avature.
Their robots.txt allows the job portals (`/*/externaljobs`, `/*/jobs`; only addresses with `qtvc=`
are closed); their sitemaps list the sites' own pages, not jobs; the RSS feed (`.../SearchJobs/feed/`)
follows a country filter but lists only the 20 oldest jobs and ignores sorting and paging, so it is
not used. Lists are ordinary pages: Siemens shows six jobs a page whatever is asked and pages with
`folderOffset`, Siemens Energy twenty with `jobOffset`; the reader follows each page's own next-page
link. A Siemens list is filtered by a country option (`?42386[]=812132` for Germany; the option
numbers of all 30 supported countries were read from the site's own option search, 24 November),
Siemens Energy has a page per country (`SearchJobsGermany`, `SearchJobsUK`, ...). Read with Jobcu's
own client on 24 November: Siemens 381 jobs in Germany, 155 in the UK, 15 in Ireland; Siemens Energy
271 in Germany, 137 in the UK. A job "in multiple locations" is on every country's list (Iceland's had
four, in Brazil and Japan): its country comes from its page. Job pages: Siemens' carry Avature's
label and value fields ("Posted since 23-Nov-2026", "Location(s)", job type, work mode) and the ad in
an unlabelled field, no JobPosting data; Siemens Energy's carry JobPosting data with only the title
and posting day, and the place at the top of the ad. A live read through the reader with
electronics search words (Germany, 7 days): 95 requests in about 4 minutes, 30 matching jobs read,
7 fresh, among them two "Siemens Graduate Program" jobs and a junior electrical engineer's in Erlangen;
Siemens Energy 45 requests, a UK "Graduate Electrical Engineer" among them.

**Terms and risk (owner rule of 24 November: only a real risk of being sued or of a lasting ban rules
a source out).** [Siemens' terms of use](https://www.siemens.com/global/en/general/terms-of-use.html)
forbid users to "engage in text or data mining", including "any automated scraping, reproduction, or
extraction of content" from its digital services. [Siemens Energy's terms of use](https://www.siemens-energy.com/global/en/home/general/terms-of-use.html)
have no clause about automated reading. No lawsuit or legal threat by either company against readers
of job lists or job aggregators was found (web searches, 24 November). What Jobcu reads per search:
the searched countries' lists (about 90 pages for Germany, the UK and Ireland at Siemens), at most
30 job pages a list of titles matching the person's search words (a page read once is remembered),
at one request a second or slower, with Jobcu's own name, robots.txt respected and reading stopped at
the first refusal; no account, no check passed. So the source is off by default and read only for a
person who switches "Company career sites (Avature)" on in Settings, accepting Siemens' terms for
their own job search (`sources.TERMS_NOTES`), like the Bundesagentur; Siemens Energy is read under the
same switch.

### SmartRecruiters career pages — 2026-11-24

**Access.** `api.smartrecruiters.com/robots.txt` admits only LinkedInBot, so SmartRecruiters' posting
interface is never used. A company's public career page, `careers.smartrecruiters.com/{Company}`, has
no robots rules of its own (its robots.txt address leads to the job search's home page) and nor do
the job pages on `jobs.smartrecruiters.com` (404). The career page lists every open job grouped by
place, the groups in alphabetical order, the first page of groups in the page and the others at
`/{Company}/api/groups?page=N` (`data-groups-pages`: Continental 34, AECOM 77). The lists give no
dates; each job page carries the standard job data as page markup (schema.org JobPosting: exact
posting time, town and country, employment type, full ad), which the SuccessFactors markup reader
reads as it is. A job listed in several places has its main one on its page, which is kept only in
the country it was listed for; Continental puts a street in the town field, so the list's town is kept
when the page's isn't a known town. Bosch's page (`BoschGroup`) leads to jobs.bosch.com, whose
robots.txt closes `/en/` to robots other than a few named ones: the reader asks for the career page
without following redirects, so Bosch isn't read there. Read once each with
`tools/check_employers.py`: Continental (103 jobs in Germany), Aumovio (49 in Germany), Renesas
Electronics (40 Germany, 28 UK), ALTEN (112 Germany, 89 UK), Ramboll (115 Germany, 55 UK, 15
Ireland), AECOM (287 UK, 19 Ireland, 37 Germany), Wabtec (34 Germany, 27 UK), Assystem (123 UK),
Brainlab (14 Germany), XP Power (11 Germany), Averna (5 UK, 3 Ireland), Segula Technologies (France).
A live read with electronics search words: Renesas gave a "Graduate Digital Design Engineer" in
Edinburgh posted the day before and a junior technical sales engineer's job in Munich.

**Terms and risk.** SmartRecruiters' [terms for job seekers](https://www.smartrecruiters.com/legal/terms-of-use/)
forbid to "use automatic means to access content or data from other users" (among the rules for its
candidate portal and services). No lawsuit or legal threat by SmartRecruiters against readers of job
pages or job aggregators was found (web searches, 24 November); tools that read its public job pages
are openly offered. What Jobcu reads per search: the lists of the directory's SmartRecruiters
companies that hire in the searched countries (a few hundred pages at most, one a second, Jobcu's
own name) and at most 30 job pages a company of titles matching the person's search words, each
remembered once read; robots.txt respected, reading stopped at the first refusal. Because of that
clause the source is off by default and read only for a person who switches "Company career sites
(SmartRecruiters)" on in Settings, accepting the terms for their own job search
(`sources.TERMS_NOTES`).

**Found by themselves (2026-11-25).** SmartRecruiters' addresses (`jobs.` and
`careers.smartrecruiters.com/{Company}`) are recognised in job sites' links and in the careers pages
the person's AI names, like Workday's: for a person who accepted SmartRecruiters' terms, such a
company's list is checked once and read from the next search on (`employers.learn`,
`employers.find`); for anyone else it isn't read at all, not even to check it, and the AI's
look-up names the employer under "SmartRecruiters" among the systems they don't use. Before, every
reader with such terms was left out of learning even when accepted, and SmartRecruiters' addresses
counted as a system Jobcu doesn't read.

### Phenom career sites — 2026-11-24

**Access.** A Phenom career site's search page asks the site's own interface,
`POST https://{host}/widgets` with `{"ddoKey": "refineSearch", "selected_fields": {"country":
[...]}, "from": 0, "size": 50, ...}` (the section's `lang`, e.g. `en_global`, and region), which
answers with the chosen countries' jobs (title, places, posting day, number) and each country's
job count. Their robots.txt closes only `*/px-widgets`, the apply pages, chat and tracking; job
pages (`/{region}/{language}/job/{number}`) carry JobPosting data with the full ad. Address
parameters (`?country=`) and the sort order are ignored by the search page itself, so the
interface is used, read whole for each searched country (it gives each job's day, so nothing is
opened until a job is still in the running). Counts on 24 November: ABB 129 jobs in Germany, 39
UK, 6 Ireland (7 requests for all three lists in a live read, 57 posted within the week); Siemens
Healthineers 107 Germany, 46 UK, 13 Ireland; Thermo Fisher 104, 176, 40; Danaher 53, 93, 10; RTX
28, 139, 3; GE Aerospace 6 Germany, 25 UK; Exyte 228 Germany, 19 Ireland, 13 UK. A job in several
places is on each of their countries' lists, with all its places. RTX, Danaher, Thermo Fisher and
GE Aerospace are also read on Workday, whose ads are behind the check; the duplicate rules join
the two copies. FERCHAU's Phenom site uses another address form and isn't read yet.

**Terms and risk.** [ABB's terms of use](https://www.abb.com/global/en/company/provider-information)
require ABB's prior written permission to scrape its sites (another version limits automated access
to what a person could request). ABB's Workday list asks robots not to read it, which is respected;
its Phenom site allows the job lists and pages. No lawsuit or legal threat by ABB or by Phenom against
readers of job lists was found (web searches, 24 November). What Jobcu reads per search: one count
request and one to four list requests per searched country and employer, and job pages only for jobs
still in the running, one request a second, with Jobcu's own name, robots.txt respected. So the
source is off by default and read only for a person who switches "Company career sites (Phenom)" on
in Settings, accepting those terms for their own job search (`sources.TERMS_NOTES`).

### Jibe career sites and Arm's own site — 2026-11-24

Schneider Electric (`careers.se.com`) and AMD (`careers.amd.com`) put a Jibe career site in front of
iCIMS, whose hosts' robots.txt closes everything (`careers-se.icims.com`, `careers-amd.icims.com`,
also Arm's `experienced-arm.icims.com`); TT Electronics' iCIMS host allows its job pages, but they
carry no job data (the ad sits in a frame). The Jibe sites' robots.txt closes nothing, their
sitemaps list `/jobs/{number}?lang=en-us` without titles or dates, and the site's own search,
`GET /api/jobs?country=Germany&page=1&limit=100&sortBy=posted_date&descending=true`, answers newest
first with each job's title, places, posting day (Schneider "November 23, 2026", AMD an ISO time),
employment type and the full ad (description, responsibilities, qualifications), and the number of
matching jobs. Schneider had 100 jobs in Germany, 67 in the UK and 16 in Ireland; AMD 6, 21 and 17.
A live read of Schneider's three lists took 4 requests (13 jobs posted within the week). Neither
site's terms has a clause about automated reading (Schneider's terms of use; AMD's allow personal,
informational use), and no legal action against readers of job lists was found, so the source runs
by default. Arm's own site (`careers.arm.com`, Radancy) lists its jobs in a sitemap with dates whose
addresses name town and title, and its pages carry JobPosting data: it is read as a job sitemap.
So is BAE Systems' UK job search (`jobsearch.baesystems.com`, run with its recruitment partner; the
applications go to an Avature site): robots.txt allows everything, its `jobs-sitemap.xml` lists 441
dated job addresses with their titles, and each page carries JobPosting data with the town, country
and full ad ("Graduate Electrical Engineer", Cowes). No terms page could be read (BAE's main site
refuses Jobcu, the job site has none) and no legal action against job readers was found.

### Broad boards and web discovery — 2026-10-10

**Rechecked:** [LinkedIn's agreement](https://www.linkedin.com/legal/user-agreement) restricts
scraping/copying and unauthorized automation. [Indeed's terms](https://www.indeed.com/legal)
require written permission for automated access, with a conditional robots.txt exception;
its [Job Sync API terms](https://docs.indeed.com/legal-terms/job-sync) concern partner integrations,
not a general personal-app search entitlement. Neither establishes Jobcu collection permission.

StepStone's [current applicant-terms portal](https://www.stepstone.de/e-recruiting/rechtliches/nutzungsbedingungen-bewerber/)
embeds its terms, and the [official integration catalogue](https://api.stepstone.com/)
documents job feeds, applications and recruitment integrations. No permitted personal-app
vacancy-reading route was established. This preserves the held decision; it does not claim
that no StepStone API exists. Permission/partner scope remains the dependency for direct reading.

[Google Custom Search JSON API](https://developers.google.com/custom-search/v1/overview) is
closed to new customers; existing customers must transition by 2027-01-01. It is not a new
self-service discovery route for Jobcu. [Gemini Search grounding](https://ai.google.dev/gemini-api/docs/google-search/)
already supports cited research. Adding discovery still needs reliable exact vacancy URLs,
permitted originals and original dates; search snippets do not establish freshness or recall.
No search-engine scraping, board adapter, partner account or vacancy traffic was introduced.

### Employer feeds and remote candidates — 2026-10-10

**Primary checks:** [Greenhouse's Job Board API](https://developers.greenhouse.io/job-board.html)
documents public unauthenticated GETs and optional full content; this differs from its private
recruiting-management APIs. [Lever's own posting documentation](https://github.com/lever/postings-api)
describes published employer listings. [Personio's recruiting overview](https://support.personio.de/hc/en-us/articles/360000314338-Overview-of-the-Personio-Recruiting-API)
distinguishes its employer XML feed from account integrations. These existing methods depend
on discovering actual employers, permitted hosts and original evidence; an endpoint catalogue
or directory size does not establish unique fresh relevant coverage.

[Jobicy's API/RSS documentation](https://jobicy.com/jobs-rss-feed), updated 2026-10-01,
explicitly permits ordinary apps and AI integrations with attribution and canonical Jobicy URLs.
The public paginated feed covers seven days with a three-hour publication delay; direct ATS
links require separate paid access. RSS polling must not exceed hourly. Candidate for remote
work, pending robots/terms checks at implementation and comparison of country eligibility,
original dates/descriptions and unique contribution. No paid feed, adapter or vacancy call here.

[Remotive's original API terms](https://github.com/remotive-com/remote-jobs-api) require attribution
and links, and delay public jobs by 24 hours. **Inference:** weak as the primary route for a
daily 24-hour fresh-job search; possible remote backup value is not disproved. Neither feed
establishes broad on-site hardware, nursing or teaching coverage. Broad-board restrictions
above remain: a reachable/internal endpoint is not app permission or a guarantee against bans.

### Ashby workplace fields — 2026-10-10

**Rechecked:** the [public posting contract](https://developers.ashbyhq.com/docs/public-job-posting-api)
documents primary `address.postalAddress`, direct secondary `address`, and their locality,
region and country fields. Missing upstream data remains missing; `publishedAt` is last
publication. [Customer terms](https://www.ashbyhq.com/resources/terms) govern contracted service
use, not a new blanket crawling licence. A metadata-only robots.txt request to api.ashbyhq.com
returned 401; this neither grants crawling permission nor changes the documented public API
contract. Blocked pages stay blocked.

The parser correction consumes fields in the existing documented list response, preserving
free text and legacy nested secondary addresses. No endpoint, employer directory, scope,
request budget, robots policy, page access or permission is expanded. It does not infer an
unknown town, employer head office or first posting date. Fictional evidence and limits:
[ENGINEERING](ENGINEERING.md#evidence-identity-and-scoring).

## Identity and freshness evidence

### Oracle title search for a job only job sites listed — 2026-11-21

Oracle's list finder takes a `keyword` (the career site's search box): one request, most
relevant first, from every country (`OracleSource.find_by_title`, at most 50 answers). Checked
once on one employer's public list. On a saved search's pool it joined one employer's posting
first posted a year before a job site listed it again. A list answer that names another country
is ruled out before any full ad is read.

### Workday title search for a job only job sites listed — 2026-11-21

Workday's list address takes a `searchText` (the search box on every Workday career site). For
a job still in the running that only job sites listed, of a directory employer on Workday,
Jobcu asks that employer's list once for the job's title and reads the full ads of at most the
three closest titles (`WorkdaySource.find_by_title`, `employerpostings.py`). Same address, robots
check, polite client and request budget as reading the list; no new endpoint or host. Checked on
a saved search's pool (free, Jobcu's own reader): 8 postings joined, all the right vacancy
(Leonardo's three graduate and academy jobs, first posted 25 August to 26 October and listed
again by a job site on 10 November; Vishay, Airbus, MBDA); ADI's and Microchip's servers were
behind the robots.txt challenge recorded the same day and weren't asked.
### Workday robots.txt behind a human check — 2026-11-21, revised 2026-11-24

Fetched with Jobcu's own identity: `robots.txt` on Workday's `wd1` and `wd5` servers (85 of the
directory's Workday companies, e.g. analogdevices.wd1, medtronic.wd1, microchiphr.wd5, gevernova.wd5)
answered 429 with Cloudflare's "Security Check" page (`cf-mitigated: challenge`); `wd3` servers
answered their usual file. On 24 November the check also covered the career pages and sitemaps and
the job-ad address (`GET /wday/cxs/.../job/...`), whether or not the request asked for JSON or was
spaced a minute apart, while the job list (`POST /wday/cxs/.../jobs`) answered as before (778 jobs at
Analog Devices); robots.txt itself answered normally on one later try.

The robots standard ([RFC 9309, 2.3.1.3](https://www.rfc-editor.org/rfc/rfc9309.html)) says a
robots.txt answered with a 4xx status is "unavailable" and a crawler "MAY access any resources";
[Google](https://developers.google.com/search/docs/crawling-indexing/robots/robots_txt) treats
4xx except 429 that way and a 429 like a server error, assuming no restrictions once it lasts with
no saved copy. From 2026-11-24 Jobcu follows the standard (the owner: Workday is essential in their
field): a 4xx robots.txt sets no rules, a 5xx or network failure allows nothing for that search, and
a check on robots.txt alone no longer counts as the server refusing Jobcu. Jobcu still never gets past
a check: an address that shows one is not read, and once a list or ad Jobcu needs shows one, that
server isn't asked again in the search. So the wd1/wd5 lists give each job's title, place, date and
the employer's link (which a person opens in a browser); their ads come from other sites' copies of the
same job where there are some, and a job known only by its title is scored as such ("the ad couldn't be
read"). In search 21 (72 hours) these servers gave 89 jobs of 33 employers, four of them at 60+
(Analog Devices 84, Medtronic 75, Littelfuse 71).

### Career sites learned from job links — 2026-11-25

Job sites' copies of a job often carry the employer's own link: JSearch's apply options, FreeHire's
original address, the Bundesagentur's link to the original ad, Reed's external link. In search 21's
saved pool (72 hours) 30 job-site copies linked a career system Jobcu reads (Oracle 10, Workday 10,
SuccessFactors 3, Softgarden 2, Personio 2, Ashby, Greenhouse, Teamtailor 1 each), on 13 sites the
directory and the found employers didn't read: among them Honeywell's newer Oracle host
(`icfcjb.fa.ocs.oraclecloud.com`, 21 jobs in the UK), Ralliant's (Tektronix) Oracle site, Oxford
Nanopore's, and Eykon's SuccessFactors site. Most of the directory's additions of 24 November came
from such links, found by hand.

Since this date a search does that itself (`employers.learn`): after collecting, it takes the career
sites the job sites' links name (`careerlinks.board_in_job_link`: an address on a system Jobcu
reads, or a SuccessFactors job page `/job/{Town}-{Title}-{postcode}/{number}/` on the employer's own
address), leaves out those Jobcu reads (another address of one list counts as that list: a Personio
company at `.de` or `.com`, another site name on an Oracle host) and checks the twelve most linked,
beside the later steps, with the system's own reader as the directory check does (its list read
once; robots.txt, polite pace and checks as always). Usable ones are kept in the person's data folder
and read from the next search on, like the employers the person's AI finds. A site is checked again
after a month, or after a week when it only refused or couldn't be reached. Only readers the person
uses and whose terms need no acceptance (not SmartRecruiters, Phenom or Avature) take part. No AI
call, no web search and no job link is visited: only the public job lists of the sites named.

### Workday's check follows what one address sends — 2026-11-25

With Jobcu's own identity, one request at a time: the lists and the ads of 11 wd1/wd5 employers
(Analog Devices, Microchip, NXP, Medtronic, KLA, Intel, NVIDIA, Aptiv, Moog, GE Vernova, Stryker)
answered normally, full ads included; robots.txt still answered with the check. About half an hour
later, after some 40 more Workday requests that included about ten to addresses that don't exist (a
wrong site name; Workday answers those with the same check page, not 404), every wd1 and wd5 list
answered this computer with the check, Analog Devices' and Microchip's included, for about 35 to 40
minutes (one request every three minutes: refused from about 08:50 to after 09:24 UTC+3, answered
again at 09:30), while wd3 lists answered.
So the check depends on what one address has sent, not on the list: a search reading about 90
wd1/wd5 companies, four at a time at each site's own pace, can meet it midway, and from then on each
further company only adds a refused request.

Since then Jobcu keeps the polite pace per Workday server (`wd1`, `wd5`, ...: one request a second
across all the companies on it, `http.server_of`) instead of per company, and a server that refuses
three companies in a row, with nothing answered in between, isn't asked again in that search
(`http.REFUSALS_IN_A_ROW`): the others are tried again in the next search. One company refusing alone
(a list whose address changed) doesn't stop the rest. The search's notes say how many companies asked
for a human check. The check itself is never passed.

### Workday ads read from the employer's own site — 2026-11-24

Some employers on wd1/wd5 publish every vacancy on their own career site too, under the vacancy
number their Workday list shows (the list's first `bulletFields` entry, e.g. `R5049393`, also at the
end of the Workday address, `..._R5049393-2`). GE Vernova's site (`careers.gevernova.com`, robots.txt
allows everything and names its sitemap) lists each in its job sitemap as
`/automation-engineer/job/R5049393`, and the page carries the standard job data (JobPosting: title,
full ad, exact posting time, place). Measured on the 80 newest jobs of each Workday list, by number:
GE Vernova 79 (all 64 of that day), Johnson & Johnson 61 (`careers.jnj.com`), Thermo Fisher 13 of 20
and Danaher 15 of 20 (Phenom sites, `/global/en/sitemap_index.xml`), RTX 14 (Phenom; its sitemap
lists part of the jobs); Abbott, GE Aerospace and Agilent 0, and Hitachi Energy's site uses its own
numbers (`JID3-...`), so none of them is used.

The directory names such a site's job sitemap for the Workday entry (`ads`). When Workday answers an
ad with its check, the reader reads that sitemap once per search, opens the page whose address names
the same number (the version without a language path first, at most two), and takes it only when its
JobPosting has a full ad and the job's title (`workday.SAME_TITLE`); otherwise the job stays as it
was. The page's place is kept (RTX's and Workday's are the same building code where both name one;
"4 Locations" on Workday becomes the four towns), and its date only when it is earlier than the list's
(a later one can be an update). Same robots check, polite client and request budget as the list; the
Workday check itself is never passed. A live read through the reader: GE Vernova 12 of 12 jobs, Thermo
Fisher, RTX and J&J 6 of 6 in Germany, Danaher 3 of 6 (the others aren't in its sitemap).

### Directory refresh and employers added — 2026-11-25

`tools/check_employers.py` read every directory employer's list once (all 177 Workday employers
answered at one request a second per Workday server). Three Greenhouse boards no longer exist
(HEADBORNE.AI, Parloa, TrueLayer) and left. A country or town an employer hired in before now stays
in its entry when its list has no job there on the day of the check: the snapshot of 3 October had
left, for example, Rolls-Royce's graduate site (which posted its UK Engineering and Technology
Graduate Programme on 5 October) out of UK searches, and this check would have removed Ireland from
ZF and Endress+Hauser for the same reason (186 entries kept a country that way). A list that
exists but has no job in the supported countries right now keeps its entry (Littelfuse's
university site).

Added after one read each: Workday: Signify (`lighting.wd3`, 11 jobs in Germany), Avnet (Avnet
Silica and EBV Elektronik, `avnet.wd1`, 73 in Germany and 11 in the UK, with an EMEA engineering
graduate programme), 3M (13 in Germany, 13 in the UK), ZEISS (`zeissgroup.wd3`, 433 in Germany, 26
in the UK), Freudenberg (209 in Germany, 20 in the UK, 15 in Ireland, e-Power Systems among them),
Rolls-Royce Power Systems' early-careers site (48 in Germany). SuccessFactors: Advanced Energy
(power conversion; Germany, the UK and Ireland), Bertrandt (on SAP's hosting,
`bertrandt.jobs.hr.cloud.sap`: a customer's career site there, not SAP's own website), Teradyne,
Skyworks, Lear, Celestica (25 in the UK, 14 in Ireland) and Seagate (its Derry~Londonderry jobs:
the address writes the town "DerryLondonderry", now read as Derry). Jibe: Keysight (Böblingen;
its `location` filter is a text search that matched 155 jobs for Germany, most of them in the US,
so Jibe lists are now asked by `country`, which gives the same lists on Schneider's and AMD's
sites). Eightfold: Northrop Grumman (`ngc.eightfold.ai`, 46 in the UK), Lam Research. Ashby:
Vertical Aerospace (11 in the UK). Oracle: Honeywell Aerospace (`icfcjb.fa.ocs.oraclecloud.com`, 21
in the UK; Honeywell's other host stays), Socomec, Garrett Motion. Phenom (read for those who accept
its terms): Leonardo UK (`careers.uk.leonardo.com/gb/en`, 374 jobs in the UK) and Arrow Electronics
(24 in Germany, 13 in the UK). Workable, added the same day: ZeroAvia (hydrogen-electric aircraft
propulsion in Kemble, power-electronics roles among them; 12 jobs in the UK).

Looked at and not read: FERCHAU's site (`touch.ferchau.com`) says in its robots.txt "Please do not
spider for jobs and projects from this website" and offers its jobs through an interface on request,
so it isn't read; its jobs come through the Bundesagentur. b-ite (Vincorion and other employers)
answers its job search only with each employer's own key from that employer's page, which Jobcu
doesn't reuse. Brunel's robots.txt closes its German pages to AI crawlers and every page to Jooble's
job robot; Orizon's closes its job pages; both reach Jobcu through the Bundesagentur. Arrow's and
nVent's Workday addresses answered with Workday's check (a wrong or closed address gets the same
page); Arrow is read on its Phenom site. Hensoldt's Workday site is an old one (its jobs are on its
SuccessFactors site, read since October). IAV runs SuccessFactors' older portal, which Jobcu doesn't
read; Qorvo's SuccessFactors site had 8 jobs, none in the supported countries.

### Employers added and moved — 2026-11-24

Read once each with `tools/check_employers.py`: Woodward (Workday wd5, 41 jobs in Germany),
BorgWarner (wd5, 13 in Germany), Evolito (wd3, 38 in the UK), Altera (wd1, 10 in the UK), Leidos (wd5,
47 in the UK, 10 in Germany), and the Eightfold sites of Micron (`careers.micron.com`, robots allows
`/careers`; its terms limit only the request rate) and HP (`apply.hp.com`, 24 jobs in Germany, 19 in
the UK). NXP moved to Workday's newer address without a server number (`nxp.myworkdayjobs.com`,
linked from nxp.com; 43 jobs in Germany, 12 in the UK); its old wd3 address answers 422 for every
request. Dell left Workday for Oracle Recruiting on its own address
(`enterpriseplatform.dell.com/CX_1001`, no robots.txt; 9 jobs each in Germany, the UK and Ireland).
The directory's "Emerson" Workday site is Emerson College's and is named so; Emerson's own jobs are on
Oracle (`hdjq.fa.us2.oraclecloud.com/CX_1`, linked from emerson.com; 36 jobs in Germany, 17 in the UK).
The directory check now keeps a town only when the town list knows it (Teveren, Molesworth and
Whiteley were villages or bases).

### Workday detail workplaces — 2026-10-23

A bounded check through the existing Workday reader's terms, robots and polite-request gates
confirmed `jobPostingInfo.location` and string-list `additionalLocations` alongside the full
ad. The reader now consumes these fields in the response it already requests, without another
endpoint, query, country or source allowance. Named locations remain source evidence; absent
or malformed fields retain known metadata. This is an existing-response parser correction,
not permission for new collection or evidence that every employer fills those fields.

### Employer-board moves — 2026-10-23

[Amplitude's careers page](https://amplitude.com/careers) now links to its
[Ashby board](https://jobs.ashbyhq.com/amplitude). [Wayve's official join page](https://wayve.ai/careers/join-us/)
redirects to its [Ashby board](https://jobs.ashbyhq.com/wayve). Move Amplitude's directory
entry to Ashby and remove only Wayve's obsolete Greenhouse entry; its existing Ashby entry
and country coverage remain. Do not remove an employer merely because an old board fails.

Rechecked the [documented public posting API](https://developers.ashbyhq.com/docs/public-job-posting-api)
and [customer terms](https://www.ashbyhq.com/resources/terms). Two bounded posting-API reads
returned listed jobs with full descriptions. The API host's robots file returned 401 again;
no HTML crawling permission is inferred. Existing documented posting-API use, access decisions
and request budgets remain. This verifies board identity, not market coverage or fresh-job recall.

### Lists that are gone rest — 2026-11-25

Lists move without notice: NXP's Workday address answered 422 for weeks after it moved, Dell
moved to Oracle, and search 21 found two Greenhouse boards gone. The directory is checked only now
and then, so a gone list cost a request and a line in every search's notes until someone removed it.
Now a directory list that answers "not found" (404 or 410) in searches at least seven days apart,
with no answer in between, rests: it isn't asked until 30 days after it was last found gone, then
once more; any answer clears it. The employer's new list is found by Jobcu itself, through the
links of job sites' copies of its jobs and the person's AI's employer look-up. Only "not found"
counts: a refusal, a human check or a server error never makes a list rest.

### Official town populations — 2026-11-24

Conditions about a town's size ("a city with at least 0.3% of the country's people") used GeoNames'
figures, which are of mixed age. Braunschweig had 244,715 people and Kiel 252,668, so with 0.3% of
Germany at about 250,500 Kiel counted and Braunschweig didn't. Destatis's official figures for
31.12.2024 (2022 census basis) are 252,962 and 252,668, so both count. GeoNames also gave Berlin
3,426,354 (official 3,685,265) and Frankfurt am Main 650,000 (official 756,021). Jobcu now ships
[Destatis's list of towns with town rights](https://www.destatis.de/DE/Themen/Laender-Regionen/Regionales/Gemeindeverzeichnis/Administrativ/05-staedte.html)
(`data/official_people.csv`, 2,059 towns; its cover sheet permits copying and passing it on with
the source named). Each figure goes to the town of the same full name in the same district (the
first five digits of the official key; the town list records the district), and to the biggest such
town (a city's parts list the city among their names). 1,720 German towns take the official figure.
Braunschweig now passes 0.3%; Gütersloh and Kaiserslautern pass 100,000, and Gera and Hildesheim fall
below it. `tools/update_official_people.py` rebuilds the file.

### Employers found through saved results — 2026-11-24

The saved result lists (2,145 different cards) were checked for employers with good matches whose own
career sites Jobcu didn't read. Most such employers were engineering agencies, whose ads already reach
Jobcu through job sites. Employers with their own boards on systems Jobcu reads were added with
`tools/check_employers.py` (one list read each): Agile Robots (Greenhouse, 67 jobs in Germany), Riedel
Communications (softgarden, 42), Mynaric (Personio, 26), planqc (Personio, 22 in Germany, Austria and
the UK), STABL Energy (Personio, 6) and Delta Energy Systems, whose
[robots file](https://application.delta-emea.com/robots.txt) lists a job sitemap whose pages carry
JobPosting data (20 jobs in Germany).

Not added: ABB's and Clarios' Workday lists ask automated tools not to read them (Clarios is on wd5,
behind the human check above). [Siemens' terms of use](https://www.siemens.com/global/en/general/terms-of-use.html)
forbid "text or data mining", including "any automated scraping": its Avature site is read only for a
person who accepts that in Settings ([its record](#avature-siemens-and-siemens-energy--2026-11-24)).
Advantest's jobs are on ADP Recruiting, which Jobcu has no
reader for. Saab's job pages are in its sitemap without JobPosting data. Brainlab, AECOM and ALTEN
use SmartRecruiters, read since 2026-11-24 for those who switch it on; Bosch's SmartRecruiters page
leads to its own site, whose robots.txt closes its job pages.

### SuccessFactors lists for the employer's own posting — 2026-11-24

A search reads each SuccessFactors site's whole list (its sitemap), and every address names the job's town
and title. A job only job sites listed, of such an employer, is matched against that list for the
employer's own posting (no extra request; a list the search didn't read is read once), and only the
closest titles' pages are opened. A replay on a copy of one saved search, reading today's lists, joined
Hensoldt's "Hardwareentwickler" (the card scored 80) and Advanced Energy's Cork design role (first posted
by the employer two weeks before a job site's date, so labelled a repost). A page that shows no ad (a
closed job still listed) is never taken for the posting. Addresses drop the slashes of "(m/w/d)", so the
title after the town is read without them.

### SuccessFactors titles the search words miss — 2026-11-21

The reader opened only pages whose address matched the search words, so a SuccessFactors title
the words miss never reached the person's AI, while other career systems' did (2,162 titles in
one search; four of its cards at 70 or more came from them, the best match of the list among
them). Now a job new on the list since its last reading (first seen within 36 hours of a reading
that didn't have it, `listmemory.posted`), whose address names a town in a country searched,
goes to the title check with the title its address spells; its page is opened only if the check
keeps it. Same sitemap and job pages, robots check and request budget; no page is opened that
the earlier rule wouldn't have opened for a matching title. A list's first reading dates
nothing, so the first search after a pause sends no such titles.

### SuccessFactors jobs posted for several towns — 2026-11-24

A job page can list several workplaces, in no set order: Nordex's power-electronics job listed
Sarriguren (Spain), Rostock and Hamburg. Jobcu took the first, so the job was in Spain on one reading
(and left out as outside the countries searched) and in Rostock on another, never matching the Hamburg
copy a job site had; that card linked to a middleman page with a 400-character excerpt instead of the
employer's 4,460-character ad. The site's own address for a job names its main town
(`/job/Hamburg-Power-Electronics-Engineer-...`), so Jobcu now takes the listed place in that town and
keeps the first place only when the address names none of them.

### SuccessFactors job layouts without a type or a date — 2026-11-14

**Checked:** one sitemap and one job page of each of the directory's 49 SuccessFactors
employers, then every page matching one saved search's words at 18 of them, all through the
reader's own terms, robots and polite-request gates (no new endpoint, page scope or allowance).

- 13 sites' job pages carry no `datePosted` (B. Braun, Danfoss, HARTING, Liebherr, Rohde &
  Schwarz, Sennheiser, SICK, sonnen, TE Connectivity, Vaillant, Vector Informatik, Vitesco
  Technologies, Webasto). Their jobs stay "Posting date unknown".
- On five of them (Danfoss, Liebherr, Rohde & Schwarz, sonnen, Webasto) the site's own job
  layout marks the title and the ad inside a block that says `itemscope` without a type. The
  reader took that block for some other item and kept nothing: 30 of 30 matching pages came in
  with the page address as the title and no text. It now reads an untyped block that holds the
  title or the ad as the job; a block of another named type is still left out. After the
  correction all 44 matching undated pages gave the full ad, and 31 pages of five dated sites
  read as before.
- Sitemaps keep listing closed jobs. Their pages answer 200 and show a short notice where the
  ad was ("this position has been filled"): the first listed page of three sites. A job block
  holding only such a notice (no title, layout part, apply link or part filled in later) is
  no job.
- One site marks its title twice; joined, the doubled title matched no job-site copy of the
  same job (all eight of its jobs in one saved search). A repeated title is read once.
- Two sites (Vector Informatik, Vitesco Technologies) fill the ad in with scripts; their pages
  give a title at most. Nothing is run or requested to get more.

This is a parser correction on pages already requested. It is not evidence about how many of
these employers' jobs the search words find, and the missing dates are not repaired by it.

**Dates from the list itself (same day).** The sitemap's `lastmod` is one day for every page
(487 of 487 on one site), so it dates nothing. Job numbers in the sitemap last: 12 of 23
numbers remembered from searches one to five weeks earlier are still on two sites' lists. Jobcu
therefore remembers each listed job's first sight and the reading before it (`listmemory.py`,
the list's public job numbers and reading times only) and dates an undated page from that: a
job that appeared between two readings at most 36 hours apart is posted on the day it was
first seen; one listed since before the search's window began is older than the window; a
list's first reading, a first sight after a longer pause, an empty answer and a list that is
mostly new at once date nothing. Checked end to end on two of the sites with a copy of a real
database (the earlier reading made up from the day's list without four matching jobs): those
four were dated to the day and kept, the 15 other matching jobs became older copies with their
full ads. It adds no request: the sitemap is read whole in every search already. What a real
second search a day later shows is not measured yet.

**One vacancy per language (same day).** These sites list a vacancy once per language, under
different numbers: 440 pairs among one site's 919 listed pages. Each listing became its own
job, so the same job showed as two cards (in one saved history, 18 of 54 career-site cards
were nine jobs twice), up to 12 points apart where only one version was in a language the
person spoke. Sites that number their vacancies send both pages to an address with that number
and the language (`/3387-de_DE/`, `/3387-en_US/`): the reader takes that as the site's word
that the listings are one vacancy. Sites that don't show the same untranslated ad under each
language's listing; there, listings with the same title, place and posting day are one when
their texts are identical, or their pages are in different languages and at least half of
their lines are the same (10 of 10 pairs on one site, 62 to 76% alike). Read with the
corrected reader, 43 matching pages of four sites are 31 jobs. Of a vacancy's versions the
search keeps the one the person reads best (their level in its language, then the job
country's own language). Pages are requested as before; nothing new is read.

### Original-ad sections and access boundaries — 2026-10-15

**Checked:** [Schema.org's JobPosting definition](https://schema.org/JobPosting) supplies
separate responsibilities, qualifications, skills, education, experience and eligibility
properties as well as `description`. [Experience](https://schema.org/experienceRequirements)
can be text or an object with months; [education](https://schema.org/educationRequirements)
can be a credential and explicitly allow experience instead. These definitions do not say
every skill is mandatory, or that a missing property means no requirement. Its
[terms](https://schema.org/docs/terms.html) cover the vocabulary, not permission to collect
an employer's pages. The correction consumes already requested markup, preserves wording and
alternatives, and adds no endpoint, page scope or request allowance.

[SAP's website terms](https://www.sap.com/about/legal/terms-of-use.html), revised 2026-02-26,
restrict automated extraction, persistent copying and passing site content to AI providers
without specific permission. Search-engine indexing exceptions do not grant Jobcu permission.
SAP-owned `sap.com` career pages are held before requests, including redirect destinations;
other employers' SuccessFactors sites remain subject to their own terms and robots rules.
This supersedes the older robots-only assumption for SAP's own directory entry. It is an
access restriction, not evidence that SAP jobs lack value or that the whole career system
should be removed. A permitted independent original/feed or explicit permission is needed
to reopen that direct collection. Existing private history is preserved.

**Checked 2026-10-07:** [Google's job-posting reference](https://developers.google.com/search/docs/appearance/structured-data/job-posting)
defines `identifier` as the hiring organization's unique job reference and `datePosted` as
the employer's original posting date. [Schema.org](https://schema.org/JobPosting) distinguishes
an identifier from a title/description. These are data definitions, not collection permission.
Jobcu applies them conservatively: an employer source's different listing IDs cannot be
collapsed by matching names or templates; an exact ID still supports repost detection.
This is an engineering inference from the adapter contract, not proof that every system uses
only one listing ID per real vacancy. Cross-site names and unknown legacy metadata remain
imperfect identity evidence; old merged history is preserved rather than guessed apart.

[SQLite's limits](https://www.sqlite.org/limits.html) allow device-specific parameter limits.
`jobidentity.rows` uses [Python 3.13's connection limit](https://docs.python.org/3.13/library/sqlite3.html#sqlite3.Connection.getlimit)
to bound batched reads; fictional regression checks lower the limit to 64.
[SQLite's transaction reference](https://www.sqlite.org/lang_transaction.html) explains that
`BEGIN IMMEDIATE` starts a write transaction before later reads/writes. Jobcu uses it to
serialize identity allocation; fictional simultaneous-save and rollback checks verify behavior.

### Greenhouse temporal evidence

**Rechecked 2026-10-09:** the [Job Board contract](https://docs.greenhouse.io/job-board.html)
separates `first_published`, `updated_at` and detail `application_deadline`; GET data is public.
The [API overview](https://support.greenhouse.io/hc/en-us/articles/10568627186203-Greenhouse-API-overview)
describes exporting public posts. The [legal portal](https://www.greenhouse.com/legal) links
subscription/privacy agreements; this is not a new license or permission for private APIs.
An actual public robots.txt read on boards-api.greenhouse.io returned HTTP 200 and disallowed
only `/embed/`. No vacancies were fetched for this research; existing budgets/blocked-host
rules remain. Only fields in the already-used list/detail response change interpretation.

Inference: modification does not establish first publication; missing/invalid original dates
stay unknown. A post date also cannot prove the underlying requisition is new: the contract
distinguishes post `id` from `internal_job_id`. Bulk `content=true` was a research lead here;
the dated implementation below supersedes that status. The same API overview says
Harvest endpoints require authentication; no private API access is introduced.

## Full-ad evidence and existing detail APIs

**Rechecked 2026-10-08:** [Google's job-posting reference](https://developers.google.com/search/docs/appearance/structured-data/job-posting)
requires a full description including duties, qualifications, skills, hours, education and
experience; `datePosted` means the employer's original posting date. These are data definitions,
not collection permission or proof that a particular site's text includes every condition.

[Greenhouse's Job Board API](https://docs.greenhouse.io/job-board.html) documents public GET
endpoints without authentication. Its job-list response omits content by default (the optional
`content=true` includes it); the individual job endpoint returns the full content. This supports
the existing separate list/detail reader, not unrestricted employer crawling or applications.
[Reed's jobseeker API](https://www.reed.co.uk/developers/jobseeker) likewise documents separate
search and job-ID detail endpoints: details include description and expiration, and a missing
job returns a blank response. It requires an API key via HTTP Basic authentication. Recruiter
API limits must not be assumed to apply to these jobseeker endpoints.

Inference for Jobcu: a list summary or failed detail read does not establish that the vacancy's
requirements are unavailable everywhere. Read another already-matched copy through its
existing permitted adapter; prefer the original employer when live reading is necessary.
Existing endpoints, terms/robots checks, source limits and access decisions are retained;
no source or collection permission is added by this coordinator change. Full text still needs
identity, completeness and bounded-age checks. Live recall/fit benefits need independent review.

### Greenhouse original lists and references — 2026-10-12

The [public Job Board contract](https://docs.greenhouse.io/job-board.html) was rechecked:
`content=true` includes full descriptions, departments and offices in the existing GET list;
individual GET details can still supply first publication and application deadlines.
The API host's robots.txt again returned 200 with only `/embed/` disallowed. Existing request
limits, blocked-host rules and public GET access remain; no Harvest access or application
submission is introduced. Larger list payloads trade bandwidth for earlier original evidence.

Official career references independently verify [ARX Robotics](https://www.arx-robotics.com/careers)
and [STARK's public career board](https://job-boards.eu.greenhouse.io/skdse) as Greenhouse feeds.
The directory records their individual check dates. Its other historic observations were not
re-certified. Source dates, underlying requisition identity, fit and current-window eligibility
are separate checks; a vendor's New label is not original publication evidence.

## Job-source cooldown protocol

**Checked 2026-10-08:** [RFC 9110 section 10.2.3](https://www.rfc-editor.org/rfc/rfc9110.html#name-retry-after)
defines Retry-After as either non-negative integer seconds or an HTTP date. It gives a minimum
delay before a follow-up request. [RFC 6585 section 4](https://www.rfc-editor.org/rfc/rfc6585.html#section-4)
defines 429 rate limiting, allows Retry-After and forbids caching a 429 response. It does not
prescribe whether a service applies limits per resource, host or account.

Jobcu conservatively shares a 429/5xx cooldown across readers of that host within one search,
including the last failed attempt. This is an engineering choice to avoid parallel readers
undercutting a delay, not proof that every provider has host-wide limits. Other hosts continue.
Valid delays are not shortened to Jobcu's ordinary backoff bound; zero and past dates remain
zero, while invalid headers use ordinary backoff. The established bot-protection test now
stops that host on its first recognized refusal, without retries or later network reads in
the same client. Already-running requests may finish; saved evidence remains usable.

[Python 3.13 date parsing](https://docs.python.org/3.13/library/email.utils.html#email.utils.parsedate_to_datetime)
supports HTTP-date forms, including legacy representations; invalid dates can raise ValueError.
[Timed lock acquisition](https://docs.python.org/3.13/library/threading.html#lock-objects)
allows queued readers to check Stop instead of waiting behind a long cooldown. Search and
condition-correction clients check Stop during waits. Fake-clock tests establish request
ordering and cancellation; they do not measure live source availability or job recall.

This changes retry coordination only: adapters, endpoints, minimum intervals, source limits
and robots/terms permissions are unchanged. No new vacancy collection permission is inferred.

## AI and Maps

### Electronics employer and specialist coverage — 2026-10-10

These primary references identify employer leads, **not collection licences, current jobs or
proof of missed vacancies**. Do not bulk-harvest member lists or use job-site accounts. Check
each employer's current terms/robots, actual career system and original-ad evidence before
adding it. Industry membership may include agencies, suppliers with no local hiring and
outdated acquired companies; independently verify identity and country.

| Country / route | Evidence and contribution hypothesis |
|---|---|
| Germany: sector employers | [ZVEI's sector board](https://www.zvei.org/verband/ueber-uns/vorstand) identifies power supplies, capacitors, semiconductors, PCB and automation employers, including inpotron and BLOCK. Hypothesis: specialist manufacturers can broaden coverage beyond familiar large brands; no vacancy benchmark established. |
| Ireland: microelectronics ecosystem | [MIDAS industry members](https://www.midasireland.ie/about-us/midas-company-members/) identifies design/research/manufacturing firms such as Emdalo, Icergi, Farran and Firecomms. A stronger sector-discovery reference than relying only on a general national board; no current relevant-job count inferred. |
| UK: electronics supply chain | [TechWorks member search](https://techworks.org.uk/members-searchable/) covers semiconductors, electronic systems and power electronics as well as other sectors/agencies. Candidate employer reference; no automatic collection right inferred. |
| Netherlands and Italy | [High Tech NL](https://www.hightechnl.nl/onzeleden/) separates semiconductor, energy and other clusters; [ANIE](https://anie.it/) represents electrotechnical/electronic industry. Candidate references, pending individual career-site checks and contribution evidence. Switzerland/Belgium need equally specific verified references, not guessed parity. |
| Original career-system gaps | [Bosch's FAQ](https://www.bosch.com/careers/faq/) confirms SmartRecruiters; Bosch's page there leads to jobs.bosch.com, whose robots.txt closes its job pages (2026-11-24). [ABB's application guide](https://careers.abb/global/en/how-to-apply) identifies Workday; its board (`abb.wd3`, External_Career_Page) asks automated tools not to read it (2026-11-24); its own Phenom site, careers.abb, allows job lists and pages and is read for those who accept ABB's terms ([2026-11-24](#phenom-career-sites--2026-11-24)). [Keysight's current career landing](https://jobs.keysight.com/external) is public; reachability does not establish an API/reader entitlement. Siemens' Avature site is read only for a person who accepts its terms in Settings ([2026-11-24](#avature-siemens-and-siemens-energy--2026-11-24)). |
| Specialist boards | [Engineers Ireland terms](https://www.engineersireland.ie/Terms-of-use) do not establish an automated vacancy licence. [Jobvector's legal page](https://www.jobvector.de/impressum.html) links separate terms; no permitted Jobcu feed established. IET's [platform terms](https://www.theiet.org/media/9621/iet-platform-general-terms.pdf) contain extraction restrictions; the applicable job-board terms/permission remain a dependency. Suitable public manual benchmarks need original dates and employer IDs. |
| Broader portals | [StepStone XML documentation](https://api.stepstone.com/knowledge-base/xml-guide-stepstone-de/) describes publishing ads, not a general vacancy-reading licence. [jobs.ch terms](https://www.jobs.ch/en/terms/) expressly restrict scraping and automation outside official tools. LinkedIn/Indeed and EURES dependencies above remain; no internal endpoint, cookies or blocked-host bypass is introduced. |

The shipped directory's existing electronics employers and unread systems were inspected
locally; its countries are historical observations, not verified today's coverage. A missing
directory entry does not prove a whole-search miss: an aggregator or discovered-employer
record may cover it. No list was fetched through Jobcu, source added/removed or private result
aggregate published. PULS/Agoria web research encountered robots restrictions; blocked pages
were not retried through another route. Rechecked permissions and a date-verified independent
sample are required before claiming additional recall. [Priority decision](ENGINEERING.md#source-reliability).

### Gemini running costs

**Rechecked 2026-10-15:** [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing)
lists Gemini 3.8 Flash standard input/output at USD0.75/3.75 per million through 2026-12-31,
then USD1.50/7.50 from 2027-01-01. Output includes thinking. Google Search grounding has
5,000 free monthly requests shared across Gemini 3 and newer models, then USD14/1,000;
the page's footnote says each performed search query is charged. One model request can
produce multiple queries. Grounding with Google Maps is a separate Gemini tool; it is not
Jobcu's directly called Routes matrix or its allowance.

Inference: count available grounding queries, other account work and thinking before forecasting;
do not add reasoning tokens twice or present a token-only estimate as an invoice. These are
public rates, not verified owner billing, tax, currency or remaining allowance.

### Priced grounding and spend controls — 2026-10-15

**Rechecked 2026-10-15:** [Google's grounding guide](https://ai.google.dev/gemini-api/docs/google-search#pricing)
counts unique nonempty queries within each request for Gemini 3 and newer; Gemini 2.5 and
older bill per grounded prompt. Repeated streaming metadata must not
inflate that count; a separate request can incur the same query charge again. The
[pricing table](https://ai.google.dev/gemini-api/docs/pricing) separately lists cached-input
rates and grounding fees; thinking is already billed with output. Shared free allowances
cannot be inferred from one app's ledger. The date of each price record limits its applicability.

[Google's billing guide](https://ai.google.dev/gemini-api/docs/billing#spend-caps) documents
experimental project spend caps in AI Studio's Spend page, with roughly ten minutes of possible
enforcement delay and overages. Prepay balances and billing graphs have different processing
delays. These controls are distinct from an estimated local ceiling and alerts-only Cloud
budgets. No billing account was accessed or changed for this research.

**Query controls rechecked 2026-10-17:** Google's [grounding guide](https://ai.google.dev/gemini-api/docs/google-search/)
prices each query selected by newer native models. The locked SDK's `GoogleSearch`/`ToolConfig`
and [Interactions generation configuration](https://ai.google.dev/api/interactions-api) expose
no documented hard query-count ceiling for built-in Google Search. Jobcu's request allowance
cannot enforce one inside the provider; prompt instructions or earlier observed counts are
not spending guarantees. Token maxima do not cap these query fees. Keep local estimates and
provider controls distinct, local token ceilings do not include every possible provider charge.

### Billing refusals and processing evidence — 2026-10-12

**Rechecked 2026-10-16:** Google's [billing documentation](https://ai.google.dev/gemini-api/docs/billing)
and [Interactions error reference](https://ai.google.dev/gemini-api/docs/api-errors) identify
exhausted prepay credit as HTTP 402 until replenishment. An active monthly spending cap is
separate from available prepaid credit; do not infer a particular account's balance from
this general contract. Delayed cut-off can create
a negative balance, deducted from the next purchase. Billing reports can lag; a balance
change alone cannot identify the charge for one run. This supports a terminal billing error,
not repeated minute-scale throttling waits or a diagnosis from a screenshot timestamp.

[Current pricing](https://ai.google.dev/gemini-api/docs/pricing) still lists 3.8 Flash standard
input/output USD0.75/3.75 per million through 2026-12-31, with thinking included in output.
Search queries have the documented shared free allowance and additional per-query fees.
Complete comparison includes failed work, retrieved content where charged, cache/storage,
tax/currency and separate Maps; local token estimates are not invoices.
The [Flex contract](https://ai.google.dev/gemini-api/docs/flex-inference) retains a 50% token
discount with variable 1–15-minute target latency, sheddable capacity, shared rate limits
and client-managed retries; there is no automatic Standard fallback. It uses Interactions
and is not implemented by Jobcu's Generate Content adapter. Batch can take up to 24 hours.
Equal-token half-price arithmetic does not measure actual latency/recovery or full savings.

### Long AI answers and streaming

**Retention rechecked 2026-10-15:** [Gemini additional terms](https://ai.google.dev/gemini-api/terms)
restrict storage of grounded results to specified purposes, including displayed-result evaluation
and end-user history (up to two years), or temporary refinement with deletion/display conditions.
Associated suggestions/links and use restrictions still apply. This is not permission for an
unrestricted hidden archive or a reusable fact database. Jobcu's new raw reference notes are
in-flight only and excluded from serialization; existing owner history is preserved. Durable
recovery or paid hosted-research experiments require verifying the exact refinement/display,
retention/expiry and reuse contract first.

**Checked 2026-10-10:** Google's [Generate Content API reference](https://ai.google.dev/api/generate-content)
documents `streamGenerateContent` with the same generation request fields, including tools and
generation configuration. The [official Python SDK](https://github.com/googleapis/python-genai#generate-content-synchronous-streaming)
exposes `models.generate_content_stream`; its examples consume successive response chunks.
The response contract includes terminal finish reasons, prompt feedback, grounding metadata
and request-level token usage. Schema-valid partial JSON does not establish completed generation.

The locked SDK 2.24.0 was inspected locally: its synchronous streaming path does not guarantee
closing an interrupted HTTP response. [HTTPX's public response hooks](https://www.python-httpx.org/advanced/event-hooks/)
run before the body is consumed and provide that response object. Inference for Jobcu: close
each request's tracked responses in `finally`, without closing the shared SDK client or another
thread's body. Tests use the actual locked SDK and an offline HTTPX transport; no provider call.

An [original developer report](https://discuss.ai.google.dev/t/60s-timeout-from-python-sdk/83274)
describes long non-streaming requests disconnecting around 60 seconds and reports streaming as
a workaround. It is a lead, not proof of a universal server deadline, the cause of a particular
connection failure or guaranteed improvement with current models. Streaming can also fail.
Preserve medium thinking and necessary evidence; verify completed answers, metadata and live
behavior rather than claim savings from a different transport alone. Existing service terms,
pricing, allowance and endpoint identities still apply; this adds no job source or access right.

### Grounding passage links — 2026-10-16

**Checked 2026-10-16.** Google's [Generate Content grounding contract](https://ai.google.dev/api/generate-content#GroundingSupport)
links claim segments to grounding-chunk indices. For streaming, indices refer to chunks
accumulated across all responses in order. Segment offsets are bytes within provider parts;
the segment also supplies corresponding text. The locked official SDK exposes these fields.
Inference for Jobcu: retain unique literal note passages with their source URLs rather than
guess Python character offsets across chunks or infer associations from duplicate page titles.
A provider attribution establishes provenance, not independent verification or a complete
condition. Missing/ambiguous links remain unknown. This uses the existing Generate Content
contract and adds no service, endpoint, retention right or paid-call authority.

### Grounding links are not followed — 2026-11-07

**Checked 2026-11-07.** The [Gemini API Additional Terms](https://aistudio.google.com/docs/terms)
(effective 2026-03-23), "Grounding with Google Search", define Links as "any other means to fetch
web pages (including hyperlinks and URLs)" in a Grounded Result, and call it a violation to
extract or collect them "for another purpose", for example "using programmatic or automated means
to collect Links" or "using Links to identify destination pages for crawling or scraping". Gemini's research sources are Google redirect links titled only with
the page's site: 209 of 215 sources in two recorded Jobcu searches (3.8 Flash, Interactions API).
Decision: Jobcu never requests a redirect link to learn its target. A redirect source names no
page, so it can't confirm an address an answer names (`livepostings.py` keeps an employer posting
only when a source names that page; the log counts sources that name no page). No request, retention
right or paid-call authority is added.

### Transport diagnosis limits — 2026-10-16

**Checked 2026-10-16.** In [SDK issue #1356](https://github.com/googleapis/python-genai/issues/1356),
a reporter described a disconnect after a minute despite longer timeouts, then attributed their
own case to an unstable client network. The maintainer could not reproduce it. In
[issue #2705](https://github.com/googleapis/python-genai/issues/2705), a maintainer confirmed
TCP keepalive prevented a reported NAT idle-eviction case. That report concerns longer silent
calls and a different failure mode; it does not identify every pre-header disconnect.

These are competing diagnostic leads, not proof of Jobcu's network path or a reason to change
reasoning/model settings. The locked SDK passes the configured timeout to HTTPX and its server
timeout header. A controlled reproduction and private transport evidence are needed before
claiming an increased deadline, keepalive or another network policy fixes a particular failure.

### Native reasoning refusals — 2026-10-15

**Checked 2026-10-15.** The official [OpenAI reasoning guide](https://developers.openai.com/api/docs/guides/reasoning)
distinguishes the requested reasoning effort, model defaults and billed reasoning tokens.
Omitting the setting is not a general proof of equal effort. Google's
[Generate Content thinking guide](https://ai.google.dev/gemini-api/docs/generate-content/thinking.md)
uses `thinking_config.thinking_level`, lists different supported levels and model defaults,
and distinguishes Gemini 2.5's budget control. This is the Generate Content contract Jobcu
uses; Interactions controls are not interchangeable.

Anthropic's [effort guide](https://platform.claude.com/docs/en/build-with-claude/effort) and
[thinking troubleshooting](https://platform.claude.com/docs/en/build-with-claude/thinking-troubleshooting)
distinguish whole-control support from rejected levels, thinking modes and per-turn effort.
A rejection of one value or combination does not mean the model lacks all effort controls.
These documents establish request distinctions, not every provider error's exact wording,
quality equivalence or live account availability. Jobcu's narrow refusal classifier is checked
with fictional SDK error payloads; unrecognized refusals preserve the requested setting.
See [implementation and limits](ENGINEERING.md#ai-providers-usage-and-recovery).

### Router reasoning and JSON formats — 2026-10-25

**Checked 2026-10-25.** OpenRouter's [reasoning tokens guide](https://openrouter.ai/docs/use-cases/reasoning-tokens)
documents the unified `reasoning` object (`effort` or `max_tokens`) and says Anthropic models
are enabled only through it; a top-level `reasoning_effort` is not documented there, although
its model list still accepts it. Small paid probes on zero-retention hosts with the same
calculation: two models on one host reasoned and answered correctly without a
`response_format`, but with a JSON schema or JSON object answered in about 20 tokens with no
reasoning and wrong values; `require_parameters` did not refuse those requests. Other tested
models reasoned with a JSON schema; one of them occasionally did not. Claude Sonnet 5.5 used
no reasoning on the probe with either control, also directly on Anthropic's API at medium and
high effort: its adaptive thinking decides per request, so zero reasoning there is the model's
choice, not a dropped control.

### Maps request limits and recovery

**Per-route outcomes rechecked 2026-10-09:** Google's [matrix reference](https://developers.google.com/maps/documentation/routes/reference/rest/v2/TopLevel/computeRouteMatrix)
separates each element's error status from its route-found condition; the
[matrix guide](https://developers.google.com/maps/documentation/routes/compute_route_matrix)
allows errors in individual elements of an otherwise successful response. `ROUTE_NOT_FOUND`
is an explicit outcome; an error, missing element or unusable duration does not establish it.
The [field-mask guide](https://developers.google.com/maps/documentation/routes/choose_fields)
says default protobuf values can be omitted, so a missing zero index/code is different from
an invalid index/code. Inference: preserve valid partial durations and leave unchecked
alternatives unknown; attribute any AI fallback separately, without storing Maps times as AI.
Google's [canonical error codes](https://github.com/googleapis/googleapis/blob/master/google/rpc/code.proto)
identify permission/authentication refusals (7/16) and exhausted resources (8). Jobcu stops
later network attempts after known access refusals or persistent per-element quota scope,
while preserving valid results from the same response. Raw status messages remain private.

[Policies](https://developers.google.com/maps/documentation/routes/policies),
[usage limits](https://developers.google.com/maps/documentation/routes/usage-and-billing) and
[global pricing](https://developers.google.com/maps/billing-and-pricing/pricing) were rechecked
the same day. Matrix limits/free caps/first-tier prices below remain listed; eligibility and
SKU depend on the account/features. Existing request dimensions, billing controls, attribution
and caching rules remain. No live route, key, billing or account change was used for research.

**Rechecked 2026-10-08:** [Routes usage and billing](https://developers.google.com/maps/documentation/routes/usage-and-billing)
counts matrix elements as origins × destinations; its documented standard rate is 3,000
elements/minute and transit matrices allow at most 100 elements. An owner's project can have
different configured quotas. Jobcu keeps its existing request dimensions and route cap.
[Current global pricing](https://developers.google.com/maps/billing-and-pricing/pricing) lists
10,000 free monthly Matrix Essentials elements, then USD5/1,000 in the first paid tier;
Matrix Pro lists 5,000 then USD10/1,000. Features determine the SKU. These are dated price facts,
not a guarantee of free requests, account eligibility or a recommendation to increase limits.

[Google's error design](https://google.aip.dev/193) identifies causes through ErrorInfo and
QuotaFailure details; raw messages can contain account/resource identifiers.
[Google's retry guidance](https://google.aip.dev/194) treats RESOURCE_EXHAUSTED as generally
non-retryable when replenishment may take hours or retries have billing implications.
[Maps web-service guidance](https://developers.google.com/maps/documentation/routes/web-service-best-practices)
supports increasing delays for recoverable failures. Inference: known daily/monthly/zero
quotas should stop immediately; temporary or unidentified throttling may recover through
bounded retries. Metadata availability is not promised for every response. Jobcu parses known
units/names when present, falls back to prose and labels an unidentified quota honestly.

[Routes policies](https://developers.google.com/maps/documentation/routes/policies) retain
content caching restrictions and Google Maps attribution; EEA terms depend on billing address.
No cross-search duration cache or new access is introduced. Attempted elements are counted
conservatively before every network attempt, including errors; this ledger is not a Google
invoice and cannot track usage from other apps. No live call or account/billing change was
made for this check. Measured fictional limits live in [ENGINEERING](ENGINEERING.md#locations-and-travel).

**Storage/reuse rechecked 2026-10-09:** the [Routes-specific contract, section 19.3](https://cloud.google.com/maps-platform/terms/maps-service-terms)
permits temporary latitude/longitude caching for 30 days, not an unrestricted duration cache.
The policy's indefinite exception is for place IDs. Do not transfer another API's exceptions
to Routes durations, or claim that the coordinate exception authorizes stored travel decisions.
Code inspection confirms Jobcu's independently sourced town coordinates and exact-request
in-memory reuse; these differ from retaining yesterday's Google journey time. Current terms
and time-sensitive timetables do not authorize indefinite location-only route reuse.

## Native streams and selected reference pages — 2026-10-18

**Responses control check, 2026-10-19:** OpenAI's current
[Responses reference](https://developers.openai.com/api/reference/cli/resources/responses/methods/create)
documents `max_tool_calls` as a total ceiling across built-in tools: further attempts are
ignored. Jobcu sends the already allowed research count through that field. This controls
tool calls, while token/retrieved-content charges and account limits remain separate.
The same reference distinguishes completed, failed and incomplete responses and provides
usage separately from output. Error outcomes must retain received usage rather than erase it.
The [current Gemini Interactions schema](https://ai.google.dev/api/interactions-api) does not
document a corresponding per-request hosted-query ceiling. A prompt instruction cannot create
that guarantee. These are dated protocol facts, not comparative matching results or a reason
to switch a configured provider automatically.

Google's [Interactions API](https://ai.google.dev/api/interactions-api) supports streaming,
structured response schemas, medium thinking and `store=false` without a previous interaction.
The [streaming guide](https://ai.google.dev/gemini-api/docs/streaming) documents early lifecycle
events and final completion. The [error guide](https://ai.google.dev/gemini-api/docs/api-errors)
distinguishes invalid requests, refusals, quotas and retryable server failures. A partial
usage object is not a complete receipt. SDK automatic retries are disabled; Jobcu owns attempts.

[Google Search grounding](https://ai.google.dev/gemini-api/docs/google-search) bills unique
queries for the relevant model generation, rather than one fixed fee per API request. The
current Google Search tool schema has no per-request query ceiling. An instruction asking for
four searches is not an enforced four-query limit. Directly supplied source text needs no
hosted search tool; input and output tokens still cost money. No invoice saving is established
by this contract alone.

The federal election authority's [official city/district tables](https://www.bundeswahlleiterin.de/dam/jcr/903d2260-fbd1-457f-a7d5-2580db9b0580/btw25_wbztabs_gesamt.pdf)
permit reproduction/distribution with attribution (PDF page 2). City rows can be split across
constituencies and multiple pages; counties and city states need their correct geographic
aggregation. Review the full geographic identifier rather than matching only the name
before a comma; an identically named surrounding county can occupy different table pages.
The [national results](https://www.bundeswahlleiterin.de/bundestagswahlen/2025/ergebnisse/bund-99.html)
provide the corresponding election baseline. A dated election file alone cannot establish
that a later election has not occurred.

[The PopuList](https://popu-list.org/) publishes classifications for public use with citation;
its [methodology](https://popu-list.org/elementor-page-1041/) explains coverage and expert review.
Version 4.0 covers national elections through May 2026; parties below its inclusion threshold
may be absent. Its vote-share graph is explicitly approximate and is not an official result.
Do not equate every unlisted party with a known negative category. Use official election
figures and explicit category coverage, or rigorous bounds for remaining unclassified votes.
Robots/access checks and the dated permission review remain required for each selected source.
Source selections, actual questions, evidence and verification receipts stay private.

**UK reference-data lead, checked 2026-10-19:** the [Commons Library data index](https://commonslibrary.parliament.uk/data/)
encourages re-use under the [Open Parliament Licence v3.0](https://www.parliament.uk/site-information/copyright/open-parliament-licence/),
with its required attribution and no implied endorsement. Its independent
[election-results service](https://electionresults.parliament.uk/) publishes verified results,
CSV downloads, a public SQLite export and a [data dictionary](https://electionresults.parliament.uk/meta/data-dictionary).
The [election index](https://electionresults.parliament.uk/elections) separates general elections,
by-elections and notional boundary-adjusted results. These cannot be interchanged in a city/
national comparison. A constituency/region is still not automatically a whole city; verify
the population/election geographic units, complete counts and category definition first.
Recheck robots/access for the chosen independent host; a blocked download does not authorise
another route to that blocked host. No city verdict follows from finding the dataset.


The federal civic-education agency's [dated election profiles](https://www.bpb.de/themen/parteien/wer-steht-zur-wahl/bundestagswahl-2025/)
identify expert authors and distinguish programme descriptions from quoted party claims. Its
[current publisher notice](https://www.bpb.de/die-bpb/ueber-uns/service/impressum/) was checked
on 2026-10-18. Review the selected article's date, author, applicable rights and robots before
reading it automatically; retain attribution and do not redistribute complete articles. An
ideological inference from an expert description must be labelled as an inference, rather than
misquoted as an explicit binary classification. These references can address gaps in another
dataset's coverage; a short programme summary alone does not prove every category comparison.

## Completion-state contracts — 2026-10-19

The [Chat completion object](https://developers.openai.com/api/reference/resources/chat)
defines natural stops, length limits, filters and tool/function calls; usage is optional in the
response schema. A compatible host must confirm completion rather than merely supply parseable
JSON. Missing primary counts cannot establish a complete zero-cost receipt.

Anthropic's [stop-reason guide](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons)
distinguishes finished turns/stop sequences, output limits, refusals, pending tools, paused
server-tool loops and context-window exhaustion. Continuing a paused turn is an additional
operation; Jobcu does not silently buy it or switch models. Installed-SDK fictional fixtures
verify parsing, receipts and retained controls. They do not establish another host's tariff,
cache premium, access rights or real matching/grounding quality.

## Additional access boundaries

These retained access observations were recorded in September–October 2026. Adapter parsing
and request budgets are defined in `src/jobcu/sources/`; public accessibility alone does not
establish collection permission.

Recorded access boundaries also cover SmartRecruiters' API (its career pages: see their record) and iCIMS hosts whose robots rules
refused Jobcu, Hays/Rise Technical terms that restricted collection, EURES' partner route,
and blocked publicjobs.ie, UK Civil Service Jobs and DWP Find a Job interfaces. These were not
implemented as bypasses. Historical employer/board counts are not current vacancy coverage.

**Learn4Good — 2026-11-02.** JSearch's only link for many UK and German ads. Its robots.txt allows
job pages and disallows `/jobs/index.php?controller=*`, the address of its "Bewerben" button
(`controller=job_page&action=click`); Jobcu never requests that address and only sends the
person's browser there on a click. Of 10 pages read from outside the UK, all 6 UK pages showed
no apply button but "View / Apply for Jobs Matching My Jurisdiction" ("jobs on this site that
accept applications from your location"); all 4 German pages had the button. The page says
applications from the visitor's country are not accepted "via this jobsite": a limit of the site,
not of the job. Its UK pages' text is a rewritten summary (a reworded title; one gave a different
town in its heading than in its text) and holds no link to the original. So its UK pages come
last among a job's links, the job stays, and for a good job the person's AI looks for the
employer's own posting online (`livepostings.py`).

## Native Xiaomi interface — recorded 2026-10-22

The [Chat API](https://mimo.mi.com/docs/en-US/api/chat/openai-api) documents the native endpoint,
enabled thinking, JSON-object output and completion tokens including thinking. It does not
promise a literal medium control. The [Web Search guide](https://mimo.mi.com/docs/en-US/quick-start/usage-guide/text-generation/tool-calling/web-search)
describes the separately activated plugin. Keyword/result limits do not bound total search
rounds or cost. Returned flat annotations do not establish passage-level citation mappings.

The [ordinary API agreement](https://mimo.mi.com/docs/quick-start/terms/user-agreement) and
[Token Plan terms](https://mimo.mi.com/docs/en-US/tokenplan/Token%20Plan/subscription) describe
different products/use restrictions. The [payment FAQ](https://mimo.mi.com/docs/en-US/quick-start/faq/payment)
describes delayed billing and possible negative balances. Alerts/prepayment do not establish
an exact currency ceiling. These are recorded interface/terms facts, not a provider recommendation.
