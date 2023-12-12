class NormalizeError(Exception):
    def __init__(self, property: str, text: str) -> None:
        self.text = text
        self.property = property
        super().__init__(f'could not normalize text "{self.text}" as {self.property}')


class ParseError(Exception):
    def __init__(self, property: str, text: str) -> None:
        self.text = text
        self.property = property
        super().__init__(f'could not parse text "{self.text}" as {self.property}')


class InferError(Exception):
    def __init__(self, property: str, input: str) -> None:
        self.input = input
        self.property = property
        super().__init__(f'could not infer {self.property} from input "{self.input}"')
