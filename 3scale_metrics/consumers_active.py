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

tenants_dict = params['tenants']

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
    f'threescale_active_consumers',
    f'3scales consumidores activos en el ultimo mes',
    labelnames=[
        'product',
        'tenant'
    ],
    registry=registry)

for tenant_dict in tenants_dict:

    tenant = Tenant(
        name=tenant_dict['name'],
        url=tenant_dict['url'],
        token=tenant_dict['token'],
        apps=[]
    )

    tools.log.info(f'TENANT -> {tenant.name}')
    tools.log.info('----------------------------')

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

    tools.log.info(f'PRODUCTS {[p.name for p in products]}')

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

    tools.log.info(f'ACCOUNTS {[a.name for a in accounts]}')

    # APPLICATIONS
    active_consumers = []
    metrics_since = datetime.now() - timedelta(days=30)
    metrics_until = datetime.now()

    for a in accounts:

        result = requests.get(
            f'{tenant.url}/admin/api/accounts/{a.id}/applications.json?access_token={tenant.token}&page=1&per_page=10000', verify=False)

        for a in result.json()['applications']:

            id = a['application']['id']

            result = requests.get(
                f'{tenant.url}/stats/applications/{id}/usage.json?access_token={tenant.token}&metric_name=hits&since={metrics_since}&until={metrics_until}&granularity=month&skip_change=true', verify=False)

            hits = result.json()['total']

            app = App(
                id=id,
                name=a['application']['name'],
                state=a['application']['state'],
                description=a['application']['description'],
                service_id=a['application']['service_id'],
                hits=hits
            )

            if app.hits > 0:
                active_consumers.append(app)

    tools.log.info(f'ACTIVE CONSUMERS {[a.name for a in active_consumers]}')

    # ----------------------------------------------
    # SUBIDA A PROMETHEUS
    # ----------------------------------------------

    for a in active_consumers:

        gauge.labels(
            product=adapted_name(a.name),
            tenant=adapted_name(tenant.name)
        ).set(len(active_consumers))

push_to_gateway(
    pushgateway_url, job=f'threescale_active_consumers_by_tenant', registry=registry)
