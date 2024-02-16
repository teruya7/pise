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
from database import Database
from search import Search
from error_handler import ErrorHandler

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
    "db": Database,
    "search": Search,
    "eh": ErrorHandler
    })