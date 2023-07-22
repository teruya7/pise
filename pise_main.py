from fire import Fire
from calc_info import CalcInfoMaker
from target_info import TargetInfoMaker
from preparation_info import PreparationInfoMaker
from analysis_info import AnalysisInfoMaker
from submittion import JobSubmitter
from visual_info import VisualInfoMaker
from summary_info import SummuryInfoMaker
from markdown import MarkdownMaker
from error_info import ErrorInfoMaker

Fire({
    "ti": TargetInfoMaker, 
    "ci": CalcInfoMaker, 
    "pi": PreparationInfoMaker,
    "ei": ErrorInfoMaker,
    "ai": AnalysisInfoMaker, 
    "vi": VisualInfoMaker,
    "si": SummuryInfoMaker,
    "submit": JobSubmitter,
    "md": MarkdownMaker
    })