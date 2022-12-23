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

cluster_to = params['clusters']['to']['name']


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
    services = tools.sh(
        f'oc get services -n {namespace} -o custom-columns=NAME:.metadata.name --no-headers=true', echo=False).split('\n')

    tools.sh('mkdir yamls/')

    for service in services:

        if only_from:
            match_all_regex = len(
                [regex for regex in only_from if re.match(regex, service)]) == len(only_from)
            if not match_all_regex:
                continue

        if ignore_from:
            match_any_regex = any(
                True for regex in ignore_from if re.match(regex, service))
            if match_any_regex:
                continue

        tools.log.info(f'{cluster_from} -> Obteniendo {service}')
        service_yaml = tools.sh(
            f'oc get service {service} -n {namespace} -o yaml')

        service_dict = yaml.load(service_yaml, Loader=yaml.FullLoader)
        service_dict['metadata'].pop('managedFields', None)
        service_dict['metadata'].pop('creationTimestamp', None)
        service_dict['metadata'].pop('namespace', None)
        service_dict['metadata'].pop('resourceVersion', None)
        service_dict['metadata'].pop('selfLink', None)
        service_dict['metadata'].pop('uid', None)
        service_dict.pop('status', None)

        if 'spec' in service_dict:
            service_dict['spec'].pop('clusterIP', None)
            service_dict['spec'].pop('clusterIPs', None)

        dict_yaml_modified = yaml.dump(service_dict, default_flow_style=False)
        with open(f'yamls/{service}.yaml', 'w') as file:
            file.write(dict_yaml_modified)

    # login cluster to
    login_success = tools.login_openshift(cluster_to)
    if not login_success:
        tools.log.info(f'Error en login {cluster_to}')
        exit(1)

    tools.sh(f'oc apply -n {namespace} -f yamls/')

    tools.log.info(f'proceso terminado namespace -> {namespace}')


tools.log.info(f'proceso terminado')
