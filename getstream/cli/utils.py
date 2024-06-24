from functools import update_wrapper
import click


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
