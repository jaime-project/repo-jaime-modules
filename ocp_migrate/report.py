from typing import Dict, List
import tools

params = tools.get_params()

cluster_from = params['cluster_name']

csv_file_path = 'report.csv'

row_items = [
    # WORKLOADS
    'deployments',
    'deploymentconfigs',
    'statefulsets',
    'secrets',
    'configmaps',
    'cronjobs',
    'jobs',
    'daemonSets',
    'horizontalPodAutoscalers',
    # NETWORKING
    'services',
    'routes',
    # STORAGE
    'pv',
    'pvc',
    # BUILDS
    'buildconfigs',
    'is',
    # USERS
    'users',
    'groups',
    'sa',
    'roles',
    'rolebinding',
]


def get_count(object: str, project: str) -> int:
    return len(tools.sh(f'oc get {object} -n {project} -o custom-columns=NAME:.metadata.name', echo=False).split('\n')[1:])


login_success = tools.login_openshift(cluster_from)
if not login_success:
    tools.log.info(f'Error en login {cluster_from}')
    exit(1)


projects = [
    project
    for project in tools.sh(f'oc get projects -o custom-columns=NAME:.metadata.name', echo=False).split('\n')[1:]
    if 'openshift-' not in project
]


list_rows = []

tools.log.info('Generando encabezados')
row = 'projects;'
for object in row_items:
    row += f'{object};'

list_rows.append(row)


tools.log.info('Obteniendo datos')
for project in projects:

    row = f'{project};'
    for object in row_items:
        tools.log.info(f'Obteniendo datos de {object} para el proyecto {project}')
        row += f'{get_count(object, project)};'

    list_rows.append(row)


tools.log.info(f'Generando archivo CSV en {csv_file_path}')
for row in list_rows:
    tools.sh(f'echo "{row}" >> {csv_file_path}')

tools.log.info(f"{cluster_from} -> Proceso terminado")
