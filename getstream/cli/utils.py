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
    Create a Click option that parses JSON input.

    This decorator creates a Click option that expects a JSON string as input.
    It attempts to parse the input string as JSON and passes the resulting
    Python object to the command function.

    Args:
        option_name (str): The name of the option to create.

    Returns:
        Callable: A decorator that adds a JSON-parsing option to a Click command.

    Raises:
        click.BadParameter: If the input cannot be parsed as valid JSON.

    Examples:
        >>> @click.command()
        ... @json_option('--data')
        ... def cmd(data):
        ...     click.echo(type(data))
        ...     click.echo(data)
        ...
        >>> runner = CliRunner()
        >>> result = runner.invoke(cmd, ['--data', '{"key": "value"}'])
        >>> print(result.output)
        <class 'dict'>
        {'key': 'value'}
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
    Get a string representation of a type annotation.

    This function handles various type hints, including basic types,
    List, Dict, Optional, and Union. It provides a consistent string
    representation for each type, which can be useful for generating
    documentation or type checking.

    Args:
        annotation (Any): The type annotation to convert to a string.

    Returns:
        str: A string representation of the type annotation.

    Examples:
        >>> get_type_name(str)
        'str'
        >>> get_type_name(List[int])
        'list[int]'
        >>> get_type_name(Optional[str])
        'union[str, NoneType]'
        >>> get_type_name(Union[str, int])
        'union[str, int]'
    """
    if annotation is Optional:
        return "Optional"
    if annotation is Union:
        return "Union"

    origin = get_origin(annotation)
    if origin is not None:
        if origin is Union:
            args = get_args(annotation)
            if len(args) == 2 and type(None) in args:
                # This is an Optional type
                other_type = next(arg for arg in args if arg is not type(None))
                return f"union[{get_type_name(other_type)}, NoneType]"
            else:
                args_str = ", ".join(get_type_name(arg) for arg in args)
                return f"union[{args_str}]"
        else:
            args = get_args(annotation)
            origin_name = origin.__name__.lower()
            if args:
                args_str = ", ".join(get_type_name(arg) for arg in args)
                return f"{origin_name}[{args_str}]"
            return origin_name

    if hasattr(annotation, "__name__"):
        return annotation.__name__

    return str(annotation)


def parse_complex_type(value, annotation):
    """
    Parse a complex type from a JSON string or return the original value if it's not JSON.

    Args:
        value (str): The input value to parse.
        annotation (Type[Any]): The type annotation for the expected result.

    Returns:
        Any: The parsed data, either as an instance of the annotated class
             or as a basic Python data structure, or the original value if not JSON.

    Raises:
        click.BadParameter: If the input is invalid JSON and the annotation expects a complex type.
    """
    if value is None:
        return None

    if isinstance(value, str):
        try:
            data = json.loads(value)
        except json.JSONDecodeError:
            if annotation in (dict, list) or (
                hasattr(annotation, "__origin__")
                and annotation.__origin__ in (dict, list)
            ):
                raise click.BadParameter(f"Invalid JSON for '{annotation}' parameter")
            return value

        if isinstance(annotation, type):  # Check if annotation is a class
            try:
                return annotation(**data)
            except TypeError:
                # If we can't instantiate the class, just return the parsed data
                return data
        return data
    return value


def add_option_from_arg(cmd, param_name, param):
    """
    Add a Click option to a command based on a function parameter.

    This function inspects the given parameter and adds an appropriate
    Click option to the command. It handles basic types (str, int, bool),
    as well as more complex types like lists and dicts.

    Args:
        cmd (Callable): The Click command to add the option to.
        param_name (str): The name of the parameter.
        param (Parameter): The inspect.Parameter object representing the function parameter.

    Returns:
        Callable: The modified Click command with the new option added.

    Examples:
        >>> @click.command()
        ... def hello():
        ...     pass
        >>> param = inspect.Parameter('name', inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=str)
        >>> hello = add_option_from_arg(hello, 'name', param)
        >>> hello.params[0].name
        'name'
        >>> hello.params[0].type
        <class 'str'>
    """
    type_name = get_type_name(param.annotation)
    print(f"Adding option for {param_name} with type {type_name}")

    if type_name == "bool":
        cmd = click.option(f"--{param_name}", is_flag=True, default=False)(cmd)
    elif type_name == "str":
        cmd = click.option(f"--{param_name}", type=str)(cmd)
    elif type_name == "int":
        cmd = click.option(f"--{param_name}", type=int)(cmd)
    elif type_name.startswith("list"):
        cmd = click.option(f"--{param_name}", multiple=True)(cmd)
    elif type_name == "dict":
        cmd = json_option(f"--{param_name}")(cmd)
    elif type_name.startswith("union") or type_name.startswith("Optional"):
        cmd = click.option(f"--{param_name}", callback=parse_union_type)(cmd)
    else:
        cmd = click.option(
            f"--{param_name}",
            callback=lambda ctx, param, value: parse_complex_type(
                value, param.annotation
            ),
        )(cmd)

    return cmd


def parse_union_type(ctx, param, value):
    if value is None:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value  # If it's not valid JSON, return the original string
