from django.db.models import QuerySet, Q


class ResourceQuerySet(QuerySet):

    def resources(self):
        return self.filter(~Q(isTrainingResource=True))

    def training_resources(self):
        return self.filter(isTrainingResource=True)

    def approved_resources(self):
        return self.resources().filter(approved=True)

    def approved_training_resources(self):
        return self.training_resources().filter(approved=True)