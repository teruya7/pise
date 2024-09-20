from fire import Fire
from target import Target
from preparation import Preparation
from analysis import Analysis
from submission import Submission
from visualization import Visualization
from summary import Summury
from markdown import Markdown
from doping import Doping
from calculation import Calculation
from cpd import Cpd
from search import Search
from error_handler import ErrorHandler
from vasp_speed_test import VaspSpeedTest
from collect import Collect

Fire({
    "tar": Target,
    "cal": Calculation, 
    "pre": Preparation,
    "ana": Analysis, 
    "vis": Visualization,
    "sum": Summury,
    "submit": Submission,
    "md": Markdown,
    "dp": Doping,
    "cpd": Cpd,
    "search": Search,
    "eh": ErrorHandler,
    "sp": VaspSpeedTest,
    "col": Collect
    })