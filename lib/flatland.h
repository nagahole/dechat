#ifndef FLATLAND_H
#define FLATLAND_H 1

#include "scanner.h"
#include "asteroid_cluster.h"

/*
 * flatland_protect
 * Core function, attempts to use the scanner to clear the cluster
 * :: void* cluster :: Cluster of asteroids heading for flatland
 * :: void* scanner :: Asteroid detecting scanner.
 * Acts in place to clear the asteroids.
 */
void flatland_protect(void* cluster, void* scanner);

#endif
