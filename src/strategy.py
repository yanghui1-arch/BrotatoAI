class Strategy:
    strategy = {}

    @classmethod
    def register(cls, opt:str, func:callable):
        cls.strategy[opt] = func

    @property
    def access_strategy(self):
        return self.strategy
    
    def step(self, opt, **kwargs):
        self.strategy[opt](**kwargs)