import json
from dataclasses import dataclass
from typing import Dict, List

import tools
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

params = tools.get_params()

namespace = params['namespace']
cluster_name = params['cluster']
groups = params['groups']
pushgateway_url = params['pushgateway-url']

# ----------------------------------------------
# OBTENCION DE PRODUCTOS
# ----------------------------------------------


def adapted_name(name: str) -> str:
    return str(name).lower().replace(' ', '_').replace("""'""", '').replace('-', '_').replace('ñ', 'ni')


@dataclass
class Group():
    name: str
    labels: Dict[str, str]
    products: List[str]

    def __str__(self) -> str:
        return json.dumps(self.__dict__)


tools.login_openshift(cluster_name)
tools.log.info('\n')

products_names = tools.sh(
    f'oc get product -n {namespace} -o custom-columns=NAME:.metadata.name --no-headers=true', echo=False).split('\n')

groups_dict = {}
for group in groups:

    command = f'oc get product -n {namespace} -o custom-columns=NAME:.metadata.name --no-headers=true -l '

    for label_key, label_value in group['labels'].items():
        command += f"{label_key}={label_value},"

    command = command[:-1]

    groups_dict[group['name']] = Group(
        name=group['name'],
        labels=group['labels'],
        products=tools.sh(command, echo=False).split('\n')
    )


tools.log.info('LISTADO')
tools.log.info(products_names)
tools.log.info('\n')

tools.log.info('GRUPOS')
for group_key, group_value in groups_dict.items():
    tools.log.info(f'{group_key} -> {group_value.products}')
tools.log.info('\n')


# ----------------------------------------------
# SUBIDA A PROMETHEUS
# ----------------------------------------------


registry = CollectorRegistry()

gauge = Gauge(
    f'threescale_migrated_products',
    f'3scales apis migradas',
    labelnames=[
        'group',
        'labels'
    ],
    registry=registry)

for group_name, group_object in groups_dict.items():

    gauge.labels(
        group=adapted_name(group_name),
        labels='_'.join(group_object.labels.keys())
    ).set(len(group_object.products))


push_to_gateway(pushgateway_url,
                job='threescale_migrated_products', registry=registry)
