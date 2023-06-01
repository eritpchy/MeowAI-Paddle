class ClasTag:
    def __init__(self, id, label, score, exclude):
        self.id = id
        self.label = label
        self.score = round(score, 3) if score else 0
        self.exclude = exclude