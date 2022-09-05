"""
Streamy Remote `Action` REST API
"""
from ...utils import BluePrint

#** Variables **#

api = BluePrint('/api/v1/action/')

#** Routes **#

@api.get('/back/')
def back():
    pass

@api.get('/next/')
def next():
    pass

@api.get('/pause/')
def pause():
    pass

@api.get('/shuffle/{state}')
def shuffle(state: str):
    pass
