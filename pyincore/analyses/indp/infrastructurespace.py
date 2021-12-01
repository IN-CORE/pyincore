class InfrastructureSpace(object):
    """
    This class models a geographical space.

    Attributes
    ----------
    id : int
        The id of the space
    cost : float
        The cost of preparing the space for a repair action
    """

    def __init__(self, id, cost):
        self.id = id
        self.cost = cost
