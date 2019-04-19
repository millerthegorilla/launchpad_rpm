from abc import ABCMeta, abstractmethod


class BasicClass(object):
    __metaclass__ = ABCMeta

    instance = None
    bob = 10

    def __new__(cls, *args, **kwargs):
        if not cls.instance:
            cls.instance = super(BasicClass, cls).__new__(
                                    cls, *args, **kwargs)

        return cls.instance

    @abstractmethod
    def action(self):
        pass # do something


class FirstLevelChild(BasicClass):
    # __metaclass__ = ABCMeta
    def __init__(self):
        self.bob = 10

    def jim(self):
        print(self.bob)

    def action(self):
        pass  # do something in this or other abstract method
        # also parent method can be called with help of super


class SecondLevelChild1(FirstLevelChild):
    def action(self):
        pass  # do something unique for this class
        # in this or other abstract method
        # also parent method can be called with help of super


class SecondLevelChild2(FirstLevelChild):
    def action(self):
        pass  # do something unique for this class
        # in this or other abstract method
        # also parent method can be called with help of super
