"""
FastAPI BluePrint implementation
"""
from enum import Enum
from typing import List, Callable
from collections import namedtuple
from dataclasses import dataclass, field

from fastapi import FastAPI

#** Variables **#
__all__ = ['Method', 'Route', 'BluePrint']

#** Classes **#

class Method(Enum):
    GET     = 'GET'
    PUT     = 'PUT'
    POST    = 'POST'
    DELETE  = 'DELETE'
    OPTIONS = 'OPTIONS' 

Route = namedtuple('Route', ('action', 'method', 'path', 'args', 'kwargs'))

@dataclass
class BluePrint:
    path:   str = '/'
    routes: List[Route] = field(default_factory=list)

    def route(self, method: Method, path: str, *args, **kwargs) -> Callable:
        """
        custom decorator to add given function to blueprint router

        :param method: method to use for routing
        :param path:   path to associated w/ specified route
        :param args:   positional argument to pass to router
        :param kwargs: keyword arguments to pass to router
        :return:       decorator function
        """
        def decorator(func: Callable) -> Callable:
            self.routes.append(Route(func, method, path, args, kwargs))
            return func
        return decorator

    def get(self, path: str, *args, **kwargs) -> Callable:
        """
        add decorated function as GET route to blueprint router

        :param path:   path to associated w/ specified route
        :param args:   positional args to pass to router
        :param kwargs: keyword arguments to pass to router
        :return:       decorator function
        """
        return self.route(Method.GET, path, *args, **kwargs)

    def put(self, path: str, *args, **kwargs) -> Callable:
        """
        add decorated function as PUT route to blueprint router

        :param path:   path to associated w/ specified route
        :param args:   positional args to pass to router
        :param kwargs: keyword arguments to pass to router
        :return:       decorator function
        """
        return self.route(Method.PUT, path, *args, **kwargs)

    def post(self, path: str, *args, **kwargs) -> Callable:
        """
        add decorated function as POST route to blueprint router

        :param path:   path to associated w/ specified route
        :param args:   positional args to pass to router
        :param kwargs: keyword arguments to pass to router
        :return:       decorator function
        """
        return self.route(Method.POST, path, *args, **kwargs)

    def delete(self, path: str, *args, **kwargs) -> Callable:
        """
        add decorated function as DELETE route to blueprint router

        :param path:   path to associated w/ specified route
        :param args:   positional args to pass to router
        :param kwargs: keyword arguments to pass to router
        :return:       decorator function
        """
        return self.route(Method.DELETE, path, *args, **kwargs)

    def apply_blueprint(self, app: FastAPI):
        """
        apply blueprinted routes to original app object

        :param app: fastapi app instance
        """
        for route in self.routes:
            path = f"{self.path.rstrip('/')}/{route.path.strip('/')}"  
            func = getattr(app, route.method.value.lower(), None)
            if func is None:
                raise RuntimeError(f'invalid http method: {route.method!r}')
            decorator = func(path, *route.args, **route.kwargs)
            decorator(route.action)
