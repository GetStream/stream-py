from functools import update_wrapper
import click

from typing import get_origin, get_args, Union

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
    """
    Get the name of a type
    """
    if hasattr(annotation, '__name__'):
        return annotation.__name__
    elif hasattr(annotation, '_name'):
        return annotation._name
    elif get_origin(annotation):
        origin = get_origin(annotation)
        args = get_args(annotation)
        if origin is Union and type(None) in args:
            # This is an Optional type
            return get_type_name(args[0])
        return f"{origin.__name__}[{', '.join(get_type_name(arg) for arg in args)}]"
    return str(annotation)


def parse_complex_type(value, annotation):
    """
    Parse a complex type from a JSON string
    """
    if isinstance(value, str):
        try:
            data_dict = json.loads(value)
            type_name = get_type_name(annotation)
            if type_name in globals():
                return globals()[type_name](**data_dict)
            else:
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
    # TODO: improve this to handle more complex types
    elif param.annotation == list:
        cmd = click.option(f'--{param_name}', multiple=True)(cmd)
    elif param.annotation == dict:
        cmd = json_option(f'--{param_name}')(cmd)
    else:
        cmd = json_option(f'--{param_name}')(cmd)
    return cmd
