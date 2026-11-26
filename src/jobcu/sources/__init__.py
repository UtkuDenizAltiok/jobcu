"""Job sources: one isolated module per source. A failing source never breaks a search."""

from jobcu.settings import Settings
from jobcu.sources.adzuna import AdzunaSource
from jobcu.sources.arbeitnow import ArbeitnowSource
from jobcu.sources.ashby import AshbySource
from jobcu.sources.avature import AvatureSource
from jobcu.sources.base import JobSource
from jobcu.sources.bundesagentur import BundesagenturSource
from jobcu.sources.careers import CareerSystemSource
from jobcu.sources.dvinci import DvinciSource
from jobcu.sources.eightfold import EightfoldSource
from jobcu.sources.euraxess import EuraxessSource
from jobcu.sources.freehire import FreeHireSource
from jobcu.sources.gradcracker import GradcrackerSource
from jobcu.sources.greenhouse import GreenhouseSource
from jobcu.sources.jibe import JibeSource
from jobcu.sources.jobsacuk import JobsAcUkSource
from jobcu.sources.jobsireland import JobsIrelandSource
from jobcu.sources.jobtech import JobTechSource
from jobcu.sources.jobvite import JobviteSource
from jobcu.sources.jsearch import JSearchSource
from jobcu.sources.leforem import LeForemSource
from jobcu.sources.lever import LeverSource
from jobcu.sources.listpages import ListPageSource
from jobcu.sources.nav import NavSource
from jobcu.sources.nhsjobs import NhsJobsSource
from jobcu.sources.oracle import OracleSource
from jobcu.sources.personio import PersonioSource
from jobcu.sources.phenom import PhenomSource
from jobcu.sources.pinpoint import PinpointSource
from jobcu.sources.prospective import ProspectiveSource
from jobcu.sources.recruitee import RecruiteeSource
from jobcu.sources.reed import ReedSource
from jobcu.sources.servicebund import ServiceBundSource
from jobcu.sources.sitemaps import SitemapSource
from jobcu.sources.smartrecruiters import SmartRecruitersSource
from jobcu.sources.softgarden import SoftgardenSource
from jobcu.sources.successfactors import SuccessFactorsSource
from jobcu.sources.teachingvacancies import TeachingVacanciesSource
from jobcu.sources.teamtailor import TeamtailorSource
from jobcu.sources.werkenvoornederland import WerkenVoorNederlandSource
from jobcu.sources.workable import WorkableSource
from jobcu.sources.workday import WorkdaySource

# Sources whose site terms don't allow automated reading: read only for a person who switches
# them on and so accepts that (the owner's choice for the Bundesagentur, 2026-10-30, after its
# support desk neither gave nor refused permission). Settings shows each one's note.
TERMS_NOTES = {
    "bundesagentur": "Its portal terms (8 July 2026) don't allow automated reading. Switch it "
                     "on only if you accept that for your own job search.",
    # Siemens' terms of use forbid "text or data mining" of its websites (2026-11-24); no
    # record of Siemens acting against readers of its job lists was found (SOURCES).
    "avature": "Siemens' website terms don't allow automated reading (text and data mining). "
               "Switch it on only if you accept that for your own job search.",
    # SmartRecruiters' terms for job seekers forbid "automatic means to access content or data
    # from other users" (2026-11-24); no legal action against readers of job pages was found.
    "smartrecruiters": "SmartRecruiters' terms for job seekers don't allow automatic means to "
                       "read its pages. Switch it on only if you accept that for your own job "
                       "search.",
    # ABB's website terms require its written permission for scraping (2026-11-24); no legal
    # action against readers of job lists was found.
    "phenom": "ABB's website terms don't allow scraping without its written permission. Switch "
              "it on only if you accept that for your own job search.",
    # Gradcracker's legal page forbids scraping and allows copies for reading or browsing and
    # for personal use (2026-11-25); no legal action against readers was found.
    "gradcracker": "Gradcracker's legal page doesn't allow scraping (it allows copies for "
                   "reading and for your personal use). Switch it on only if you accept that "
                   "for your own job search.",
    # Jobvite's terms of use forbid scraping content "on or through" its site (2026-11-26); no
    # legal action against readers of job pages was found.
    "jobvite": "Jobvite's terms of use don't allow scraping its content. Switch it on only if "
               "you accept that for your own job search.",
}
OPT_IN_SOURCES = frozenset({"jsearch", *TERMS_NOTES})


def disabled_sources(settings: Settings) -> list[str]:
    return sorted(set(settings.sources_disabled) | (OPT_IN_SOURCES - set(settings.source_opt_ins)))


def accepted_terms(settings: Settings) -> frozenset[str]:
    """The sources with restrictive terms that this person switched on."""
    return frozenset(TERMS_NOTES) - set(disabled_sources(settings))


def career_sources() -> list[CareerSystemSource]:
    """Company career systems, read for the employers in the employer directory."""
    return [AshbySource(), AvatureSource(), DvinciSource(), EightfoldSource(),
            GreenhouseSource(), JibeSource(), JobviteSource(), LeverSource(), ListPageSource(),
            OracleSource(),
            PersonioSource(), PhenomSource(), PinpointSource(), ProspectiveSource(),
            RecruiteeSource(), SitemapSource(), SmartRecruitersSource(), SoftgardenSource(),
            SuccessFactorsSource(), TeamtailorSource(), WorkableSource(), WorkdaySource()]


def all_sources() -> list[JobSource]:
    """Fresh source objects for one search, in the order they're shown."""
    return [AdzunaSource(), JSearchSource(), ArbeitnowSource(), FreeHireSource(), JobTechSource(),
            BundesagenturSource(), ServiceBundSource(), EuraxessSource(), JobsAcUkSource(),
            GradcrackerSource(), JobsIrelandSource(),
            ReedSource(), TeachingVacanciesSource(), NhsJobsSource(), LeForemSource(),
            WerkenVoorNederlandSource(), NavSource(), *career_sources()]
