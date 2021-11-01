from dataclasses import dataclass


@dataclass
class PreviewOptions:
    empty_line_before_difference: bool = False
    """
    Indicates whether or not to emit an an empty line before the difference
    visualisation if there is one.
    """
