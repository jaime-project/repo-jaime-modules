from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List

import requests
import tools
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

params = tools.get_params()

namespace = params['namespace']
cluster_name = params['cluster']
pushgateway_url = params['pushgateway-url']

tenants_dicts = params['tenants']


# ----------------------------------------------
# OBTENCION DE DATOS
# ----------------------------------------------

def adapted_name(name: str) -> str:
    return str(name).lower().replace(' ', '_').replace("""'""", '').replace('-', '_').replace('ñ', 'ni')


@dataclass
class Account():
    id: int
    name: str
    state: str


@dataclass
class App():
    id: int
    name: str
    description: str
    state: str
    service_id: int
    hits: int = 0


@dataclass
class Product():
    id: int
    name: str
    system_name: str
    apps: List[App] = field(default_factory=[])


@dataclass
class Tenant():
    name: str
    url: str
    token: str
    apps: List[App] = field(default_factory=[])


registry = CollectorRegistry()

gauge = Gauge(
    f'threescale_tenant_apps',
    f'3scales apps activas por tenant',
    labelnames=['tenant'],
    registry=registry)

for tenant_dict in tenants_dicts:

    tenant = Tenant(
        name=tenant_dict['name'],
        url=tenant_dict['url'],
        token=tenant_dict['token'],
        apps=[]
    )

    # PRODUCTS
    result = requests.get(
        url=f'{tenant.url}/admin/api/services.json?access_token={tenant.token}&page=1&per_page=10000', verify=False)

    products = []
    for s in result.json()['services']:

        products.append(Product(
            id=s['service']['id'],
            name=s['service']['name'],
            system_name=s['service']['system_name'],
            apps=[]
        ))

    tools.log.info(f'TENANT {tenant.name} -> PRODUCTS {[p.name for p in products]}')

    # ACCOUNTS
    result = requests.get(
        f'{tenant.url}/admin/api/accounts.json?access_token={tenant.token}&page=1&per_page=10000', verify=False)

    accounts = []
    for a in result.json()['accounts']:
        accounts.append(Account(
            id=a['account']['id'],
            name=a['account']['org_name'],
            state=a['account']['state']
        ))

    tools.log.info(f'TENANT {tenant.name} -> ACCOUNTS {[a.name for a in accounts]}')

    # APPLICATIONS
    for a in accounts:

        result = requests.get(
            f'{tenant.url}/admin/api/accounts/{a.id}/applications.json?access_token={tenant.token}&page=1&per_page=10000', verify=False)

        for a in result.json()['applications']:

            id = a['application']['id']

            tenant.apps.append(App(
                id=id,
                name=a['application']['name'],
                state=a['application']['state'],
                description=a['application']['description'],
                service_id=a['application']['service_id']
            ))

    tools.log.info(f'TENANT {tenant.name} -> APPS {[a.name for a in tenant.apps]}')
    tools.log.info('\n')

    tools.log.info(tenant.name)
    tools.log.info('-------------------------------------------------')
    for a in tenant.apps:
        tools.log.info(a.name)
    tools.log.info('\n\n')

# ----------------------------------------------
# SUBIDA A PROMETHEUS
# ----------------------------------------------

    gauge.labels(
        tenant=adapted_name(tenant.name)
    ).set(len(tenant.apps))

push_to_gateway(pushgateway_url,
                job='threescale_tenant_apps', registry=registry)
