class APIFail(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class NoReleasingAnime(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)