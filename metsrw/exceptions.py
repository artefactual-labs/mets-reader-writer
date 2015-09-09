class MetsError(Exception):
    """ Base Exception for this module. """
    pass


class ParseError(MetsError):
    """ Error parsing a METS file. """
    pass
