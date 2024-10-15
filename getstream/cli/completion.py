import os
import sys
import click
from getstream.cli.configure import CONFIG_DIR, ensure_config_dir

COMPLETION_PATH = {
    'bash': os.path.join(CONFIG_DIR, 'completion.bash'),
    'zsh': os.path.join(CONFIG_DIR, 'completion.zsh'),
    'fish': os.path.join(CONFIG_DIR, 'completion.fish')
}


def install_completion_command():
    @click.command()
    @click.option('--shell', type=click.Choice(['bash', 'zsh', 'fish']), required=True)
    def install_completion(shell):
        """Install the completion script for the specified shell."""
        ensure_config_dir()
        script = f"_{os.path.basename(sys.argv[0]).replace('-', '_').upper()}_COMPLETE={shell}_source {sys.argv[0]}"
        path = COMPLETION_PATH[shell]
        with open(path, 'w') as f:
            f.write(script)
        click.echo(f"Completion script installed at {path}")
        click.echo(f"Add the following line to your ~/.{shell}rc by running:")
        click.echo(f"echo 'source {path}' >> ~/.{shell}rc")
        click.echo(f"Then restart your shell or run 'source ~/.{shell}rc' to enable completion.")
    
    return install_completion

def completion():
    """Returns the Click command object for completion"""
    from . import cli  # Import here to avoid circular imports
    return cli