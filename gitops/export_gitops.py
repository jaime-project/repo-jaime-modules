from typing import Dict, Set

import tools
import yaml

params = tools.get_params()

cluster = params['cluster_name']
namespaces = params['namespaces']
labels = params['labels']
exclude = params.get('exclude', None)


# ------------------------------------------
# FUNCTIONS
# ------------------------------------------

def create_directory_structure(app_name: str):
    tools.sh(f'mkdir -p gitops/apps/{app_name}/base')
    tools.sh(f'mkdir -p gitops/apps/{app_name}/overlays/dev')


def yaml_to_dict(content: str) -> Dict[str, object]:
    return yaml.load(content, Loader=yaml.FullLoader)


def dict_to_yaml(dic_yaml: Dict[str, object]) -> str:
    return yaml.dump(dic_yaml)


def clean_dict_yaml(dic_yaml: Dict[str, object]) -> Dict[str, object]:

    dic_yaml['metadata'].pop('managedFields', None)
    dic_yaml['metadata'].pop('creationTimestamp', None)
    dic_yaml['metadata'].pop('resourceVersion', None)
    dic_yaml['metadata'].pop('selfLink', None)
    dic_yaml['metadata'].pop('generation', None)
    dic_yaml['metadata'].pop('uid', None)
    dic_yaml.pop('status', None)

    if dic_yaml['kind'] == 'PersistentVolumeClaim':
        dic_yaml['metadata'].pop('finalizers', None)
        dic_yaml['metadata'].pop('annotations', None)
        dic_yaml['spec'].pop('volumeName', None)

    if dic_yaml['kind'] == 'Service':
        dic_yaml['spec'].pop('clusterIP', None)
        dic_yaml['spec'].pop('ipFamilies', None)
        dic_yaml['spec'].pop('clusterIPs', None)

    return dic_yaml


def save_into_base_directory(app_name: str, content: str, file_name: str):
    with open(f'gitops/apps/{app_name}/base/{file_name}.yaml', 'w') as f:
        f.write(content)


def have_all_labels(labels_dict: Dict[str, str], dict_yaml: Dict[str, object]) -> bool:

    for label, value in labels_dict.items():

        if not label in dict_yaml['metadata']['labels']:
            return False

        if value != dict_yaml['metadata']['labels'][label]:
            return False

    return True


def get_clean_dict(object_type: str, object_name: str, namespace: str):

    ob_yaml = tools.sh(
        f'oc get {object_type} {object_name} -n {namespace} -o yaml')

    dic_yaml = yaml_to_dict(ob_yaml)
    dic_yaml = clean_dict_yaml(dic_yaml)

    return dic_yaml


def save_object(app_name: str, dict_yaml: Dict[str, object], object_name):

    create_directory_structure(app_name)
    save_into_base_directory(app_name, dict_to_yaml(dict_yaml), object_name)


def get_related_items(dict_yaml: Dict[str, object]) -> Dict[str, Set[str]]:

    related_items = {
        'configmap': set([]),
        'secret': set([]),
        'pvc': set([])
    }

    if dict_yaml['kind'] == 'CronJob':
        dict_yaml = dict_yaml['spec']['jobTemplate']

    if 'volumes' in dict_yaml['spec']['template']['spec']:

        for volume in dict_yaml['spec']['template']['spec']['volumes']:

            if 'configMap' in volume:
                related_items['configmap'].add(
                    (volume['configMap']['name']))

            if 'persistentVolumeClaim' in volume:
                related_items['pvc'].add(
                    volume['persistentVolumeClaim']['claimName'])

    for container in dict_yaml['spec']['template']['spec']['containers']:

        if 'env' in container:
            for env in container['env']:

                if 'valueFrom' in env and 'secretKeyRef' in env['valueFrom']:
                    related_items['secret'].add(
                        env['valueFrom']['secretKeyRef']['name'])

                if 'valueFrom' in env and 'configMapKeyRef' in env['valueFrom']:
                    related_items['configmap'].add(
                        env['valueFrom']['configMapKeyRef']['name'])

        if 'envFrom' in container:
            for env_from in container['envFrom']:

                if 'secretRef' in env_from:
                    related_items['secret'].add(env_from['secretRef']['name'])

                if 'configMapRef' in env_from:
                    related_items['configmap'].add(
                        env_from['configMapRef']['name'])

    if exclude:
        if exclude['configmap']:
            related_items.pop('configmap')
        if exclude['secret']:
            related_items.pop('secret')

    return related_items


# ------------------------------------------
# SCRIPT
# ------------------------------------------
objects_types = [
    'dc',
    'deployment',
    'statefulset',
    'jobs',
    'cronjobs',
    'route',
    'ingress',
    'svc'
]


if not tools.login_openshift(cluster):
    tools.log.info(f'Error en login {cluster}')
    exit(1)

if not namespaces:
    namespaces = [
        ob
        for ob
        in tools.sh(f'oc get projects -o custom-columns=NAME:.metadata.name --no-headers=true', echo=False).split('\n')
        if not 'openshift-' in ob and not 'kube-' in ob
    ]


for np in namespaces:

    for obj_type in objects_types:

        tools.log.info(f'Processing {obj_type}')

        command = f'oc get {obj_type} -n {np} -o custom-columns=NAME:.metadata.name --no-headers=true -l '

        for label_key, label_value in labels.items():
            command += f"{label_key}={label_value},"

        command = command[:-1]

        objects = tools.sh(command, echo=False).split('\n')

        if '' in objects:
            continue

        for obj in objects:

            tools.log.info(f'Found {obj_type} -> {obj}')

            dict_yaml = get_clean_dict(obj_type, obj, np)
            save_object(obj, dict_yaml, obj)

            related_items = get_related_items(dict_yaml)
            for item_type, item_list in related_items.items():

                for item in item_list:

                    dict_item = get_clean_dict(item_type, item, np)
                    save_object(obj, dict_item, item)

            tools.log.info(f'Saved {obj_type} -> {obj}')

tools.log.info('proceso terminado')
