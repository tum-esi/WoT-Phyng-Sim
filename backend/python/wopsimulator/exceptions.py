class CaseTypeError(Exception):
    """Incorrect case type"""
    pass


class CaseNotFound(Exception):
    """Required case was not found"""
    pass


class CaseAlreadyExists(Exception):
    """Case cannot be created as it already exists"""
    pass


class WrongPhyngType(Exception):
    """Wrong phyng type error"""
    pass


class PhyngNotFound(Exception):
    """Required phyng was not found"""
    pass


class PhyngSetValueFailed(Exception):
    """Phyng value setting failed"""
    pass
