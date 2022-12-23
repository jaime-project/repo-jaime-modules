import re

import tools
import yaml

params = tools.get_params()

cluster_from = params['clusters']['from']['name']
namespaces = params['clusters']['from'].get('namespaces', [])
url_public_registry = params['clusters']['from']['url_public_registry']

cluster_to = params['clusters']['to']['name']


login_success = tools.login_openshift(cluster_from)
if not login_success:
    tools.log.info(f'Error en login {cluster_from}')
    exit(1)


if not namespaces:
    namespaces = [
        ob
        for ob
        in tools.sh(f'oc get projects -o custom-columns=NAME:.metadata.name --no-headers=true', echo=False).split('\n')
        if not 'openshift-' in ob or not 'kube-' in ob
    ]

for namespace in namespaces:

    # buscando cosas en el cluster from
    tools.log.info(f"{cluster_from} -> Obtieniendo secrets")
    secrets = tools.sh(
        f'oc get secret -n {namespace} -o custom-columns=NAME:.metadata.name --no-headers=true', echo=False).split('\n')

    tools.log.info(f"{cluster_from} -> Obtieniendo imagestream")
    images = tools.sh(
        f'oc get is -n {namespace} -o custom-columns=NAME:.metadata.name --no-headers=true', echo=False).split('\n')

    # buscando secret
    for s in secrets:

        p = re.compile('default-dockercfg-*')
        m = p.match(s)
        if m:
            secret = s
            tools.log.info('Encontrado secret -> ', s)

    if not secret:
        tools.log.info(f'Error en encontrar un secret con la forma -> default-dockercfg-*')
        exit(1)

    secret_content = tools.sh(f'oc get secret {secret} -n {namespace} -o yaml')

    # logueando cluster to
    login_success = tools.login_openshift(cluster_to)
    if not login_success:
        tools.log.info(f'Error en login {cluster_to}')
        exit(1)

    tools.sh('mkdir -p yamls/secrets')

    # generando secret en cluster to
    tools.sh(f'oc new-project {namespace}')

    with open(f'yamls/secrets/{secret}.yaml', 'w') as file:
        dic_yaml = yaml.load(secret_content, Loader=yaml.FullLoader)

        dic_yaml['metadata'].pop('managedFields', None)
        dic_yaml['metadata'].pop('creationTimestamp', None)
        dic_yaml['metadata'].pop('namespace', None)
        dic_yaml['metadata'].pop('resourceVersion', None)
        dic_yaml['metadata'].pop('selfLink', None)
        dic_yaml['metadata'].pop('uid', None)
        dic_yaml.pop('status', None)

        dic_yaml['metadata'].pop('ownerReferences', None)

        file.write(yaml.dump(dic_yaml, default_flow_style=False))

    tools.sh(f'oc apply -n {namespace} -f yamls/secrets/{secret}.yaml')
    tools.log.info(f'Creado secret -> {secret}')

    # migrando imagenes
    for image in images:

        tools.sh(
            f"oc import-image {image} --from={url_public_registry}/{namespace}/{image} --all --confirm --insecure=true -n {namespace}")

    tools.sh(
        f"oc delete secret {secret} -n {namespace}")

    tools.log.info(f'proceso terminado namespace -> {namespace}')

tools.log.info(f'proceso terminado')
