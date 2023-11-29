class InvalidStatusValueError(Exception):
    def __init__(self, value: str) -> None:
        super().__init__(f"invalid status value: {value}")


class InvalidSportValueError(Exception):
    def __init__(self, value: str) -> None:
        super().__init__(f"invalid sport value: {value}")


class InvalidWeightClassValueError(Exception):
    def __init__(self, value: str) -> None:
        super().__init__(f"invalid weight class value: {value}")


class InvalidDateValueError(Exception):
    def __init__(self, value: str) -> None:
        super().__init__(f"invalid date value: {value}")


class InvalidBillingValueError(Exception):
    def __init__(self, value: str) -> None:
        super().__init__(f"invalid billing value: {value}")


class InvalidRoundFormatValueError(Exception):
    def __init__(self, value: str) -> None:
        super().__init__(f"invalid round format value: {value}")


class InvalidRoundTimePatternError(Exception):
    def __init__(self, pattern: str) -> None:
        super().__init__(f"invalid round time pattern: {pattern}")


class InvalidRoundPatternError(Exception):
    def __init__(self, pattern: str) -> None:
        super().__init__(f"invalid round pattern: {pattern}")


class InvalidMatchSummaryPatternError(Exception):
    def __init__(self, pattern: str) -> None:
        super().__init__(f"invalid match summary pattern: {pattern}")


class InvalidTitleInfoPatternError(Exception):
    def __init__(self, pattern: str) -> None:
        super().__init__(f"invalid title info pattern: {pattern}")


class InvalidOddsPatternError(Exception):
    def __init__(self, pattern: str) -> None:
        super().__init__(f"invalid odds pattern: {pattern}")


class InvalidWeightSummaryPatternError(Exception):
    def __init__(self, pattern: str) -> None:
        super().__init__(f"invalid weight summary pattern: {pattern}")


class InvalidRecordPatternError(Exception):
    def __init__(self, pattern: str) -> None:
        super().__init__(f"invalid record pattern: {pattern}")
