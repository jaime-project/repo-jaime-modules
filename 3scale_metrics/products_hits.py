from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List
from uuid import uuid4

import requests
import tools
import urllib3
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

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

    def total_hits(self):
        return sum([a.hits for a in self.apps])


@dataclass
class Tenant():
    name: str
    url: str
    token: str
    apps: List[App] = field(default_factory=[])


registry = CollectorRegistry()

gauge = Gauge(
    f'threescale_hits',
    f'3scales hits por cada app por producto',
    labelnames=[
        'product',
        'tenant',
        'app'
    ],
    registry=registry)

gauge_total = Gauge(
    f'threescale_hits_total',
    f'3scales hits por producto',
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

    tools.log.info(f'ACCOUNTS {[p.name for p in accounts]}')

    # APPLICATIONS
    apps = []
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

            apps.append(App(
                id=id,
                name=a['application']['name'],
                state=a['application']['state'],
                description=a['application']['description'],
                service_id=a['application']['service_id'],
                hits=hits
            ))

    tools.log.info(f'APPS {[p.name for p in apps]}')

    # APPLICATIONS BY PRODUCT

    for p in products:
        p.apps = [
            app
            for app in apps
            if app.service_id == p.id
        ]

    tools.log.info('APPLICATIONS BY PRODUCT')
    tools.log.info('-------------------------------------------------')
    for p in products:
        tools.log.info(f'PRODUCT -> {p.name}')
        for a in p.apps:
            tools.log.info(f'APP -> {a.name}: {a.hits}')
        tools.log.info(f'PRODUCT -> {p.name} total: {p.total_hits()}')
        tools.log.info('\n')

    tools.log.info('\n')

    # ----------------------------------------------
    # SUBIDA A PROMETHEUS
    # ----------------------------------------------

    for p in products:

        for a in p.apps:

            gauge.labels(
                app=adapted_name(a.name),
                product=adapted_name(p.name),
                tenant=adapted_name(tenant.name)
            ).set(a.hits)

        gauge_total.labels(
            product=adapted_name(p.name),
            tenant=adapted_name(tenant.name)
        ).set(p.total_hits())

push_to_gateway(pushgateway_url,
                job=f'threescale_hits_apps_by_product_by_tenant',
                registry=registry)
