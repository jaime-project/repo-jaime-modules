import tools
import re

params = tools.get_params()

cluster_from = params['clusters']['from']['name']
namespace_from = params['clusters']['from']['namespace']
object_from = params['clusters']['from']['object']
only_from = params['clusters']['from'].get('only', [])
ignore_from = params['clusters']['from'].get('ignore', [])

login_success = tools.login_openshift(cluster_from)
if not login_success:
    tools.log.info(f'Error en login {cluster_from}')
    exit(0)

tools.log.info(f"{cluster_from} -> Obtieniendo todos los objetos")
objects = [
    ob
    for ob
    in tools.sh(f'oc get {object_from} -n {namespace_from} -o custom-columns=NAME:.metadata.name', echo=False).split('\n')[1:]
]


objects_to_migrate = []
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

    objects_to_migrate.append(ob)

tools.log.info(f"{cluster_from} -> Objetos entontrados: {len(objects_to_migrate)}")

for ob in objects_to_migrate:
    tools.log.info(ob)

tools.log.info(f"{cluster_from} -> Proceso terminado")
