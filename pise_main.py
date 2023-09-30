from fire import Fire
from target import Target
from preparation import Preparation
from analysis import Analysis
from submittion import Submittion
from visualization import Visualization
from summary import Summury
from markdown import Markdown
from error import Error
from doping import Doping

Fire({
    "tar": Target, 
    "pre": Preparation,
    "er": Error,
    "ana": Analysis, 
    "vis": Visualization,
    "sum": Summury,
    "submit": Submittion,
    "md": Markdown,
    "dope": Doping
    })