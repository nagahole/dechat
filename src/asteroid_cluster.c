#include "asteroid_cluster.h"

/*
 * asteroid_cluster_create
 * Creates an asteroid cluster at the location of the first argument
 * :: void* data            :: The location of the cluster
 * :: const int n_asteroids :: The maximum number of asteroids in this cluster
 * :: const float tolerance :: The tolerance of all asteroids in this cluster
 */
void asteroid_cluster_create(
        void* data,
        const int n_asteroids,
        const float tolerance)
{
    // TODO
}

/*
 * asteroid_cluster_add_asteroid
 * Adds an asteroid to the cluster
 * :: void* cluster :: The cluster to add the asteroid to
 * :: void* poly_x  :: X polynomial for the asteroid
 * :: void* poly_y  :: Y polynomial for the asteroid
 * Acts in place, updating the cluster
 */
void asteroid_cluster_add_asteroid(void* cluster, void* poly_x, void* poly_y)
{
    // TODO
}

/*
 * int asteroid_cluster_clear
 * Checks if the cluster of asteroids has been cleared
 * :: void* asteroids :: Pointer to the asteroid cluster
 * Returns 1 if all asteroids are clear
 * Returns 0 otherwise
 */
int asteroid_cluster_clear(void* asteroids)
{
    // TODO
    return 0;
}

/*
 * asteroid_cluster_scan
 * Performs a scan on the asteroid cluster from a point 
 * :: void* cluster :: The cluster
 * :: const float x :: X position of the scanner
 * :: const float y :: Y position of the scanner
 * Returns the minimum distance between any asteroid in the cluster and the scanner.
 * Returns INF if the distance is greater than 1000
 * Returns NaN if an asteroid has impacted
 */
float asteroid_cluster_scan(void* cluster, const float x, const float y)
{
    // TODO
    return 0;
}


/*
 * void asteroid_cluster_intercept
 * Checks if a given x, y coordinate intercepts with any of the asteroids in the cluster
 * :: void* cluster :: Pointer to cluster of asteroids
 * :: const float x :: x coordinate to attempt to intercept 
 * :: const float y :: y coordinate to attempt to intercept
 * Returns nothing
 */
void asteroid_cluster_intercept(
        void* asteroids,
        const float x,
        const float y)
{
    // TODO
    return;
}

/*
 * asteroid_cluster_impact
 * Checks if any asteroid has impacted at y <= 0
 * :: void* cluster :: Pointer to the cluster
 * Returns 1 if an impact has occurred, 0 otherwise
 */
int asteroid_cluster_impact(void* cluster)
{
    // TODO
    return 0;
}

/*
 * void asteroid_cluster_update
 * Updates the position of all asteroids in the cluster
 * :: void* cluster :: Pointer to asteroid cluster object
 * Returns nothing, all updates occur in place
 */
void asteroid_cluster_update(void* cluster)
{
    // TODO
    return;
}

/*
 * get_tolerance
 * Gets the tolerance of an asteroid cluster
 * :: void* cluster :: Pointer to cluster
 * Returns the tolernace of all asteroids in that cluster
 */
float get_tolerance(void* cluster) 
{
    // TODO
    return 0;
}
