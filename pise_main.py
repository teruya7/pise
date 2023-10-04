from fire import Fire
from target import Target
from preparation import Preparation
from analysis import Analysis
from submission import Submission
from visualization import Visualization
from summary import Summury
from markdown import Markdown
from doping import Doping

Fire({
    "tar": Target, 
    "pre": Preparation,
    "ana": Analysis, 
    "vis": Visualization,
    "sum": Summury,
    "submit": Submission,
    "md": Markdown,
    "dope": Doping
    })