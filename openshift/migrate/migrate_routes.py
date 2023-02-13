import os
import re

import yaml
import tools

###########################################
# VARS
###########################################

params = tools.get_params()

cluster_from = params['clusters']['from']['name']
namespaces = params['clusters']['from'].get('namespaces', [])
only_from = params['clusters']['from'].get('only', [])
ignore_from = params['clusters']['from'].get('ignore', [])
host_replace_from = params['clusters']['from']['host_replace_from']

cluster_to = params['clusters']['to']['name']
host_replace_to = params['clusters']['to']['host_replace_to']


###########################################
# SCRIPT
###########################################

# login cluster from
login_success = tools.login_openshift(cluster_from)
if not login_success:
    tools.log.info(f'Error en login {cluster_from}')
    exit(1)


if not namespaces:
    namespaces = [
        ob
        for ob
        in tools.sh(f'oc get projects -o custom-columns=NAME:.metadata.name --no-headers=true', echo=False).split('\n')
        if not 'openshift' in ob and not 'kube-' in ob
    ]

for namespace in namespaces:

    # obteniendo yamls
    tools.log.info(f"{cluster_from} -> Obtieniendo todos los objetos")
    routes = tools.sh(
        f'oc get routes -n {namespace} -o custom-columns=NAME:.metadata.name --no-headers=true', echo=False).split('\n')

    tools.sh('mkdir yamls/')

    for route in routes:

        if only_from:
            match_all_regex = len(
                [regex for regex in only_from if re.match(regex, route)]) == len(only_from)
            if not match_all_regex:
                continue

        if ignore_from:
            match_any_regex = any(
                True for regex in ignore_from if re.match(regex, route))
            if match_any_regex:
                continue

        tools.log.info(f'{cluster_from} -> Obteniendo {route}')
        route_yaml = tools.sh(
            f'oc get routes {route} -n {namespace} -o yaml')

        route_dict = yaml.load(route_yaml, Loader=yaml.FullLoader)
        route_dict['metadata'].pop('managedFields', None)
        route_dict['metadata'].pop('creationTimestamp', None)
        route_dict['metadata'].pop('resourceVersion', None)
        route_dict['metadata'].pop('selfLink', None)
        route_dict['metadata'].pop('uid', None)
        route_dict.pop('status', None)

        if 'spec' in route_dict:
            route_dict['spec']['host'] = route_dict['spec']['host'].replace(
                host_replace_from, host_replace_to)

        dict_yaml_modified = yaml.dump(route_dict, default_flow_style=False)
        with open(f'yamls/{route}.yaml', 'w') as file:
            file.write(dict_yaml_modified)

    # login cluster to
    login_success = tools.login_openshift(cluster_to)
    if not login_success:
        tools.log.info(f'Error en login {cluster_to}')
        exit(1)

    tools.sh(f'oc apply -n {namespace} -f yamls/')

    tools.log.info(f'proceso terminado namespace -> {namespace}')


tools.log.info(f'proceso terminado')
