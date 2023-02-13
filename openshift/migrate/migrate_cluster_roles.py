import tools

params = tools.get_params()

cluster_from = params['clusters']['from']['name']
cluster_to = params['clusters']['to']['name']
repo = params['repo']


# CLUSTERROLES
tools.log.info(f"Generando job para clusterroles")
tools.new_jaime_job(repo, 'migrate_object', 'OPENSHIFT', {
    'clusters': {
        'from': {
            'name': cluster_from,
            'namespace': 'openshift',
            'object': 'clusterroles',
            'ignore': [
                "system:*",
                "openshift-*",
                "registry-*",
                "admin",
                "cluster-admin"
            ]
        },
        'to': {
            'name': cluster_to
        }
    }
}, 'migrate-clusterroles')

# CLUSTERROLEBINDINGS
tools.log.info(f"Generando job para clusterrolebindings")
tools.new_jaime_job(f'migrate-clusterrolebindings', repo, 'migrate_object', {
    'clusters': {
        'from': {
            'name': cluster_from,
            'namespace': 'openshift',
            'object': 'clusterrolebindings',
            'ignore': [
                "system:*",
                "openshift-*",
                "registry-*",
                "admin",
                "cluster-admin"
            ]
        },
        'to': {
            'name': cluster_to
        }
    }
})

tools.log.info(f"Proceso terminado")
