import configparser
import os
import click

CONFIG_DIR = os.path.expanduser('~/.stream-cli')
CONFIG_PATH = os.path.join(CONFIG_DIR, 'config.ini')

def ensure_config_dir():
    os.makedirs(CONFIG_DIR, exist_ok=True)

def get_config():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_PATH):
        config.read(CONFIG_PATH)
    return config

def save_config(config):
    ensure_config_dir()
    with open(CONFIG_PATH, 'w') as configfile:
        config.write(configfile)

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

@click.command()
@click.option('--profile', default='default', help='Profile name to display')
def show_config(profile):
    config = get_config()
    if not config.has_section(profile):
        click.echo(f"Profile '{profile}' not found.")
        return
    
    click.echo(f"Configuration for profile '{profile}':")
    click.echo(f"API Key: {'*' * 10}{config[profile]['api_key'][-3:]}")
    click.echo(f"API Secret: {'*' * 13}")
    click.echo(f"App Name: {config[profile]['app_name']}")

def mask_value(value):
    if len(value) <= 3:
        return '*' * len(value)
    return '*' * (len(value) - 3) + value[-3:]