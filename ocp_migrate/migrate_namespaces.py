import re

import tools
import yaml

###########################################
# VARS
###########################################

params = tools.get_params()

cluster_from = params['clusters']['from']['name']
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


# obteniendo yamls
tools.log.info(f"{cluster_from} -> Obtieniendo todos los objetos")
namespaces = tools.sh(
    f'oc get namespaces -o custom-columns=NAME:.metadata.name --no-headers=true', echo=False).split('\n')

tools.sh('mkdir yamls/')

for np in namespaces:

    if only_from:
        match_all_regex = len(
            [regex for regex in only_from if re.match(regex, np)]) == len(only_from)
        if not match_all_regex:
            continue

    if ignore_from:
        match_any_regex = any(
            True for regex in ignore_from if re.match(regex, np))
        if match_any_regex:
            continue

    tools.log.info(f'{cluster_from} -> Obteniendo {np}')
    np_yaml = tools.sh(
        f'oc get namespace {np} -o yaml')

    np_dict = yaml.load(np_yaml, Loader=yaml.FullLoader)
    np_dict['metadata'].pop('managedFields', None)
    np_dict['metadata'].pop('creationTimestamp', None)
    np_dict['metadata'].pop('resourceVersion', None)
    np_dict['metadata'].pop('uid', None)
    np_dict.pop('status', None)

    np_dict_modified = yaml.dump(np_dict, default_flow_style=False)
    with open(f'yamls/{np}.yaml', 'w') as file:
        file.write(np_dict_modified)


# login cluster to
login_success = tools.login_openshift(cluster_to)
if not login_success:
    tools.log.info(f'Error en login {cluster_to}')
    exit(1)

tools.sh(f'oc apply -f yamls/')

tools.log.info(f'proceso terminado')
