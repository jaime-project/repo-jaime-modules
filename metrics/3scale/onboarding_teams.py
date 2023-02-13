import tools
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

params = tools.get_params()

namespace = params['namespace']
cluster_name = params['cluster']
pushgateway_url = params['pushgateway-url']

labels = params['labels']
teams = params['teams']
label_team_name = params['label-team-name']

# ----------------------------------------------
# OBTENCION DE PRODUCTOS
# ----------------------------------------------


def adapted_name(name: str) -> str:
    return str(name).lower().replace(' ', '_').replace("""'""", '').replace('-', '_').replace('ñ', 'ni')


tools.login_openshift(cluster_name)

products_by_team = {}
for team in teams:

    command = f'oc get product -n {namespace} -o custom-columns=NAME:.metadata.name --no-headers=true -l '

    for label_key, label_value in labels.items():
        command += f"{label_key}={label_value},"

    command += f'{label_team_name}={team}'

    products_by_team[team] = tools.sh(f'{command} | wc -l')


tools.log.info('Listado')
for team, products_count in products_by_team.items():
    tools.log.info(f'{team} -> {products_count}')


# ----------------------------------------------
# SUBIDA A PROMETHEUS
# ----------------------------------------------


registry = CollectorRegistry()

gauge = Gauge(
    f'threescale_onboarding_apis',
    f'3scales apis migradas de equipos que realizaron el onboarding',
    labelnames=['team'],
    registry=registry)

for team, products_count in products_by_team.items():

    gauge.labels(
        team=adapted_name(team)
    ).set(products_count)

push_to_gateway(pushgateway_url,
                job='threescale_onboarding_apis', registry=registry)
