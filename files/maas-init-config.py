#!/usr/bin/env python3
from maas.client import connect
from maas.client.bones import CallError
from maas.client.utils.async import asynchronous
from maas.client.enum import IPRangeType

import argparse, os
import yaml




class EnvDefault(argparse.Action):
    def __init__(self, envvar, required=True, default=None, **kwargs):
        if not default and envvar:
            if envvar in os.environ:
                default = os.environ[envvar]
        if required and default:
            required = False
        super(EnvDefault, self).__init__(default=default, required=required, 
                                         **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)


@asynchronous
async def enable_dhcp():
    try:
        fabric = await client.fabrics.get_default()
        untagged = fabric.vlans.get_default()

        racks = await client.rack_controllers.list()
        untagged.dhcp_on = True
        untagged.primary_rack = racks[0]
        if racks[1]:
            untagged.secondary_rack = racks[1]
        await untagged.save()
    except Exception as e:
        print('Failed to enable DHCP:\n', e)    
    else:
        print('DHCP enabled.')


@asynchronous
async def create_ip_ranage(start_ip, end_ip, comment=None):
    current_ranges = await client.ip_ranges.list()
    for range in current_ranges:
        try:
            assert range.start_ip is start_ip and range.end_ip is end_ip
        except Exception as e:
            print('IP Range exists on subnet:', range.subnet.cidr)
            return          
    try:
        range_create = await client.ip_ranges.create(
            start_ip,
            end_ip,
            comment=comment,
            type=IPRangeType.DYNAMIC
            )
    except Exception as e:
        print('Failed to create IP Range:\n', e)
    else:
        print('Created new IP Range: %s-%s' % (start_ip, end_ip))


def create_ip_ranages(subnets=list()):
    for subnet in subnets:
        for range in subnets.get(subnet).get('reserved'):
            create_ip_ranage(range['start_ip'], range['end_ip'])


@asynchronous
async def create_spaces(spaces=list()):
    print('Space:')
    # get names of current spaces
    cur_spaces = list()
    for zone in await client.spaces.list():
        cur_spaces.append(zone.name)
    # create new spaces
    for new_space in spaces:
        if new_space in cur_spaces:
            print('  %s: exists, skipping.' % new_space)
        else:
            try:
                print('space test')
                await client.spaces.create(name=new_space)
            except Exception as e:
                print('  %s: error creating: %s' % (new_space, e))
            else:
                print('  %s: created.' % new_space)



@asynchronous
async def create_zones(zones=list()):
    print('Zones:')
    # get names of current zones
    czs = list()
    for zone in await client.zones.list():
        czs.append(zone.name)
    # create new zones
    for nz in zones:
        if nz['name'] in czs:
            print('  %s: exists, skipping.' % nz['name'])
        elif nz['name'] != 'default':
            try:
                await client.zones.create(name=nz['name'], description=nz['description'])
            except Exception as e:
                print('  %s: error creating: %s' % (nz['name'], e))
            else:
                print('  %s: created.' % nz['name'])


@asynchronous
async def configure_domains(domains=list()):
    print('Domains: Not implemented in API.')
    # cur_domains = list()
    # for domain in await client.domains.list():
    #   cur_domains.append(domain.name)
    for domain in domains:
        # await client.domains.create(domain)
        print('  Would create domain: %s' % domain)


@asynchronous
async def configure_settings(config):
    print('Configuring MAAS Settings.')
    await client.maas.set_default_os(config['default_osystem'])
    await client.maas.set_default_distro_series(config['default_distro_series'])
    await client.maas.set_commissioning_distro_series(config['commissioning_distro_series'])
    await client.maas.set_default_min_hwe_kernel(config['default_min_hwe_kernel'])
    # await client.maas.set_kernel_options(config['kernel_opts'])
    await client.maas.set_name(config['maas_name'])
    await client.maas.set_upstream_dns(config['upstream_dns'])
    # await client.maas.set_dnssec_validation(MAASType.DNSSEC.looup(config['dnssec_validation']))
    await client.maas.set_config('dnssec_validation', config['dnssec_validation'])
    await client.maas.set_ntp_server(' '.join(config['ntp_servers']))
    await client.maas.set_config('ntp_external_only', config['ntp_use_external_only'])
    # await client.maas.set_config('network_discovery', config['network_discovery'])
    # await client.maas.set_config('active_discovery_interval', config['active_discovery_interval'])
    # await client.maas.set_enable_third_party_drivers(config.enable_third_party_drivers)


@asynchronous
async def pre_flight():
    myself = await client.users.whoami()
    assert myself.is_admin, "%s is not an admin" % myself.username
    # Check for a MAAS server capability.
    version = await client.version.get()
    assert "devices-management" in version.capabilities
    # Check the default OS and distro series for deployments.
    print('Who am I? %s' % myself.username)
    print('Where am I? %s\n' % args.maas_url)



_PROG_DESC_ = """
MAAS Initial Configuration

Performs post install setup of MAAS to provide a working network.

Not Production ready!
"""


parser = argparse.ArgumentParser(
    #prog='maas-init-config',
    description=_PROG_DESC_,
    epilog='Careful.',
    formatter_class=argparse.RawDescriptionHelpFormatter,)
parser.add_argument('-k', '--apikey', action=EnvDefault, envvar='MAAS_APIKEY', help='MAAS API key')
parser.add_argument('--maas-url', action=EnvDefault, envvar='MAAS_URL', help='MAAS API URL', default="http://localhost:5240/MAAS/")
parser.add_argument('--do-domains', action='store_true', help='create domains')
parser.add_argument('--do-spaces', action='store_true', help='create spaces')
parser.add_argument('config_file', help='YAML configuration file path')
args = parser.parse_args()




try:
    # http://$host:$port/MAAS/account/prefs/.
    client = connect(args.maas_url, apikey=args.apikey)
except CallError as e:
    print('Error: %s' % e)


## load yaml config file
try:
    cfh = open(args.config_file, 'r')
    config_yaml = yaml.safe_load(cfh)
except FileNotFoundError as fe:
    print("Error: config_file not found: '%sn'" % args.config_file)
    exit(1)
except Exception as e:
    print('Error: %sn' % str(e))
    exit(1)


pre_flight()

configure_settings(config_yaml)

if args.do_domains:
    configure_domains(config_yaml['dns_domains'])

create_zones(config_yaml['zones'])

if args.do_spaces:
    create_spaces(config_yaml['spaces'])

create_ip_ranages(config_yaml['subnets'])

enable_dhcp()

