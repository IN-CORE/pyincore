class BuildingDamage(object):

    def __init__(self, distance_to_center, restricted_entry, restricted_use, reoccupancy, best_line_functionality,
                 full_functionality):
        self.distance_to_center = distance_to_center
        self.restricted_entry = restricted_entry
        self.restricted_use = restricted_use
        self.reoccupancy = reoccupancy
        self.best_line_functionality = best_line_functionality
        self.full_functionality = full_functionality
