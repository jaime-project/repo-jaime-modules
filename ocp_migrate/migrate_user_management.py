import tools

params = tools.get_params()

cluster_from = params['clusters']['from']['name']
cluster_to = params['clusters']['to']['name']

repo = params['repo']

user_managment = [
    'sa',
    'roles',
    'rolebindings'
]

namespaces = [
    ob
    for ob
    in tools.sh(f'oc get projects -o custom-columns=NAME:.metadata.name --no-headers=true', echo=False).split('\n')
    if not 'openshift-' in ob or not 'kube-' in ob
]

for np in namespaces:

    for ob in user_managment:

        tools.log.info(f"{cluster_to} -> Generando job para {np} {ob}")
        tools.new_jaime_job(repo, 'migrate_object', 'OPENSHIFT', {
            'clusters': {
                'from': {
                    'name': cluster_from,
                    'namespace': np,
                    'object': ob,
                    'ignore': [
                        "system:*",
                        "default",
                        "builder",
                        "deployer"
                    ]
                },
                'to': {
                    'name': cluster_to,
                    'namespace': np
                }
            }
        }, f'migrate-{ob}-{np}')


tools.log.info(f"{cluster_to} -> Generando job para users")
tools.new_jaime_job(repo, 'migrate_object', 'OPENSHIFT', {
    'clusters': {
        'from': {
            'name': cluster_from,
            'namespace': np,
            'object': 'users',
            'ignore': [
                "system:*",
                "default",
                "builder",
                "deployer"
            ]
        },
        'to': {
            'name': cluster_to,
            'namespace': np
        }
    }
}, f'migrate-users-{np}')


tools.log.info(f"{cluster_to} -> Generando job para groups")
tools.new_jaime_job(repo, 'migrate_object', 'OPENSHIFT', {
    'clusters': {
        'from': {
            'name': cluster_from,
            'namespace': np,
            'object': 'groups',
            'ignore': [
                "system:*",
                "default",
                "builder",
                "deployer"
            ]
        },
        'to': {
            'name': cluster_to,
            'namespace': np
        }
    }
}, f'migrate-groups-{np}')

tools.log.info(f"{cluster_to} -> Proceso terminado")
