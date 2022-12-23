import tools

VERSION = 'v1.0.0'

params = tools.get_params()

cluster_from = params['clusters']['from']['name']
cluster_to = params['clusters']['to']['name']
repo = params['repo']

url_public_registry = params['url_public_registry']

host_replace_from = params['host_replace_from']
host_replace_to = params['host_replace_to']


tools.log.info(f"Iniciando script de migracion version -> {VERSION}\n")

tools.log.info(f"Generando job para namespaces")
tools.new_jaime_job(repo, 'migrate_namespaces', 'OPENSHIFT', {
    'clusters': {
        'from': {
            'name': cluster_from,
            'object': 'clusterroles',
            'ignore': [
                "openshift-",
                "kube-"
            ]
        },
        'to': {
            'name': cluster_to
        }
    }
}, 'migrate_namespaces')


tools.log.info(f"Generando job para builds")
tools.new_jaime_job(repo, 'migrate_builds', 'OPENSHIFT', {
    'clusters': {
        'from': {
            'name': cluster_from,
        },
        'to': {
            'name': cluster_to
        },
        'repo': repo
    }
}, 'migrate_builds')


tools.log.info(f"Generando job para images")
tools.new_jaime_job(repo, 'migrate_images', 'OPENSHIFT', {
    'clusters': {
        'from': {
            'name': cluster_from,
            'url_public_registry': url_public_registry,
        },
        'to': {
            'name': cluster_to
        }
    }
}, 'migrate_images')


tools.log.info(f"Generando job para networking")
tools.new_jaime_job(repo, 'migrate_networking', 'OPENSHIFT', {
    'clusters': {
        'from': {
            'name': cluster_from,
            'host_replace_from': host_replace_from,
        },
        'to': {
            'name': cluster_to,
            'host_replace_to': host_replace_to,
        },
        'repo': repo
    }
}, 'migrate_networking')


tools.log.info(f"Generando job para user management")
tools.new_jaime_job(repo, 'migrate_user_management', 'OPENSHIFT', {
    'clusters': {
        'from': {
            'name': cluster_from,
        },
        'to': {
            'name': cluster_to,
        },
        'repo': repo
    }
}, 'migrate_user_management')


tools.log.info(f"Generando job para cluster roles")
tools.new_jaime_job(repo, 'migrate_cluster_roles', 'OPENSHIFT', {
    'clusters': {
        'from': {
            'name': cluster_from,
        },
        'to': {
            'name': cluster_to,
        },
        'repo': repo
    }
}, 'migrate_cluster_roles')


tools.log.info(f"Generando job para cluster roles")
tools.new_jaime_job(repo, 'migrate_pv_pvc', 'OPENSHIFT', {
    'clusters': {
        'from': {
            'name': cluster_from,
        },
        'to': {
            'name': cluster_to,
        }
    }
}, 'migrate_pv_pvc')


tools.log.info(f"Generando job para workloads")
tools.new_jaime_job(repo, 'migrate_workloads', 'OPENSHIFT', {
    'clusters': {
        'from': {
            'name': cluster_from,
        },
        'to': {
            'name': cluster_to,
        },
        'repo': repo
    }
}, 'migrate_workloads')
