import re

import tools
import yaml

###########################################
# VARS
###########################################

params = tools.get_params()

cluster_from = params['clusters']['from']['name']
namespaces = params['clusters']['from'].get('namespaces', [])
object_from = params['clusters']['from']['object']
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
    objects = tools.sh(
        f'oc get {object_from} -n {namespace} -o custom-columns=NAME:.metadata.name --no-headers=true', echo=False).split('\n')

    tools.sh('mkdir yamls/')

    for ob in objects:

        if only_from:
            match_all_regex = len(
                [regex for regex in only_from if re.match(regex, ob)]) == len(only_from)
            if not match_all_regex:
                continue

        if ignore_from:
            match_any_regex = any(
                True for regex in ignore_from if re.match(regex, ob))
            if match_any_regex:
                continue

        tools.log.info(f'{cluster_from} -> Obteniendo {ob}')
        ob_yaml = tools.sh(
            f'oc get {object_from} {ob} -n {namespace} -o yaml')

        dic_yaml = yaml.load(ob_yaml, Loader=yaml.FullLoader)
        dic_yaml['metadata'].pop('managedFields', None)
        dic_yaml['metadata'].pop('creationTimestamp', None)
        dic_yaml['metadata'].pop('resourceVersion', None)
        dic_yaml['metadata'].pop('selfLink', None)
        dic_yaml['metadata'].pop('uid', None)
        dic_yaml.pop('status', None)

        dict_yaml_modified = yaml.dump(dic_yaml, default_flow_style=False)
        with open(f'yamls/{ob}.yaml', 'w') as file:
            file.write(dict_yaml_modified)

    # login cluster to
    login_success = tools.login_openshift(cluster_to)
    if not login_success:
        tools.log.info(f'Error en login {cluster_to}')
        exit(1)

    tools.sh(f'oc apply -n {namespace} -f yamls/')

    tools.log.info(f'proceso terminado namespace -> {namespace}')

tools.log.info(f'proceso terminado')
