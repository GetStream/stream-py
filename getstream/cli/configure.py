import configparser
import os
import sys

import click

CONFIG_PATH = os.path.expanduser('~/stream_cli_config.ini')

def get_config():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_PATH):
        config.read(CONFIG_PATH)
    return config

def save_config(config):
    try:
        with open(CONFIG_PATH, 'w') as configfile:
            config.write(configfile)
        click.echo(f"Configuration successfully written to {CONFIG_PATH}")
    except IOError as e:
        click.echo(f"Error writing configuration file: {e}", err=True)
        click.echo(f"Attempted to write to: {CONFIG_PATH}", err=True)
        sys.exit(1)

@click.command()
@click.option('--profile', default='default', help='Profile name')
@click.option('--api-key', prompt=True, help='API Key')
@click.option('--api-secret', prompt=True, hide_input=True, confirmation_prompt=True, help='API Secret')
@click.option('--app-name', prompt=True, help='Application Name')
def configure(profile, api_key, api_secret, app_name):
    config = get_config()
    if not config.has_section(profile):
        config.add_section(profile)
    
    config[profile]['api_key'] = api_key
    config[profile]['api_secret'] = api_secret
    config[profile]['app_name'] = app_name
    
    save_config(config)
    click.echo(f"Configuration for profile '{profile}' has been updated.")
    click.echo(f"Config file saved at: {CONFIG_PATH}")
    click.echo(f"API Key: {mask_value(api_key)}")
    click.echo(f"API Secret: {mask_value(api_secret)}")
    click.echo(f"App Name: {app_name}")


def get_credentials(profile='default'):
    config = get_config()
    if not config.has_section(profile):
        click.echo(f"Error: Profile '{profile}' not found.")
        click.echo(f"Config file path: {CONFIG_PATH}")
        click.echo(f"Available profiles: {', '.join(config.sections())}")
        return None, None, None
    
    section = config[profile]
    api_key = section.get('api_key')
    api_secret = section.get('api_secret')
    app_name = section.get('app_name')
    
    if not all([api_key, api_secret, app_name]):
        click.echo(f"Error: Incomplete configuration for profile '{profile}'.")
        click.echo(f"API Key: {'Set' if api_key else 'Not set'}")
        click.echo(f"API Secret: {'Set' if api_secret else 'Not set'}")
        click.echo(f"App Name: {'Set' if app_name else 'Not set'}")
        return None, None, None
    
    return api_key, api_secret, app_name

def mask_value(value):
    if len(value) <= 3:
        return '*' * len(value)
    return '*' * (len(value) - 3) + value[-3:]


@click.command()
@click.option('--profile', default='default', help='Profile name to display')
def show_config(profile):
    config = get_config()
    if not config.has_section(profile):
        click.echo(f"Profile '{profile}' not found.")
        return
    
    click.echo(f"Configuration for profile '{profile}':")
    click.echo(f"API Key: {mask_value(config[profile]['api_key'])}")
    click.echo(f"API Secret: {mask_value(config[profile]['api_secret'])}")
    click.echo(f"App Name: {config[profile]['app_name']}")


@click.command()
def debug_config():
    """Debug configuration"""
    click.echo(f"Config file path: {CONFIG_PATH}")
    click.echo(f"Config file exists: {os.path.exists(CONFIG_PATH)}")
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            click.echo("Config file contents:")
            click.echo(f.read())
    else:
        click.echo("Config file does not exist.")

@click.command()
def debug_permissions():
    """Debug file permissions"""
    home = os.path.expanduser('~')
    click.echo(f"Home directory: {home}")
    click.echo(f"Home directory writable: {os.access(home, os.W_OK)}")
    
    config_dir = os.path.dirname(CONFIG_PATH)
    click.echo(f"Config directory: {config_dir}")
    click.echo(f"Config directory exists: {os.path.exists(config_dir)}")
    if os.path.exists(config_dir):
        click.echo(f"Config directory writable: {os.access(config_dir, os.W_OK)}")
    
    click.echo(f"Config file path: {CONFIG_PATH}")
    click.echo(f"Config file exists: {os.path.exists(CONFIG_PATH)}")
    if os.path.exists(CONFIG_PATH):
        click.echo(f"Config file writable: {os.access(CONFIG_PATH, os.W_OK)}")
