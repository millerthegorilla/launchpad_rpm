from collections import UserList
from multiprocessing.dummy import Pool as ThreadPool


class Dave(UserList):
    def __init__(self):
        super(Dave, self).__init__()
        self.append('bob')
        self.append('jim')
        self.append('steve')
        self.append('kim')
        self.threadpool = ThreadPool(10)
        self._i = 0

    def process(self):
        for i in self:
            yield i
