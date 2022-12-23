import tools

params = tools.get_params()

cluster = params['cluster_name']
namespaces_list = params.get('namespaces', [])
phases = params.get('phases', [])


if not tools.login_openshift(cluster):
    tools.log.info(f'Error en login {cluster}')
    exit(1)

tools.sh('mkdir yamls')


if not namespaces_list:
    namespaces_list = [
        np
        for np in tools.sh(f'oc get project -o custom-columns=NAME:.metadata.name').split('\n')[1:]
        if not 'openshift-' in np
    ]


for np in namespaces_list:

    for phase in phases:

        tools.sh(
            f'oc delete pod --force --field-selector=status.phase=={phase} -n {np}')

tools.log.info('proceso terminado')
