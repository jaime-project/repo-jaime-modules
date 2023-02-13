import tools

params = tools.get_params()

cluster_from = params['clusters']['from']['name']
host_replace_from = params['clusters']['from']['host_replace_from']

cluster_to = params['clusters']['to']['name']
host_replace_to = params['clusters']['to']['host_replace_to']

repo = params['repo']

# ROUTES
tools.log.info(f"{cluster_to} -> Generando job para routes")
tools.new_jaime_job(repo, 'migrate_routes', 'OPENSHIFT', {
    'clusters': {
        'from': {
            'name': cluster_from,
            'host_replace_from': host_replace_from
        },
        'to': {
            'name': cluster_to,
            'host_replace_to': host_replace_to
        }
    }
}, f'migrate-routes')

# SERVICES
tools.log.info(f"{cluster_to} -> Generando job para services")
tools.new_jaime_job(repo, 'migrate_services', 'OPENSHIFT', {
    'clusters': {
        'from': {
            'name': cluster_from,
            'ignore': [
                'openshift',
                'kubernetes'
            ]
        },
        'to': {
            'name': cluster_to
        }
    }
}, f'migrate-services')

tools.log.info(f"{cluster_to} -> Proceso terminado")
