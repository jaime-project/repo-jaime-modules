import tools

params = tools.get_params()

cluster_from = params['clusters']['from']['name']
cluster_to = params['clusters']['to']['name']

repo = params['repo']

workloads = [
    'deployments',
    'deploymentconfigs',
    'statefulsets',
    'secrets',
    'configmaps',
    'cronjobs',
    'jobs',
    'DaemonSets',
    'HorizontalPodAutoscalers'
]

namespaces = [
    ob
    for ob
    in tools.sh(f'oc get projects -o custom-columns=NAME:.metadata.name --no-headers=true', echo=False).split('\n')
    if not 'openshift-' in ob
]

for np in namespaces:

    for ob in workloads:

        tools.log.info(f"{cluster_to} -> Generando job para {np} {ob}")
        tools.new_jaime_job(repo, 'migrate_object', 'OPENSHIFT', {
            'clusters': {
                'from': {
                    'name': cluster_from,
                    'namespace': np,
                    'object': ob,
                    'ignore': [
                        "default-",
                        "builder-",
                        "deployer-"
                    ]
                },
                'to': {
                    'name': cluster_to,
                    'namespace': np
                }
            }
        }, f'migrate-{ob}-{np}')


tools.log.info(f"{cluster_to} -> Proceso terminado")
