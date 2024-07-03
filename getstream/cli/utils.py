from functools import update_wrapper
import click

from typing import get_origin, get_args, List, Dict, Optional, Union


import json

def pass_client(f):
    """
    Decorator that adds the Stream client to the decorated function, with this decorator you can write click commands like this

    @click.command()
    @click.option("--some-option")
    @pass_client
    def do_something(client: Stream, some_option):
        pass

    """

    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        return ctx.invoke(f, ctx.obj["client"], *args, **kwargs)

    return update_wrapper(new_func, f)

def json_option(option_name):
    """
    Decorator that adds a JSON option to the decorated function, with this decorator you can write click commands like this

    @click.command()
    @json_option("--some-option")
    def do_something(some_option):
        pass

    """
    def decorator(f):
        def callback(ctx, param, value):
            if value is not None:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    raise click.BadParameter("Invalid JSON")
            return value

        return click.option(option_name, callback=callback)(f)
    return decorator


def get_type_name(annotation):
    if annotation is Optional:
        return 'Optional'
    if annotation is Union:
        return 'Union'
    
    origin = get_origin(annotation)
    if origin is not None:
        if origin is Union:
            args = get_args(annotation)
            if len(args) == 2 and type(None) in args:
                # This is an Optional type
                other_type = next(arg for arg in args if arg is not type(None))
                return f'union[{get_type_name(other_type)}, NoneType]'
            else:
                args_str = ', '.join(get_type_name(arg) for arg in args)
                return f'union[{args_str}]'
        else:
            args = get_args(annotation)
            origin_name = origin.__name__.lower()
            if args:
                args_str = ', '.join(get_type_name(arg) for arg in args)
                return f"{origin_name}[{args_str}]"
            return origin_name
    
    if hasattr(annotation, '__name__'):
        return annotation.__name__
    
    return str(annotation)


def parse_complex_type(value, annotation):
    if isinstance(value, str):
        try:
            data_dict = json.loads(value)
            if isinstance(annotation, type):  # Check if annotation is a class
                try:
                    return annotation(**data_dict)
                except TypeError:
                    # If we can't instantiate the class, just return the dict
                    return data_dict
            return data_dict
        except json.JSONDecodeError:
            raise click.BadParameter(f"Invalid JSON for '{annotation}' parameter")
    return value


def add_option_from_arg(cmd, param_name, param):
    if param.annotation == str:
        cmd = click.option(f'--{param_name}', type=str)(cmd)
    elif param.annotation == int:
        cmd = click.option(f'--{param_name}', type=int)(cmd)
    elif param.annotation == bool:
        cmd = click.option(f'--{param_name}', is_flag=True)(cmd)
    elif get_origin(param.annotation) == list:
        cmd = click.option(f'--{param_name}', multiple=True)(cmd)
    elif param.annotation == dict:
        cmd = json_option(f'--{param_name}')(cmd)
    else:
        cmd = json_option(f'--{param_name}')(cmd)
    return cmd