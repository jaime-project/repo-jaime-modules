# Scrips para migrar de OCP a OCP

Usa diferentes scripts para migrar un cluster, lo unico que no migra son los operators, crd y el contenido de los pvs

## Script inicial

- init_migration

## Estructura de scripts

```sh
init_migration
    |- migrate_namespaces
    |- migrate_builds
        |- migrate_object
    |- migrate_images
    |- migrate_networking
        |- migrate_services
        |- migrate_routes
    |- migrate_user_management
        |- migrate_object
    |- migrate_cluster_roles
        |- migrate_object
    |- migrate_pv_pvc
        |- migrate_object
    |- migrate_workloads
        |- migrate_object

```

## Scripts adicionales

- **test**: te permite hacer una prueba simple de coneccion
- **report**: genera un archivo csv con la lista de objetos que se van a migrar