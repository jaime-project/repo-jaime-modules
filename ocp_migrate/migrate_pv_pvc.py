import tools
import yaml

params = tools.get_params()

cluster_from = params['clusters']['from']['name']
namespaces = params['clusters']['from'].get('namespaces', [])

cluster_to = params['clusters']['to']['name']
pvc_storage_class = params['clusters']['to'].get('storage_class', None)


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
        if not 'openshift-' in ob or not 'kube-' in ob
    ]

for namespace in namespaces:

    # obteniendo PVC yamls
    tools.log.info(f"{cluster_from} -> Obtieniendo todos los pvc")
    pvcs = tools.sh(
        f'oc get pvc -n {namespace} -o custom-columns=NAME:.metadata.name --no-headers=true', echo=False).split('\n')

    tools.sh('mkdir -p yamls/pvcs')
    tools.sh('mkdir -p yamls/pvs')

    for pvc in pvcs:

        ###########################################
        # PVCs
        ###########################################
        tools.log.info(f'{cluster_from} -> Obteniendo pvc {pvc}')
        pvc_yaml = tools.sh(f'oc get pvc {pvc} -n {namespace} -o yaml')

        pvc_dict = yaml.load(pvc_yaml, Loader=yaml.FullLoader)
        pvc_dict['metadata'].pop('managedFields', None)
        pvc_dict['metadata'].pop('creationTimestamp', None)
        pvc_dict['metadata'].pop('resourceVersion', None)
        pvc_dict['metadata'].pop('selfLink', None)
        pvc_dict['metadata'].pop('uid', None)
        pvc_dict.pop('status', None)

        pvc_dict['metadata'].pop('finalizers', None)
        pvc_dict['metadata'].pop('annotations', None)

        if pvc_storage_class:
            pvc_dict['spec']['storageClassName'] = pvc_storage_class

        pvc_yaml_modified = yaml.dump(pvc_dict, default_flow_style=False)
        with open(f'yamls/pvcs/{pvc}.yaml', 'w') as file:
            file.write(pvc_yaml_modified)

        ###########################################
        # PVs
        ###########################################
        pv = pvc_dict['spec']['volumeName']

        tools.log.info(f'{cluster_from} -> Obteniendo pv {pv}')
        pv_yaml = tools.sh(f'oc get pv {pv} -n {namespace} -o yaml')

        pv_dict = yaml.load(pv_yaml, Loader=yaml.FullLoader)
        pv_dict['metadata'].pop('managedFields', None)
        pv_dict['metadata'].pop('creationTimestamp', None)
        pv_dict['metadata'].pop('namespace', None)
        pv_dict['metadata'].pop('resourceVersion', None)
        pv_dict['metadata'].pop('selfLink', None)
        pv_dict['metadata'].pop('uid', None)
        pv_dict.pop('status', None)

        pv_dict['metadata'].pop('finalizers', None)
        pv_dict['spec']['claimRef'].pop('uid', None)
        pv_dict['spec']['claimRef'].pop('resourceVersion', None)

        pv_yaml_modified = yaml.dump(pv_dict, default_flow_style=False)
        with open(f'yamls/pvs/{pv}.yaml', 'w') as file:
            file.write(pv_yaml_modified)

    # login cluster to
    login_success = tools.login_openshift(cluster_to)
    if not login_success:
        tools.log.info(f'Error en login {cluster_to}')
        exit(1)

    tools.log.info('Aplicando los pvs')
    tools.sh(f'oc apply  -n {namespace} -f yamls/pvs/')

    tools.log.info('Aplicando los pvcs')
    tools.sh(f'oc apply  -n {namespace} -f yamls/pvcs/')

    tools.log.info(f'Proceso terminado namespace -> {namespace}')

tools.log.info(f'Proceso terminado')
